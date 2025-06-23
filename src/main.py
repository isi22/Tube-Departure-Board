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
from luma.core.render import canvas  # Used for initial full-screen update only


# --- CONDITIONAL DISPLAY DRIVER / EMULATOR SETUP ---
IS_RASPBERRY_PI = False
if sys.platform.startswith("linux") and os.uname().machine.startswith("arm"):
    try:
        from luma.core.interface.serial import spi
        from luma.oled.device import ssd1322

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
fontBoldTall: ImageFont.FreeTypeFont = None
FONT_SIZE: int = 10

# --- GLOBAL API SESSION & QUEUE ---
API_SESSION = requests.Session()
arrivals_queue = queue.Queue(maxsize=1)

# --- GLOBAL DISPLAY BUFFER AND DRAW HANDLE ---
global_display_buffer: Image.Image = None
global_draw_handle: ImageDraw.ImageDraw = None

# --- Store last drawn content's position/size for selective clearing ---
last_drawn_elements = {
    "clock": {"text": "", "x": 0, "y": 0, "width": 0, "height": 0},
    "arrivals": [],  # List of {'x': 0, 'y': 0, 'width': 0, 'height': 0} for each arrival line
}


# --- HELPER FUNCTIONS (mostly unchanged) ---
def make_Font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", name))
    try:
        return ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.BASIC)
    except IOError:
        return ImageFont.load_default()


def initialize_fonts():
    global font, fontBold, fontBoldTall
    font = make_Font("Dot Matrix Regular.ttf", FONT_SIZE)
    fontBold = make_Font("Dot Matrix Bold.ttf", FONT_SIZE)
    fontBoldTall = make_Font("Dot Matrix Bold Tall.ttf", 2 * FONT_SIZE)


def get_time_to_station_safe(prediction_item: dict) -> float:
    try:
        return float(prediction_item.get("timeToStation", math.inf))
    except (ValueError, TypeError):
        return math.inf


def get_current_london_datetime() -> datetime:
    london_tz = pytz.timezone("Europe/London")
    return datetime.now(london_tz)


def get_arrivals_display_area_rect(  # This function's return value is now primarily for layout, not for display.display() directly
    display_width: int,
    display_height: int,
    estimated_clock_height_plus_yoffset: int,
    font_size: int,
    row_padding: int,
) -> tuple:
    top_y = 2
    bottom_y = display_height - estimated_clock_height_plus_yoffset
    line_total_height = font_size + row_padding
    max_lines_fit = (
        math.floor(max(0, (bottom_y - top_y)) / line_total_height)
        if line_total_height > 0
        else 0
    )
    total_arrivals_display_height = max_lines_fit * line_total_height
    return (0, top_y, display_width, total_arrivals_display_height)


# --- API INTERACTION FUNCTIONS (same as before) ---
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
    return []  # Should not be reached


def get_station_id(_session: requests.Session = None) -> dict:
    TFL_STOPPOINT_SEARCH_URL = "https://api.tfl.gov.uk/StopPoint/Search"
    params = {
        "query": config.station,
        "modes": config.mode,
        "maxResults": 1,
        "app_key": config.api_key,
    }
    response = query_TFL(TFL_STOPPOINT_SEARCH_URL, params, _session=_session)
    if response and response.get("matches") and len(response["matches"]) > 0:
        return response["matches"][0]
    else:
        raise RuntimeError(f"Could not find station ID for '{config.station}'.")


def get_lines_filter(lines_config_list: list) -> set:
    filter_set = set()
    for entry in lines_config_list:
        line = entry.get("line")
        direction_substring = entry.get("direction")
        if line and direction_substring:
            filter_set.add((line.lower(), direction_substring.lower()))
    return filter_set


def get_arrivals(
    station: dict,
    filter_criteria_set: set,
    earliest_arrival_seconds: int = 0,
    n: int = 7,
    _session: requests.Session = None,
) -> list:
    try:
        TFL_STOPPOINT_ARRIVALS_URL = (
            "https://api.tfl.gov.uk/StopPoint/" + station["id"] + "/Arrivals"
        )
        all_arrivals = query_TFL(TFL_STOPPOINT_ARRIVALS_URL, _session=_session)
        if not isinstance(all_arrivals, list):
            return []
        filtered_predictions = [
            p
            for p in all_arrivals
            if (
                (p_line := p.get("lineName", "").lower())
                and (p_platform := p.get("platformName", "").lower())
                and (get_time_to_station_safe(p)) >= earliest_arrival_seconds
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
                        "vehicle_id": arrival.get("vehicleId"),
                    }
                )
        return final_display_info
    except Exception as e:
        print(f"An unexpected error occurred in get_arrivals: {e}")
        return []


# --- BACKGROUND WORKER THREAD FUNCTION (same as before) ---
def fetch_arrivals_worker(
    station_info: dict,
    lines1_filter: set,
    lines2_filter: set,
    earliest_arrival_seconds: int,
    refresh_interval_seconds: int,
):
    while True:
        try:
            print("DEBUG Worker: Fetching new arrival data...")
            new_arrivals1 = get_arrivals(
                station_info,
                lines1_filter,
                earliest_arrival_seconds,
                _session=API_SESSION,
            )
            new_arrivals2 = get_arrivals(
                station_info,
                lines2_filter,
                earliest_arrival_seconds,
                _session=API_SESSION,
            )
            try:
                while not arrivals_queue.empty():
                    arrivals_queue.get_nowait()
                arrivals_queue.put_nowait((new_arrivals1, new_arrivals2))
                print("DEBUG Worker: New arrival data put into queue.")
            except queue.Full:
                print(
                    "WARNING Worker: Arrivals queue was full, could not put new data (main thread consuming too slowly)."
                )
        except Exception as e:
            print(f"ERROR Worker: Failed to fetch arrivals: {e}. Retrying after sleep.")
        time.sleep(refresh_interval_seconds)


# --- DISPLAY DRAWING FUNCTIONS ---
# These functions now draw content onto the global_draw_handle (PIL.ImageDraw.Draw) directly.


def draw_centered_text_rows(
    draw_obj: ImageDraw.ImageDraw,
    display_width: int,
    display_height: int,
    rows_text: list[str],
    font: ImageFont.FreeTypeFont,
    fill_color: str = "yellow",
    row_spacing: int = 3,
):
    # Same logic as before, using draw_obj
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
    total_height_with_spacing = total_text_height + (len(rows_text) - 1) * row_spacing
    start_y_offset = (display_height - total_height_with_spacing) / 2
    current_y = start_y_offset
    for row_data in row_dimensions:
        row_content = row_data["content"]
        row_width = row_data["width"]
        row_height = row_data["height"]
        x_offset = (display_width - row_width) / 2
        draw_obj.text(
            (x_offset, current_y), text=row_content, font=font, fill=fill_color
        )
        current_y += row_height + row_spacing


def draw_initial_display(display_device: object, station_info: dict):
    """
    Draws the initial welcome screen. This clears the entire global buffer,
    draws the welcome message, and then sends the full buffer to the display.
    """
    global global_draw_handle, global_display_buffer  # Ensure global scope for modification

    if global_draw_handle is None or global_display_buffer is None:
        print("ERROR: Global drawing buffer not initialized for initial display!")
        return

    # Clear the entire global buffer to black
    global_draw_handle.rectangle(
        (0, 0, display_device.width, display_device.height), fill="black"
    )

    # Draw content to the global buffer
    draw_centered_text_rows(
        global_draw_handle,
        display_device.width,
        display_device.height,
        ["Welcome to", station_info["name"]],
        fontBold,
        fill_color="yellow",
        row_spacing=3,
    )

    # Send the full, newly drawn buffer to the display device
    display_device.display(global_display_buffer)


def get_time_to_arrival(arrival, font, earliest_arrival=0):
    seconds_to_arrival = int(arrival["arrival_time"].timestamp() - time.time())
    time_to_arrival = " "
    time_width = 0
    display_check = False

    if seconds_to_arrival >= earliest_arrival:
        display_check = True
        minutes_to_arrival = seconds_to_arrival / 60

        if minutes_to_arrival > 1:
            time_to_arrival = f"{math.floor(minutes_to_arrival + 0.5)} min"
        elif seconds_to_arrival > 0:  # If less than a minute, but still > 0 seconds
            time_to_arrival = f"{seconds_to_arrival} s"
        else:
            time_to_arrival = "due"

        bbox = font.getbbox(time_to_arrival)
        time_width = bbox[2] - bbox[0]

    return time_to_arrival, time_width, display_check


def draw_clock(
    draw_obj: ImageDraw.ImageDraw,
    display_width: int,
    display_height: int,
    yoffset: int,
    fontBold: ImageFont.FreeTypeFont,
    clock_area_rect: tuple,
):
    """
    Draws the live clock at the bottom of the display onto the global buffer.
    It clears only the clock's rectangle on the buffer before redrawing.
    """
    # Clear the specific old clock area on the buffer to black
    # clock_area_rect is (x, y, width, height) of the clock's content region
    draw_obj.rectangle(
        (
            clock_area_rect[0],
            clock_area_rect[1],
            clock_area_rect[0] + clock_area_rect[2],
            clock_area_rect[1] + clock_area_rect[3],
        ),
        fill="black",
    )

    clock_str = get_current_london_datetime().strftime("%H:%M:%S")

    bbox_clock = fontBold.getbbox(clock_str)
    clock_width = bbox_clock[2] - bbox_clock[0]
    clock_height = bbox_clock[3] - bbox_clock[1]
    x_offset_clock = (display_width - clock_width) / 2
    y_offset_clock = display_height - (clock_height + yoffset)

    draw_obj.text(
        (x_offset_clock, y_offset_clock),
        text=clock_str,
        font=fontBold,
        fill="yellow",
    )

    # Update last_drawn_elements for the clock (for the next clear cycle)
    # The rect in last_drawn_elements is calculated and stored in main loop's clock_area_rect
    # Here, we just ensure its content is set for potential future reference if needed.
    last_drawn_elements["clock"]["text"] = clock_str


def draw_arrival_lines(
    draw_obj: ImageDraw.ImageDraw,
    display_width: int,
    display_height: int,
    arrivals: list,
    xoffset: int,
    row_padding: int,
    yoffset: int,
    font_size: int,
    earliest_arrival_seconds: int,
    font: ImageFont.FreeTypeFont,
    fontBold: ImageFont.FreeTypeFont,
    arrivals_display_rect: tuple,  # Pass the full arrivals area rect for clearing
):
    """
    Draws the list of arrival predictions on the main board area onto the global buffer.
    It clears the entire arrivals area on the buffer before redrawing.
    """
    # Clear the entire arrivals display area on the buffer to black
    draw_obj.rectangle(
        (
            arrivals_display_rect[0],
            arrivals_display_rect[1],
            arrivals_display_rect[0] + arrivals_display_rect[2],
            arrivals_display_rect[1] + arrivals_display_rect[3],
        ),
        fill="black",
    )

    # Reset last_drawn_elements for arrivals for this frame's elements
    # This list is not strictly needed anymore if clearing full arrivals_display_rect
    # but good to keep for consistency/future features.
    last_drawn_elements["arrivals"] = []

    # Estimate clock height to determine max space for arrivals
    temp_clock_bbox = fontBold.getbbox("00:00:00")
    estimated_clock_height_plus_yoffset = (
        temp_clock_bbox[3] - temp_clock_bbox[1]
    ) + yoffset

    max_y_for_arrivals = display_height - estimated_clock_height_plus_yoffset

    row_num = 0

    for arrival in arrivals:
        time_to_arrival, time_width, display_check = get_time_to_arrival(
            arrival, font, earliest_arrival_seconds
        )

        if display_check:  # Only process and draw if display_check is True
            ypos = row_num * (font_size + row_padding) + yoffset

            if ypos >= max_y_for_arrivals:
                break

            destination_text = arrival["destination"]

            target_time_end_x = display_width - xoffset
            time_text_start_x = target_time_end_x - time_width  # Definition

            dest_text_width = (
                font.getbbox(destination_text)[2] - font.getbbox(destination_text)[0]
            )
            dest_text_end_x = xoffset + dest_text_width

            char_space_width = font.getbbox(" ")[2] - font.getbbox(" ")[0]
            if char_space_width == 0:
                char_space_width = 1

            # --- FIX IS HERE ---
            space_needed_pixels = (
                time_text_start_x - dest_text_end_x
            )  # Corrected variable name
            # --- END FIX ---

            num_spaces = max(1, math.ceil(space_needed_pixels / char_space_width))
            combined_line_text = (
                f"{destination_text}{' ' * num_spaces}{time_to_arrival}"
            )

            max_line_width = display_width - (2 * xoffset)
            bbox_combined = font.getbbox(combined_line_text)

            if (bbox_combined[2] - bbox_combined[0]) > max_line_width:
                avg_char_width = font.getbbox("A")[2] - font.getbbox("A")[0]
                if avg_char_width == 0:
                    avg_char_width = 1
                space_for_dest_pixels = (
                    max_line_width - time_width - (num_spaces * char_space_width)
                )
                max_dest_chars = math.floor(space_for_dest_pixels / avg_char_width)

                if max_dest_chars > 3:
                    destination_text = destination_text[: max_dest_chars - 3] + "..."
                elif max_dest_chars > 0:
                    destination_text = destination_text[:max_dest_chars]
                else:
                    destination_text = ""

                combined_line_text = (
                    f"{destination_text}{' ' * num_spaces}{time_to_arrival}"
                )

            draw_obj.text(
                (xoffset, ypos),
                text=combined_line_text,
                font=font,
                fill="yellow",
            )
            # Store info for this line (for next clear cycle)
            bbox_drawn_text = font.getbbox(combined_line_text)
            last_drawn_elements["arrivals"].append(
                {  # This might not be fully used if entire rect is cleared.
                    "x": xoffset,
                    "y": ypos,
                    "width": bbox_drawn_text[2] - bbox_drawn_text[0],
                    "height": bbox_drawn_text[3] - bbox_drawn_text[1],
                }
            )
            row_num += 1


# --- MAIN EXECUTION LOGIC ---
def main():
    display_device = None

    try:
        initialize_fonts()

        # --- Display Device Initialization ---
        if IS_RASPBERRY_PI:
            serial_interface = spi(port=0, device=0, gpio=None)
            display_device = ssd1322(serial_interface, rotate=config.displayRotation)
        else:
            print("DEBUG: Initializing Pygame emulator...")
            display_device = pygame(
                width=256,
                height=64,
                rotate=config.displayRotation,
            )

        # --- GLOBAL DISPLAY BUFFER AND DRAW HANDLE INITIALIZATION ---
        global global_display_buffer, global_draw_handle
        # Create a full-sized Image buffer in 'L' (8-bit grayscale) mode for SSD1322
        # Use display_device.mode to be compatible with both hardware and emulator
        global_display_buffer = Image.new(display_device.mode, display_device.size)
        global_draw_handle = ImageDraw.Draw(global_display_buffer)

        # --- Initial Data Fetch (Blocking, but only at startup) ---
        station_info = get_station_id(_session=API_SESSION)
        lines1_filter = get_lines_filter(config.lines1)
        lines2_filter = get_lines_filter(config.lines2)
        earliest_arrival_seconds = config.earliest_arrival

        print("DEBUG: Fetching initial arrival data (main thread, blocking)...")
        current_arrivals1 = get_arrivals(
            station_info, lines1_filter, earliest_arrival_seconds, _session=API_SESSION
        )
        current_arrivals2 = get_arrivals(
            station_info, lines2_filter, earliest_arrival_seconds, _session=API_SESSION
        )
        print("DEBUG: Initial arrival data fetched.")

        # --- Draw Initial Welcome Display ---
        # This uses the global buffer and performs a full screen update.
        draw_initial_display(display_device, station_info)
        time.sleep(2)  # Show welcome screen

        print("Display initialized. Starting main loop with partial updates...")

        # --- Start Background API Worker Thread ---
        worker_thread = threading.Thread(
            target=fetch_arrivals_worker,
            args=(
                station_info,
                lines1_filter,
                lines2_filter,
                earliest_arrival_seconds,
                config.refresh_interval,
            ),
            daemon=True,
        )
        worker_thread.start()

        # --- Main Display Loop Control Variables ---
        target_fps = 10
        frame_time_budget = 1.0 / target_fps

        last_api_refresh_check_time = time.monotonic()
        last_arrivals_display_time = time.monotonic()
        arrivals_display_interval = 1.0

        # Pre-calculate estimated clock height for consistent layout and dirty rects
        estimated_clock_height_plus_yoffset = (
            fontBold.getbbox("00:00:00")[3] - fontBold.getbbox("00:00:00")[1]
        ) + 2

        # Bounding box for the clock area (fixed position at bottom)
        clock_area_rect = (
            0,  # x_min: covers full width for safe clear of old clock
            display_device.height
            - estimated_clock_height_plus_yoffset,  # y_min (clock's top Y)
            display_device.width,  # width
            estimated_clock_height_plus_yoffset,  # height
        )

        while True:
            loop_start_time = time.monotonic()

            # --- Check for new data from worker thread (Non-blocking) ---
            try:
                new_arrivals1, new_arrivals2 = arrivals_queue.get_nowait()
                current_arrivals1 = new_arrivals1
                current_arrivals2 = new_arrivals2
                print("DEBUG: Main thread consumed new data from queue.")
            except queue.Empty:
                pass

            # --- API Data Refresh Logic ---
            current_monotonic_time = time.monotonic()
            if (
                current_monotonic_time - last_api_refresh_check_time
                >= config.refresh_interval
            ):
                print(
                    f"DEBUG: API Refresh interval met. (Worker thread is handling data fetch)."
                )
                last_api_refresh_check_time = current_monotonic_time

            # --- PARTIAL UPDATE DISPLAY LOGIC ---
            # All drawing happens to the global_draw_handle (on global_display_buffer)
            # Then display_device.display() is called with the full buffer.

            # 1. Update Clock (Frequent Update: aims for `target_fps`)
            # Draw clock to the global buffer (which includes clearing its area)
            draw_clock(
                global_draw_handle,
                display_device.width,
                display_device.height,
                2,
                fontBold,
                clock_area_rect,
            )
            # Send the entire buffer to the display. No cropping is done here.
            display_device.display(global_display_buffer)

            # 2. Update Arrival Lines (Less Frequent Update: controlled by `arrivals_display_interval`)
            if (
                current_monotonic_time - last_arrivals_display_time
                >= arrivals_display_interval
            ):
                all_current_arrivals = current_arrivals1 + current_arrivals2
                all_current_arrivals_sorted = sorted(
                    all_current_arrivals,
                    key=lambda p: p["arrival_time"].timestamp() - time.time(),
                )

                arrivals_display_rect_for_clear = get_arrivals_display_area_rect(
                    display_device.width,
                    display_device.height,
                    estimated_clock_height_plus_yoffset,
                    FONT_SIZE,
                    3,
                )

                # Draw arrivals to the global buffer (which includes clearing its area)
                draw_arrival_lines(
                    global_draw_handle,
                    display_device.width,
                    display_device.height,
                    all_current_arrivals_sorted,
                    xoffset=15,
                    row_padding=3,
                    yoffset=2,
                    font_size=FONT_SIZE,
                    earliest_arrival_seconds=earliest_arrival_seconds,
                    font=font,
                    fontBold=fontBold,
                    arrivals_display_rect=arrivals_display_rect_for_clear,  # Pass rect to clear this area
                )
                # Send the entire buffer to the display. No cropping is done here.
                display_device.display(global_display_buffer)

                last_arrivals_display_time = current_monotonic_time

            # --- Loop Timing and Control ---
            loop_end_time = time.monotonic()
            loop_duration = loop_end_time - loop_start_time

            sleep_time = frame_time_budget - loop_duration
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                print(
                    f"WARNING: Main loop took longer than {frame_time_budget:.3f}s! (Actual: {loop_duration:.3f}s)"
                )

    except Exception as e:
        print(f"An error occurred in main: {e}")
        if display_device:
            try:
                if hasattr(display_device, "cleanup"):
                    print("DEBUG: Calling display.cleanup()...")
                    display_device.cleanup()
                elif hasattr(display_device, "hide"):
                    print("DEBUG: Calling display.hide()...")
                    display_device.hide()
            except Exception as ce:
                print(f"DEBUG: Error during display cleanup: {ce}")
        sys.exit(1)


# --- APPLICATION ENTRY POINT ---
if __name__ == "__main__":

    main()
