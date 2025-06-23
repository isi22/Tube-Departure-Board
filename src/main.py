import config
import os
import time  # Use time.time() for API refresh interval, time.monotonic() for loop timing
import sys
import requests
import json
from datetime import datetime
import math
import pytz

# Conditional imports for display driver vs. emulator
if sys.platform.startswith("linux") and os.uname().machine.startswith("arm"):
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1322

    IS_RASPBERRY_PI = True
    try:  # Dummy pygame for Pi consistency
        from luma.emulator.device import pygame
    except ImportError:

        class pygame:
            def __init__(self, *args, **kwargs):
                pass

            def command(self, *args, **kwargs):
                pass

            def show(self):
                pass  # Add dummy show method

else:
    from luma.emulator.device import pygame

    IS_RASPBERRY_PI = False

from PIL import ImageFont, ImageDraw, Image
from luma.core.render import canvas

# --- Global Font Definitions (Loaded once) ---
font = None
fontBold = None
fontBoldTall = None
FONT_SIZE = 10


def make_Font(name, size):
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", name))
    try:
        return ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.BASIC)
    except IOError:
        print(f"Error: Could not load font from {font_path}. Using default.")
        return ImageFont.load_default()


def initialize_fonts():
    global font, fontBold, fontBoldTall
    font = make_Font("Dot Matrix Regular.ttf", FONT_SIZE)
    fontBold = make_Font("Dot Matrix Bold.ttf", FONT_SIZE)
    fontBoldTall = make_Font("Dot Matrix Bold Tall.ttf", 2 * FONT_SIZE)


def draw_centered_text_rows(
    display: object,
    rows_text: list[str],
    font: ImageFont.FreeTypeFont,
    fill_color: str = "yellow",
    row_spacing: int = 3,
):
    if not isinstance(rows_text, list) or not all(
        isinstance(row, str) for row in rows_text
    ):
        print("Error: 'rows_text' must be a list of strings.")
        return
    if not hasattr(display, "width") or not hasattr(display, "height"):
        print("Error: 'display' object must have 'width' and 'height' attributes.")
        return
    if not rows_text:
        return

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
    start_y_offset = (display.height - total_height_with_spacing) / 2
    current_y = start_y_offset

    try:
        with canvas(display) as draw:
            for row_data in row_dimensions:
                row_content = row_data["content"]
                row_width = row_data["width"]

                x_offset = (display.width - row_width) / 2

                draw.text(
                    (x_offset, current_y), text=row_content, font=font, fill=fill_color
                )
                current_y += row_data["height"] + row_spacing

    except Exception as e:
        print(f"An error occurred while drawing the centered text rows: {e}")


def draw_initial_display(display, station):
    rows = ["Welcome to", station["name"]]
    draw_centered_text_rows(display, rows, fontBold, fill_color="yellow", row_spacing=3)


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


def draw_departure_board(
    display,
    arrivals,
    xoffset=15,
    row_padding=3,
    space_num_destination=13,
    yoffset=2,
    earliest_arrival=0,
):
    with canvas(display) as draw:
        # Draw the live clock first
        london_tz = pytz.timezone("Europe/London")
        current_london_time = datetime.now(london_tz)
        clock_str = current_london_time.strftime("%H:%M:%S")

        bbox_clock = fontBold.getbbox(clock_str)  # Use bbox_clock to avoid name clash
        clock_width = bbox_clock[2] - bbox_clock[0]
        clock_height = bbox_clock[3] - bbox_clock[1]
        x_offset_clock = (display.width - clock_width) / 2
        draw.text(
            (
                x_offset_clock,
                display.height - (clock_height + yoffset),
            ),  # Use x_offset_clock
            text=clock_str,
            font=fontBold,
            fill="yellow",
        )

        # Draw arrival entries
        row_num = 1
        max_y_for_arrivals = display.height - (
            clock_height + yoffset + FONT_SIZE + row_padding
        )  # Space above clock

        for arrival in arrivals:
            time_to_arrival, time_width, display_check = get_time_to_arrival(
                arrival, font, earliest_arrival
            )
            if display_check:
                ypos = (row_num - 1) * (FONT_SIZE + row_padding) + yoffset

                # Check if this row would overlap with the clock or go off screen
                if ypos >= max_y_for_arrivals:
                    break  # Stop drawing if no more space

                # Draw row number (optional, often implied by order)
                # draw.text((xoffset, ypos), text=str(row_num), font=font, fill="yellow")

                # Draw destination (adjust xoffset for number removal if desired)
                draw.text(
                    (xoffset, ypos),  # Starts at xoffset
                    text=arrival["destination"],
                    font=font,
                    fill="yellow",
                )

                # Draw time to arrival on the right
                draw.text(
                    (display.width - time_width - xoffset, ypos),
                    text=time_to_arrival,
                    font=font,
                    fill="yellow",
                )
                row_num += 1


def query_TFL(url: str, params: dict = None, max_retries: int = 3):
    for retry_attempt in range(max_retries):
        try:
            t1 = time.time()
            response = requests.get(url, params=params, timeout=10)
            print(f"time taken for request: {(time.time()-t1):.2f} seconds")
            response.raise_for_status()
            json_response = response.json()
            if json_response:
                return json_response
            else:
                print(f"Warning: TFL API returned an empty JSON response for {url}")
                if retry_attempt == max_retries - 1:
                    raise ValueError(
                        "TFL API returned an empty or invalid JSON response after retries."
                    )
        except requests.exceptions.RequestException as e:
            print(f"Request error (Attempt {retry_attempt + 1}/{max_retries}): {e}")
            if retry_attempt == max_retries - 1:
                raise RuntimeError(
                    f"Failed to fetch data from {url} after {max_retries} retries: {e}"
                )
        except json.JSONDecodeError as e:
            print(f"JSON decode error (Attempt {retry_attempt + 1}/{max_retries}): {e}")
            if retry_attempt == max_retries - 1:
                raise ValueError(
                    f"Failed to decode JSON from {url} after {max_retries} retries: {e}"
                )
    raise RuntimeError("Unexpected exit from query_TFL retry loop.")


def get_station_id():
    TFL_STOPPOINT_SEARCH_URL = "https://api.tfl.gov.uk/StopPoint/Search"
    params = {
        "query": config.station,
        "modes": config.mode,
        "maxResults": 1,
        "app_key": config.api_key,
    }
    response = query_TFL(TFL_STOPPOINT_SEARCH_URL, params)
    if response and response.get("matches") and len(response["matches"]) > 0:
        first_match = response["matches"][0]
        return {"id": first_match.get("id"), "name": first_match.get("name")}
    else:
        raise RuntimeError(f"Could not find station ID for '{config.station}'.")


def get_lines_filter(lines_config_list):
    filter_set = set()
    for entry in lines_config_list:
        line = entry.get("line")
        direction = entry.get("direction")
        if line and direction:
            filter_set.add((line.lower(), direction.lower()))
    return filter_set


def get_arrivals(station, filter_criteria_set, earliest_arrival_seconds=0, n=7):
    try:
        TFL_STOPPOINT_ARRIVALS_URL = (
            "https://api.tfl.gov.uk/StopPoint/" + station["id"] + "/Arrivals"
        )
        all_arrivals = query_TFL(TFL_STOPPOINT_ARRIVALS_URL)

        if not isinstance(all_arrivals, list):
            print(
                f"Warning: TFL API response was not a list. Received: {type(all_arrivals)}"
            )
            return []

        # Debugging hook for filtering (as per previous answers)
        # debug_output = []
        # _debug_filter_condition_fn = lambda pl, pp, fl, fds: _debug_filter_condition(pl, pp, fl, fds, debug_output)

        filtered_predictions = [
            p
            for p in all_arrivals
            if (
                (p_line := p.get("lineName", "").lower())
                and (p_platform := p.get("platformName", "").lower())
                and p.get("timeToStation", float("inf")) >= earliest_arrival_seconds
                and any(
                    # _debug_filter_condition_fn(p_line, p_platform, f_line, f_direction_substring) and # Uncomment for debugging
                    f_line == p_line and f_direction_substring in p_platform
                    for f_line, f_direction_substring in filter_criteria_set
                )
            )
        ]
        # if debug_output: # Uncomment for debugging
        #    print("\n--- Filtering Debug Output ---")
        #    for msg in debug_output: print(msg)
        #    print("--- End Filtering Debug Output ---\n")

        filtered_sorted_arrivals = sorted(
            filtered_predictions,
            key=lambda p: p.get("timeToStation", float("inf")),
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
                    utc_timezone = pytz.utc
                    arrival_dt = naive_dt.replace(tzinfo=utc_timezone)
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

        # print(f"\n--- get_arrivals() returning {len(final_display_info)} entries ---")
        # for i, info in enumerate(final_display_info):
        #     print(
        #         f"  [{i+1}] To: {info['destination']}, Vehicle ID: {info['vehicle_id']}, Time To Station: {info['timeToStation']/60:.2f} min, Arriving: {info['arrival_time'].strftime('%H:%M:%S %Z')}"
        #     )

        return final_display_info

    except Exception as e:
        print(f"An unexpected error occurred in get_arrivals: {e}")
        return []


def main():
    display = None  # Initialize display to None outside try-block for cleanup
    try:
        initialize_fonts()

        if IS_RASPBERRY_PI:
            serial = spi(port=0, device=0, gpio=None)
            display = ssd1322(serial, rotate=config.displayRotation)
        else:
            print("DEBUG: Initializing Pygame emulator...")
            display = pygame(
                width=256,
                height=64,
                rotate=config.displayRotation,
            )
            # display.show() # Often called automatically by luma, but explicit is fine.

        station = get_station_id()
        # Assume config.lines1 and config.lines2 are lists of dictionaries as discussed
        lines1_filter = get_lines_filter(config.lines1)
        lines2_filter = get_lines_filter(config.lines2)

        # Ensure config.earliest_arrival is in seconds now
        earliest_arrival_seconds = config.earliest_arrival

        # Fetch initial arrival data immediately so the board isn't blank
        print("DEBUG: Fetching initial arrival data...")
        current_arrivals1 = get_arrivals(
            station, lines1_filter, earliest_arrival_seconds
        )
        # current_arrivals2 = get_arrivals(
        #     station, lines2_filter, earliest_arrival_seconds
        # )
        print("DEBUG: Initial arrival data fetched.")

        draw_initial_display(display, station)
        time.sleep(2)  # Show welcome screen for a moment

        print("Display initialized. Starting main loop...")

        last_api_refresh_time = (
            time.monotonic()
        )  # Use monotonic for accurate time differences

        # Define a target framerate/update rate for the display (e.g., 10 frames per second)
        target_fps = 10
        frame_time_budget = 1.0 / target_fps  # e.g., 0.1 seconds per frame

        while True:
            loop_start_time = (
                time.monotonic()
            )  # Measure start of current loop iteration

            # --- API Data Refresh Logic ---
            current_time_for_api_check = (
                time.monotonic()
            )  # Use monotonic for this check too
            if (
                current_time_for_api_check - last_api_refresh_time
                >= config.refresh_interval
            ):
                print(
                    f"DEBUG: API Refresh interval met. Fetching new data at {datetime.now(pytz.timezone('Europe/London')).strftime('%H:%M:%S')}..."
                )
                try:
                    # Fetching these might take time, blocking the loop
                    new_arrivals1 = get_arrivals(
                        station, lines1_filter, earliest_arrival_seconds
                    )
                    # new_arrivals2 = get_arrivals(
                    #     station, lines2_filter, earliest_arrival_seconds
                    # )

                    # Only update if successful (to avoid clearing valid data if API fails)
                    current_arrivals1 = new_arrivals1
                    # current_arrivals2 = new_arrivals2
                    # print(
                    #     f"DEBUG: Data refreshed. Arrivals1 count: {len(current_arrivals1)}, Arrivals2 count: {len(current_arrivals2)}"
                    # )
                except Exception as e:
                    print(f"ERROR: API data fetch failed: {e}. Keeping old data.")

                last_api_refresh_time = (
                    current_time_for_api_check  # Update API refresh time
                )

            # --- Display Drawing Logic ---
            # This block runs every frame, drawing with current (possibly old) data
            # Combine arrivals1 and arrivals2 if both are to be shown on the same board
            # all_current_arrivals = current_arrivals1 + current_arrivals2
            # Sort combined arrivals again for the display, as timeToStation changes
            # This is important for "due" calculation being based on current time
            all_current_arrivals_sorted = sorted(
                current_arrivals1,
                key=lambda p: p["arrival_time"].timestamp()
                - time.time(),  # Sort by actual seconds remaining
            )

            draw_departure_board(
                display,
                all_current_arrivals_sorted,  # Pass the combined and re-sorted list
                earliest_arrival=earliest_arrival_seconds,
            )

            # --- Loop Timing and Control ---
            loop_end_time = time.monotonic()
            loop_duration = loop_end_time - loop_start_time

            # Sleep to maintain the target FPS
            sleep_time = frame_time_budget - loop_duration
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # This warning indicates your loop is too slow to hit the target FPS
                # Reduce target_fps or optimize drawing/data processing.
                print(
                    f"WARNING: Loop took longer than {frame_time_budget:.3f}s! (Actual: {loop_duration:.3f}s)"
                )

            # Optional: Print total loop duration for debugging "skipping seconds"
            # current_total_loop_duration = time.monotonic() - loop_start_time
            # print(f"DEBUG: Loop took {current_total_loop_duration:.3f}s. Clock rendered at {datetime.now(pytz.timezone('Europe/London')).strftime('%H:%M:%S')}")

    except Exception as e:
        print(f"An error occurred in main: {e}")
        if display:
            try:
                if hasattr(display, "cleanup"):
                    print("DEBUG: Calling display.cleanup()...")
                    display.cleanup()
            except Exception as ce:
                print(f"DEBUG: Error during display cleanup: {ce}")
        sys.exit(1)


if __name__ == "__main__":
    main()
