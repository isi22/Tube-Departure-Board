import os

# --- General Configuration ---

station = "South Kensington"  # The London Underground station to display on the board.
earliest_arrival = 10  # Minimum arrival time (in minutes) for a train to be displayed.
                      # For example, if you need 10 minutes to walk to the station, setting this to 10
                      # will ensure only trains you might realistically catch are shown.

lines1 = [
    {"line": "Piccadilly", "direction": "eastbound"},
    {"line": "District", "direction": "eastbound"},
]  # Primary set of Tube lines and their specific directions to monitor.
   # Valid directions include: "eastbound", "westbound", "northbound", "southbound".
   # For DLR services, use platform for direction (e.g., {"direction": "platform 1"}).

lines2 = [
    {"line": "Piccadilly", "direction": "westbound"},
    {"line": "District", "direction": "westbound"},
]  # Second set of Tube lines and directions.
   # The physical toggle switch on the hardware will cycle the display between lines1 and lines2.

displayRotation = 0  # Rotation of the OLED display content.
                     # 0: No rotation (default orientation)
                     # 1: 90° clockwise rotation
                     # 2: 180° rotation
                     # 3: 270° clockwise rotation

switch_GPIO_pin = 17 # BCM (Broadcom pin numbering) GPIO pin connected to the toggle switch.
                     # Change this value to match your switch's connection.

refresh_interval_TFL = 20  # Interval (in seconds) between API requests to TFL for new data.
refresh_interval_display = 3  # Interval (in seconds) for refreshing the visual content on the OLED display.

max_pi_temp = 60  # Maximum Raspberry Pi CPU temperature (in Celsius) allowed.
                  # If the temperature exceeds this, the display will pause refreshing
                  # until the CPU has cooled down to prevent overheating.


# --- API Key Configuration ---
# Your TfL App Key is retrieved from an environment variable for enhanced security.
# Ensure 'TFL_API_KEY' is set in your system's environment
# (e.g., in your systemd service file).
api_key = os.getenv("TFL_API_KEY")


# --- Display Layout Settings ---
display_settings = {
    "xoffset": 3,  # Horizontal padding (in pixels) from the left and right edges of the display.
    "yoffset": 3,  # Vertical padding (in pixels) from the top and bottom edges of the display.
    "row_padding": 3,  # Vertical spacing (in pixels) between individual rows of arrival information.
    "space_arrival_num_dest_name": 13,  # Horizontal space (in pixels) between the arrival number and the destination name.
    "space_line_name_arrival_time": 25,  # Horizontal space (in pixels) between the line name and the arrival time.
}

fontSize = 10  # Base font size (in pixels) for the display text.
               # 10 is generally a good size for 128x64 OLED displays to fit multiple lines.