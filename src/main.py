# --- IMPORTS ---
import config
import os
import time
import sys
import requests
import json
from datetime import datetime
import math
import pytz
import threading
import queue

from PIL import ImageFont, ImageDraw, Image
from luma.core.render import canvas


# --- CONDITIONAL DISPLAY DRIVER / EMULATOR SETUP ---
IS_RASPBERRY_PI = False
if sys.platform.startswith("linux") and os.uname().machine.startswith("arm"):
    try:
        from luma.core.interface.serial import spi
        from luma.oled.device import ssd1322
        import RPi.GPIO as GPIO

        IS_RASPBERRY_PI = True
    except ImportError:
        print(
            "Warning: Running on Raspberry Pi but luma.oled drivers not found. Falling back to emulator."
        )
if not IS_RASPBERRY_PI:
    from luma.emulator.device import pygame


# --- GLOBAL FONT DEFINITIONS ---
font: ImageFont.FreeTypeFont = None
fontBold: ImageFont.FreeTypeFont = None

# --- GLOBAL API SESSION & QUEUES FOR THREAD COMMUNICATION ---
API_SESSION = requests.Session()
raw_api_data_queue1 = queue.Queue(maxsize=1)
raw_api_data_queue2 = queue.Queue(maxsize=1)
# rendered_frames_queue = queue.Queue(maxsize=1)
rendered_frames_queue1 = queue.Queue(maxsize=1)
rendered_frames_queue2 = queue.Queue(maxsize=1)

# --- GLOBAL BUFFER FOR FINAL DISPLAY OUTPUT ---
display_output_buffer: Image.Image = None

# --- GLOBAL DISPLAY DEVICE ---
display_device = None  # Initialize display_device to None

# --- GLOBAL DEFINITION OF ARRIVALS AREA AND CLOCK AREA OF DISPLAY ---
arrivals_display_rect, clock_display_rect = None, None  # Initialize display rectangles

# --- HELPER FUNCTIONS ---


def make_Font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", name))
    try:
        return ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.BASIC)
    except IOError:
        print(
            f"Error: Could not load font from {font_path}. Using default system font."
        )
        return ImageFont.load_default()


def initialize_fonts():
    global font, fontBold
    font = make_Font("Dot Matrix Regular.ttf", config.fontSize)
    fontBold = make_Font("Dot Matrix Bold.ttf", config.fontSize)


def get_time_to_arrival(arrival, font):
    """Calculates the time to arrival and formats it for display."""

    seconds_to_arrival = int(arrival["arrival_time"].timestamp() - time.time())
    time_to_arrival = " "  # Default value if not displayed
    time_width = 0  # Default value if not displayed

    if seconds_to_arrival >= config.earliest_arrival * 60:
        display_check = True
        minutes_to_arrival = seconds_to_arrival / 60
        # print(minutes_to_arrival)

        # Format the time string
        if minutes_to_arrival > 1:
            time_to_arrival = (
                f"{math.floor(minutes_to_arrival + 0.5)} min"
                # + "   "
                # + str(arrival["arrival_time"])
            )
        else:
            time_to_arrival = "due"  # + "   " + str(arrival["arrival_time"])

        bbox = font.getbbox(time_to_arrival)
        time_width = bbox[2] - bbox[0]

    else:
        display_check = False
    return time_to_arrival, time_width, display_check


# --- API INTERACTION FUNCTIONS ---


def query_TFL(
    url: str,
    params: dict = None,
    max_retries: int = 3,
    _session: requests.Session = None,
) -> list:
    session_to_use = _session if _session else requests.Session()
    for retry_attempt in range(max_retries):
        try:
            response = session_to_use.get(url, params=params, timeout=10)
            response.raise_for_status()
            json_response = response.json()
            return json_response if json_response else []
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(
                f"Error calling TfL API (Attempt {retry_attempt + 1}/{max_retries}): {e}"
            )
            if retry_attempt == max_retries - 1:
                raise RuntimeError(
                    f"Failed to fetch data from {url} after {max_retries} retries: {e}"
                )
        time.sleep(1)
    return []


def get_station_id(
    _session: requests.Session = None,
    lines_filter1: set = None,
    lines_filter2: set = None,
) -> dict:

    TFL_STOPPOINT_SEARCH_URL = "https://api.tfl.gov.uk/StopPoint/Search"
    TFL_STOPPOINT_DETAIL_URL_BASE = (
        "https://api.tfl.gov.uk/StopPoint/"  # Base URL for detail/children
    )

    # 1. Search for the station ---
    params_search = {
        "query": config.station,
        # "modes": "tube",
        "maxResults": 1,
        "app_key": config.api_key,
    }
    search_response = query_TFL(
        TFL_STOPPOINT_SEARCH_URL, params_search, _session=_session
    )

    if (
        not search_response
        or not search_response.get("matches")
        or len(search_response["matches"]) == 0
    ):
        raise RuntimeError(
            f"The following station could not be found: {config.station}."
        )

    search_result_id = search_response["matches"][0]["id"]

    # 2. Get details (including children) for the found StopPoint
    params_detail = {
        "app_key": config.api_key,
    }
    # Construct the full URL using the search_result_id
    detail_response = query_TFL(
        TFL_STOPPOINT_DETAIL_URL_BASE + search_result_id,
        params_detail,
        _session=_session,
    )

    if not detail_response:
        raise RuntimeError(
            f"Could not retrieve details for station ID: {search_result_id}"
        )

    final_station_data = None

    # 3. Determine if the main StopPoint or one of its children matches ---
    # Check the primary StopPoint itself
    # print(detail_response)
    if detail_response.get("stopType") == "NaptanMetroStation" and check_lines(
        detail_response.get("lines", []), lines_filter1, lines_filter2
    ):
        final_station_data = detail_response
    elif detail_response.get(
        "children"
    ):  # If it has children (likely a TransportInterchange)
        for child in detail_response["children"]:
            if child.get("stopType") == "NaptanMetroStation" and check_lines(
                child.get("lines", []), lines_filter1, lines_filter2
            ):
                final_station_data = child  # Assign the child that matched!
                break  # Found a matching child, no need to check others

    # 4. Return or raise error based on finding a match ---
    if final_station_data:
        return {
            "name": final_station_data.get("commonName"),
            "id": final_station_data.get("id"),
        }
    else:
        raise RuntimeError(
            f"'The following station is not served by the specified tube lines or is not a valid MetroStation: {config.station}."
        )


def check_lines(lines, lines_filter1, lines_filter2):
    served_lines = set()
    for line_info in lines:
        served_lines.add(line_info["id"])

    # Extract the line names specified by the user from the filter sets
    extracted_lines_filter1 = {line_name for line_name, _ in lines_filter1}
    extracted_lines_filter2 = {line_name for line_name, _ in lines_filter2}

    # Combine all unique line names from both filter sets
    all_filtered_lines_to_check = extracted_lines_filter1.union(extracted_lines_filter2)

    # Check if all lines in 'all_filtered_lines_to_check' are present in 'served_lines'
    return all_filtered_lines_to_check.issubset(served_lines)


def get_lines_filter(lines_config_list: list, _session: requests.Session = None) -> set:
    TFL_LINE_SEARCH_URL = "https://api.tfl.gov.uk/Line/Search/"
    filter_set = set()
    params = {
        "app_key": config.api_key,
    }
    for entry in lines_config_list:

        search_response = query_TFL(
            TFL_LINE_SEARCH_URL + entry.get("line"),
            params,
            _session=_session,
        )

        if not search_response.get("searchMatches"):
            raise RuntimeError(
                f"The following tube line could not be found: {entry.get('line')}."
            )

        line = search_response["searchMatches"][0]["lineId"]
        direction_substring = entry.get("direction")
        if line and direction_substring:
            filter_set.add((line.lower(), direction_substring.lower()))
    return filter_set


def get_arrivals(
    station: dict,
    filter_criteria_set: set,
    n: int = 7,
    _session: requests.Session = None,
) -> list:
    try:
        TFL_STOPPOINT_ARRIVALS_URL = (
            "https://api.tfl.gov.uk/StopPoint/" + station["id"] + "/Arrivals"
        )
        # TFL_STOPPOINT_ARRIVALS_URL = (
        #     "https://api.tfl.gov.uk/Line/district/Arrivals/" + station["id"]
        # )

        params = {
            "app_key": config.api_key,
        }
        # print(params)
        all_arrivals = query_TFL(TFL_STOPPOINT_ARRIVALS_URL, params, _session=_session)
        # print(json.dumps(all_arrivals, indent=2))
        if not isinstance(all_arrivals, list):
            return []
        filtered_predictions = [
            p
            for p in all_arrivals
            if (
                (p_line := p.get("lineId", "").lower())
                and (p_platform := p.get("platformName", "").lower())
                and p.get("timeToStation", float("inf")) >= config.earliest_arrival * 60
                and any(
                    f_line == p_line and f_direction_substring in p_platform
                    for f_line, f_direction_substring in filter_criteria_set
                )
            )
        ]
        filtered_sorted_arrivals = sorted(
            filtered_predictions, key=lambda p: p.get("timeToStation", math.inf)
        )
        final_display_info = []
        for arrival in filtered_sorted_arrivals[:n]:
            destination = arrival.get("towards") or arrival.get("destinationName")
            destination = destination if destination else "Unknown Destination"
            expected_arrival_utc_str = arrival.get("expectedArrival")
            arrival_dt = None
            if expected_arrival_utc_str:
                try:
                    naive_dt = datetime.strptime(
                        expected_arrival_utc_str, "%Y-%m-%dT%H:%M:%SZ"
                    )
                    arrival_dt = naive_dt.replace(tzinfo=pytz.utc)
                except ValueError:
                    print(
                        f"Warning: Could not parse expectedArrival: {expected_arrival_utc_str}"
                    )
            if arrival_dt is not None:
                final_display_info.append(
                    {
                        "destination": destination,
                        "arrival_time": arrival_dt,
                        "timeToStation": arrival.get("timeToStation"),
                        "lineName": arrival.get("lineName"),
                    }
                )
        return final_display_info
    except Exception as e:
        print(f"An unexpected error occurred in get_arrivals: {e}")
        return []


# --- DISPLAY DRAWING FUNCTIONS ---
# These functions draw content onto a 'draw_obj' (PIL.ImageDraw.Draw) directly,
# which is typically the off-screen buffer of the Render Worker thread.


def draw_centered_text_rows(
    draw_obj: ImageDraw.ImageDraw,
    rows_text: list[str],
    font: ImageFont.FreeTypeFont,
):
    """Draws multiple lines of text, centered horizontally and stacked vertically, onto the given draw object."""
    row_dimensions = []
    total_text_height = 0
    for row_content in rows_text:
        bbox = font.getbbox(row_content)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        row_dimensions.append(
            {"content": row_content, "width": width, "height": height}
        )
        total_text_height += height
    total_height_with_spacing = (
        total_text_height
        + (len(rows_text) - 1) * config.display_settings["row_padding"]
    )
    start_y_offset = (display_device.height - total_text_height) / 2
    current_y = start_y_offset
    for row_data in row_dimensions:
        row_content = row_data["content"]
        row_width = row_data["width"]
        row_height = row_data["height"]
        x_offset = (display_device.width - row_width) / 2
        draw_obj.text((x_offset, current_y), text=row_content, font=font, fill="yellow")
        current_y += row_height + config.display_settings["row_padding"]


def draw_initial_display(station_info: dict):
    """
    Draws the initial welcome screen as a full screen update.
    This clears the entire display via luma's canvas.
    """
    with canvas(display_device) as draw_obj:  # This clears the whole display
        draw_centered_text_rows(
            draw_obj,
            ["Welcome to", station_info["name"]],
            fontBold,
        )


def draw_pause_display(temp: float):
    """
    Draws a display indicating that the pi is pausing until the
    temperature has dropped back below the safe threshold.
    """
    with canvas(display_device) as draw_obj:  # This clears the whole display
        draw_centered_text_rows(
            draw_obj,
            [
                "Raspberry Pi temperature is " + f"{temp:.1f}" + " C.",
                "Waiting for temperature to drop below "
                + str(config.max_pi_temp - 3)
                + " C.",
            ],
            font,
        )


def draw_clock(
    draw_obj: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
):
    """
    Draws the live clock at the bottom of the display onto the given draw object.
    It's responsible for drawing the text, but not for clearing or display update.
    """
    # Clear the entire clock display area on the buffer to black
    draw_obj.rectangle(
        clock_display_rect,
        fill="black",
    )

    clock_str = datetime.now(pytz.timezone("Europe/London")).strftime("%H:%M:%S")

    draw_obj.text(
        (clock_display_rect[0], clock_display_rect[1]),
        text=clock_str,
        font=font,
        fill="yellow",
    )


def draw_arrival_lines(
    draw_obj: ImageDraw.ImageDraw,
    arrivals: list,
    font: ImageFont.FreeTypeFont,
):
    """
    Draws the list of arrival predictions on the main board area onto the global buffer.
    It clears the entire arrivals area on the buffer before redrawing.
    """

    # Clear the entire arrivals display area on the buffer to black
    draw_obj.rectangle(
        arrivals_display_rect,
        fill="black",
    )

    max_y_for_arrivals = arrivals_display_rect[3]

    row_num = 1

    for arrival in arrivals:
        time_to_arrival, time_width, display_check = get_time_to_arrival(arrival, font)

        if display_check:
            ypos = (row_num - 1) * (
                config.fontSize + config.display_settings["row_padding"]
            ) + config.display_settings["yoffset"]

            if ypos >= max_y_for_arrivals:
                break

            draw_obj.text(
                (config.display_settings["xoffset"], ypos),
                text=str(row_num),
                font=font,
                fill="yellow",
            )
            draw_obj.text(
                (
                    config.display_settings["xoffset"]
                    + config.display_settings["space_arrival_num_dest_name"],
                    ypos,
                ),
                text=arrival["destination"],
                font=font,
                fill="yellow",
            )

            if len(config.lines1) > 1:
                # If multiple lines are configured, display the line name
                # at the end of the row.
                draw_obj.text(
                    (
                        config.display_settings["xoffset_line_name"],
                        ypos,
                    ),
                    text=arrival["lineName"],
                    font=font,
                    fill="yellow",
                )

            draw_obj.text(
                (
                    display_device.width
                    - time_width
                    - config.display_settings["xoffset"],
                    ypos,
                ),
                text=time_to_arrival,
                font=font,
                fill="yellow",
            )
            row_num += 1


# --- BACKGROUND WORKER THREAD FUNCTIONS ---
# These threads run in the background, performing API fetches and rendering.


def api_fetch_worker(
    station_info: dict,
    lines_filter1: set,
    lines_filter2: set,
    pause_event: threading.Event,
):
    """
    Fetches raw API data periodically and puts it into raw_api_data_queue.
    This thread performs Task 3: fetching new API data every 30 seconds.
    """
    while True:
        pause_event.wait()  # Blocks until pause_event is set
        try:
            print(
                f"DEBUG API Fetch Worker: Fetching new raw API data at {datetime.now().strftime('%H:%M:%S')}..."
            )

            new_arrivals1 = get_arrivals(
                station_info,
                lines_filter1,
                _session=API_SESSION,
            )

            new_arrivals2 = get_arrivals(
                station_info,
                lines_filter2,
                _session=API_SESSION,
            )

            try:
                # Clear any old data in queue, ensuring only the latest is available
                while not raw_api_data_queue1.empty():
                    raw_api_data_queue1.get_nowait()
                raw_api_data_queue1.put_nowait(new_arrivals1)

                while not raw_api_data_queue2.empty():
                    raw_api_data_queue2.get_nowait()
                raw_api_data_queue2.put_nowait(new_arrivals2)

                print(
                    "DEBUG API Fetch Worker: New raw API data successfully put into queue."
                )
            except queue.Full:
                print(
                    "WARNING API Fetch Worker: Raw API data queue was full, render worker too slow. Data dropped."
                )

        except Exception as e:
            print(
                f"ERROR API Fetch Worker: Data fetch failed: {e}. Retrying after sleep."
            )

        time.sleep(config.refresh_interval_TFL)


def arrival_lines_worker(pause_event: threading.Event):
    """
    This thread is responsible for drawing all display elements onto an off-screen buffer.
    It takes raw API data from the API fetcher and renders full frames (clock + arrivals),
    then puts completed frames into rendered_frames_queue for the main thread.
    This thread handles Task 2 (drawing arrivals at 1 FPS) and preparing clock updates (part of Task 1).
    """

    # Private buffer and drawing handle for this worker thread
    # render_buffer = Image.new(display_device.mode, display_device.size)
    # render_draw_handle = ImageDraw.Draw(render_buffer)
    render_buffer1 = Image.new(display_device.mode, display_device.size)
    render_draw_handle1 = ImageDraw.Draw(render_buffer1)
    render_buffer2 = Image.new(display_device.mode, display_device.size)
    render_draw_handle2 = ImageDraw.Draw(render_buffer2)

    # Variables for state of arrivals data consumed from API Fetch Worker
    current_arrivals1 = []
    current_arrivals2 = []

    # Timing for rendering arrivals (Task 2: e.g., 0.5 FPS)
    arrivals_render_interval = config.refresh_interval_display

    while True:

        pause_event.wait()  # Blocks until pause_event is set

        loop_start_time = time.monotonic()

        # --- Get latest raw API data (non-blocking) ---
        try:
            current_arrivals1 = raw_api_data_queue1.get_nowait()
            current_arrivals2 = raw_api_data_queue2.get_nowait()
            print("DEBUG Render Worker: Consumed new raw API data from queue.")
        except queue.Empty:
            pass  # No new raw API data, use existing

        # --- Draw Arrival Lines  ---

        draw_arrival_lines(
            render_draw_handle1,
            current_arrivals1,
            font=font,
        )

        draw_arrival_lines(
            render_draw_handle2,
            current_arrivals2,
            font=font,
        )

        # --- Put the completed frame COPY into the output queue for the main thread ---
        try:
            while not rendered_frames_queue1.empty():
                rendered_frames_queue1.get_nowait()
            rendered_frames_queue1.put_nowait(render_buffer1.copy())
            while not rendered_frames_queue2.empty():
                rendered_frames_queue2.get_nowait()
            rendered_frames_queue2.put_nowait(
                render_buffer2.copy()
            )  # Put a COPY to avoid race conditions

            print(
                f"DEBUG Render Worker: display with updated arrival lines put into queue."
            )
        except queue.Full:
            print(
                "WARNING Render Worker: Rendered frames queue was full, main thread too slow to consume."
            )

        # Sleep to control render worker's own FPS
        render_duration = time.monotonic() - loop_start_time
        sleep_time = arrivals_render_interval - render_duration
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(
                f"WARNING Render Worker: Took too long ({render_duration:.3f}s) for {arrivals_render_interval:.3f}s budget."
            )


# --- MAIN EXECUTION LOGIC (PRIMARY DISPLAY THREAD) ---
def main():

    try:

        initialize_fonts()

        # --- Display Device Initialization ---
        global display_device
        if IS_RASPBERRY_PI:
            serial_interface = spi(port=0, device=0, gpio=None)
            display_device = ssd1322(serial_interface, rotate=config.displayRotation)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(config.switch_GPIO_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        else:
            print("DEBUG Main: Initializing Pygame emulator...")
            display_device = pygame(width=256, height=64, rotate=config.displayRotation)

        # --- GLOBAL ARRIVAL LINES AND CLOCK RECTANGLES INITIALIZATION ---
        global arrivals_display_rect, clock_display_rect
        bbox_clock = fontBold.getbbox("00:00:00")
        clock_width = bbox_clock[2] - bbox_clock[0]
        clock_height = bbox_clock[3] - bbox_clock[1]

        if len(config.lines1) > 1:
            line_width = 0
            for line in config.lines1:
                bbox_line = font.getbbox(line["line"])
                line_width = max(line_width, bbox_line[2] - bbox_line[0])
            bbox_arrival_time = font.getbbox("XX min")
            arrival_time_width = bbox_arrival_time[2] - bbox_arrival_time[0]
            config.display_settings["xoffset_line_name"] = (
                display_device.width
                - arrival_time_width
                - line_width
                - config.display_settings["xoffset"]
                - config.display_settings["space_line_name_arrival_time"]
            )

        arrivals_display_rect = (
            0,
            0,
            display_device.width,
            display_device.height
            - (
                clock_height
                + config.display_settings["yoffset"]
                + config.display_settings["row_padding"]
            ),  # minus 2 for padding,
        )
        clock_display_rect = (
            (display_device.width - clock_width) / 2,
            display_device.height - (clock_height + config.display_settings["yoffset"]),
            (display_device.width + clock_width) / 2,
            display_device.height,
        )

        # --- GLOBAL DISPLAY OUTPUT BUFFER INITIALIZATION ---
        global display_output_buffer
        display_output_buffer = Image.new(display_device.mode, display_device.size)

        # --- Initial Data Fetch (Blocking, but only at startup) ---
        lines_filter1 = get_lines_filter(config.lines1)
        lines_filter2 = get_lines_filter(config.lines2)
        station_info = get_station_id(
            _session=API_SESSION,
            lines_filter1=lines_filter1,
            lines_filter2=lines_filter2,
        )

        print("DEBUG Main: Initial arrival data fetched.")

        # --- Draw Initial Welcome Display ---
        draw_initial_display(station_info)
        time.sleep(2)

        print("DEBUG Main: Display initialized. Starting multi-threaded main loop...")

        # --- Start Worker Threads ---

        pause_event = threading.Event()
        pause_event.set()  # Set it so the thread starts in a 'resumed' state

        api_fetch_thread = threading.Thread(
            target=api_fetch_worker,
            args=(
                station_info,
                lines_filter1,
                lines_filter2,
                pause_event,
            ),
            daemon=True,
        )
        api_fetch_thread.start()
        print("DEBUG Main: API Fetch Worker started.")

        arrival_lines_thread = threading.Thread(
            target=arrival_lines_worker,
            args=(pause_event,),
            daemon=True,
        )
        arrival_lines_thread.start()
        print("DEBUG Main: Arrival Lines Worker started.")

        # --- Main Display Loop (TASK 1: Updates physical display) ---
        TARGET_DISPLAY_FPS = 5
        frame_time_budget = 1.0 / TARGET_DISPLAY_FPS

        while True:

            loop_start_time = time.monotonic()

            # --- Get new rendered frame from Render Worker (Non-blocking) ---
            try:
                if IS_RASPBERRY_PI:
                    if GPIO.input(config.switch_GPIO_pin):
                        new_rendered_frame = rendered_frames_queue1.get_nowait()
                    else:
                        new_rendered_frame = rendered_frames_queue2.get_nowait()

                    # Monitor the raspberry pi's temperature
                    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                        temp = float(f.read().strip()) / 1000.0
                    if temp > config.max_pi_temp:
                        pause_event.clear()
                        while temp > config.max_pi_temp - 3:
                            draw_pause_display(temp)
                            print("DEBUG Main: Sleeping for 10 seconds to cool down.")
                            time.sleep(10)
                            with open(
                                "/sys/class/thermal/thermal_zone0/temp", "r"
                            ) as f:
                                temp = (
                                    float(f.read().strip()) / 1000.0
                                )  # The temperature is given in millidegrees Celsius, so divide by 1000
                        pause_event.set()

                else:
                    new_rendered_frame = rendered_frames_queue1.get_nowait()

                # Paste the new frame onto the display_output_buffer
                display_output_buffer.paste(new_rendered_frame, (0, 0))
                print("DEBUG Main: Consumed new rendered frame from Render Worker.")
            except queue.Empty:
                pass  # No new frame yet, display the previous one.

                # --- Draw Clock (always redraw, part of Task 1 preparation) ---

            render_draw_handle = ImageDraw.Draw(display_output_buffer)

            t1 = time.monotonic()
            draw_clock(
                render_draw_handle,
                font=fontBold,
            )
            print(f"DEBUG Main: Clock drawn in {time.monotonic() - t1:.3f}s.")

            t2 = time.monotonic()
            # --- PHYSICAL DISPLAY UPDATE (TASK 1) ---
            # This sends the entire display_output_buffer to the physical display/emulator.
            # This operation still takes ~0.5s on Pi for SSD1322, so physical FPS is capped.
            display_device.display(display_output_buffer)
            print(f"DEBUG Main: Display updated in {time.monotonic() - t2:.3f}s.")
            # --- Loop Timing and Control ---
            loop_end_time = time.monotonic()
            loop_duration = loop_end_time - loop_start_time

            sleep_time = frame_time_budget - loop_duration
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                print(
                    f"WARNING Main: Loop took longer than {frame_time_budget:.3f}s! (Actual: {loop_duration:.3f}s) @ {datetime.now().strftime('%H:%M:%S')}. Physical FPS capped by display.display() time."
                )

    except Exception as e:
        print(f"An error occurred in main: {e}")
        if display_device:
            try:
                if hasattr(display_device, "cleanup"):
                    print("DEBUG Main: Calling display.cleanup()...")
                    display_device.cleanup()
                elif hasattr(display_device, "hide"):
                    print("DEBUG Main: Calling display.hide()...")
                    display_device.hide()
            except Exception as ce:
                print(f"DEBUG Main: Error during display cleanup: {ce}")
        sys.exit(1)


# --- APPLICATION ENTRY POINT ---
if __name__ == "__main__":

    main()
