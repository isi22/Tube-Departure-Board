import os

displayRotation = 0  # 0 is no rotation, 1 is rotate 90° clockwise, 2 is 180° rotation and 3 represents 270° rotation.
station = "Barons Court"  # The station to display on the board
mode = "tube"

lines = [
    {"line": "Piccadilly", "direction": "eastbound"},
    {"line": "District", "direction": "eastbound"},
]  # The lines and directions to display on the board, use trial and error to find the correct direction for each line

earliest_arrival = 8  # The earliest arrival time in minutes to display on the board
refresh_interval = 10  # The interval in seconds to refresh tfl data
api_key = None  # os.getenv("TFL_API_KEY")

display_settings = {
    "xoffset": 3,  # Padding at left and right of display edge
    "yoffset": 3,  # Padding at top and bottom of display edge
    "row_padding": 3,  # Padding between rows"
    "space_arrival_num_dest_name": 13,  # Space between arrival number and destination name
    "space_line_name_arrival_time": 25,  # Space between line name and arrival time
}

fontSize = 10  # Font size for the display, 10 is a good size for 128x64 displays

switch_GPIO_pin = 17
