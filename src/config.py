import os

displayRotation = 0  # 0 is no rotation, 1 is rotate 90° clockwise, 2 is 180° rotation and 3 represents 270° rotation.
station = "Barons Court"  # The station to display on the board
mode = "tube"

lines1 = [
    {"line": "Piccadilly", "direction": "eastbound"},
    {"line": "District", "direction": "eastbound"},
]  # The lines and directions to display on the board, use trial and error to find the correct direction for each line

lines2 = [
    {"line": "Piccadilly", "direction": "westbound"},
    {"line": "District", "direction": "westbound"},
]  # The lines and directions to display on the board, use trial and error to find the correct direction for each line

earliest_arrival = 8  # The earliest arrival time in minutes to display on the board
refresh_interval = 5  # The interval in seconds to refresh tfl data
api_key = None  # os.getenv("TFL_API_KEY")
