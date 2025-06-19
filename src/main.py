import config
import os
import time
import sys  # Import sys to check platform
import requests
import json
from datetime import datetime

# Conditional imports for display driver vs. emulator
if sys.platform.startswith("linux") and os.uname().machine.startswith("arm"):
    # Running on a Raspberry Pi
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1322

    IS_RASPBERRY_PI = True
else:
    # Running on a non-Pi (e.g., desktop for emulation)
    from luma.emulator.device import pygame  # Import the pygame emulator

    IS_RASPBERRY_PI = False


from PIL import ImageFont, ImageDraw, Image
from luma.core.render import canvas

# --- Global Font Definitions (Loaded once) ---
font = None
fontBold = None
fontBoldTall = None
fontBoldLarge = None


def make_Font(name, size):
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", name))
    return ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.BASIC)


def initialize_fonts():
    """Initializes all required fonts."""
    global font, fontBold, fontBoldTall, fontBoldLarge
    font = make_Font("Dot Matrix Regular.ttf", 15)
    fontBold = make_Font("Dot Matrix Bold.ttf", 10)
    fontBoldTall = make_Font("Dot Matrix Bold Tall.ttf", 10)
    fontBoldLarge = make_Font("Dot Matrix Bold.ttf", 20)


def draw_centered_text_rows(
    display: object,
    rows_text: list[str],
    font: ImageFont.FreeTypeFont,
    fill_color: str = "yellow",
    row_spacing: int = 3,
):

    # Calculate dimensions for each row
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

    # Add spacing for all but the last row
    total_height_with_spacing = total_text_height + (len(rows_text) - 1) * row_spacing

    # Calculate initial vertical offset to center all rows
    start_y_offset = (display.height - total_height_with_spacing) / 2

    current_y = start_y_offset

    try:
        with canvas(display) as draw:
            for row_data in row_dimensions:
                row_content = row_data["content"]
                row_width = row_data["width"]
                row_height = row_data["height"]

                # Calculate horizontal offset for this row
                x_offset = (display.width - row_width) / 2

                # Draw the text
                draw.text(
                    (x_offset, current_y), text=row_content, font=font, fill=fill_color
                )

                # Move to the next row's starting Y position
                current_y += row_height + row_spacing

    except Exception as e:
        print(f"An error occurred while drawing the centered text rows: {e}")


def draw_initial_display(display, station):
    rows = ["Welcome to", station["name"]]
    draw_centered_text_rows(display, rows, fontBold, fill_color="yellow", row_spacing=3)


def draw_departure_board(display, arrivals):
    with canvas(display) as draw:
        for row_num, arrival in enumerate(arrivals):
            draw.text(
                (5, ((row_num - 1) * 14) + 5),
                text=str(row_num),
                font=font,
                fill="yellow",
            )
            draw.text(
                (18, ((row_num - 1) * 14) + 5),
                text=arrival["destination"],
                font=font,
                fill="yellow",
            )


def query_TFL(url: str, params: dict = None, max_retries: int = 3):

    for retry_attempt in range(max_retries):
        try:
            response = requests.get(url, params=params).json()
            if response:
                return response
            else:
                raise ValueError("Error Communicating with TFL")
        except ValueError:
            if retry_attempt == 2:
                raise RuntimeError("Failed to fetch station ID after 3 retries.")


def get_station_id():

    TFL_STOPPOINT_SEARCH_URL = "https://api.tfl.gov.uk/StopPoint/Search"  # TFL API endpoint for searching stop points with name that matches the query

    params = {
        "query": config.station,  # user defined station name
        "modes": config.mode,  # user defined mode (e.g., tube, bus, etc.)
        "maxResults": 1,  # return only best match
        "api_key": config.api_key,  # user defined API key
    }

    response = query_TFL(TFL_STOPPOINT_SEARCH_URL, params)
    return {"id": response["matches"][0]["id"], "name": response["matches"][0]["name"]}


def get_lines_filter(lines):
    filter_set = set()
    for entry in lines:
        line = entry["line"]
        direction = entry["direction"]
        if line and direction:
            filter_set.add((line.lower(), direction.lower()))
    return filter_set


def get_arrivals(station, filter, n=5):

    try:

        TFL_STOPPOINT_ARRIVALS_URL = (
            "https://api.tfl.gov.uk/StopPoint/" + station["id"] + "/Arrivals"
        )  # TFL API endpoint for arrival predictions for a specific stop point

        all_arrivals = query_TFL(TFL_STOPPOINT_ARRIVALS_URL)

        filtered_arrivals = [
            p
            for p in all_arrivals
            if (
                (p.get("lineName", "").lower(), p.get("direction", "").lower())
                in filter
            )
        ]

        filtered_sorted_arrivals = sorted(
            filtered_arrivals,
            key=lambda p: p.get("timeToStation", float("inf")),
        )

        final_display_info = []

        for arrival in filtered_sorted_arrivals[:n]:  # Take only the top n
            destination = arrival.get("towards") or arrival.get("destinationName")
            destination = destination if destination else "Unknown Destination"

            expected_arrival_utc_str = arrival.get("expectedArrival")
            arrival_time_display = "N/A"  # Default display string

            if expected_arrival_utc_str:
                arrival_dt = datetime.strptime(
                    expected_arrival_utc_str, "%Y-%m-%dT%H:%M:%SZ"
                )

            final_display_info.append(
                {
                    "destination": destination,
                    "arrival_time": arrival_dt,  # Formatted time string
                }
            )

        # --- Print the final results ---
        print(f"\n--- Final Top {n} Soonest Arrivals ---")
        if not final_display_info:
            print("No matching arrivals found to display.")
        else:
            for i, info in enumerate(final_display_info):
                print(
                    f"[{i+1}] To: {info['destination']}, Arriving: {info['arrival_time']}"
                )

        return final_display_info

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    try:

        initialize_fonts()

        if IS_RASPBERRY_PI:
            # For Raspberry Pi, use the SPI interface to connect to the display
            serial = spi(port=0, device=0, gpio=None)  # Adjust GPIO as needed
            display = ssd1322(serial, rotate=config.displayRotation)
        else:
            # For emulation or non-Pi platforms, use the capture device
            display = pygame(
                width=256,
                height=64,
                rotate=config.displayRotation,
            )
            display.show()  # Show the emulator window

        station = get_station_id()
        lines1_filter = get_lines_filter(config.lines1)
        lines2_filter = get_lines_filter(config.lines2)

        arrivals1 = get_arrivals(station, lines1_filter)
        arrivals2 = get_arrivals(station, lines2_filter)

        draw_initial_display(display, station)

        # Keep the display updated (or running)
        print("Display initialized. Running...")

        last_refresh = time.time()

        while True:
            if time.time() - last_refresh > config.refresh_interval:
                arrivals1 = get_arrivals(station, lines1_filter)
                arrivals2 = get_arrivals(station, lines2_filter)
                last_refresh = time.time()
            draw_departure_board(display, arrivals1)

    except Exception as e:
        print(f"An error occurred: {e}")
        # Consider adding logging or more specific error handling


if __name__ == "__main__":
    main()
