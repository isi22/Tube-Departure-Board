# test_luma_pygame.py
import time
import sys
import os  # For os.uname().machine, if needed by the luma import logic

# Conditional import just like in your main script to be sure
if sys.platform.startswith("linux") and os.uname().machine.startswith("arm"):
    # This path shouldn't be taken on your desktop, but ensures the import consistency
    try:
        # Dummy pygame for Pi branch
        from luma.emulator.device import pygame
    except ImportError:

        class pygame:
            def __init__(self, *args, **kwargs):
                pass

            def command(self, *args, **kwargs):
                pass

else:
    # This is the path for your emulator
    from luma.emulator.device import pygame

from luma.core.render import canvas
from PIL import ImageDraw  # Not strictly needed if you only draw in canvas context

try:
    print("DEBUG: Attempting to create luma.emulator.device.pygame display...")
    # Instantiate the luma pygame device
    # Use generic width/height/rotation to rule out config issues
    display = pygame(width=128, height=64, rotate=0)
    print("DEBUG: luma.emulator.device.pygame display object created.")

    # Draw something on the display using luma's canvas context
    print("DEBUG: Drawing 'Hello Luma!' to the canvas...")
    with canvas(display) as draw:
        # Drawing in yellow for visibility
        draw.text((10, 10), text="Hello Luma!", fill="yellow")
        draw.text((10, 30), text="Test Display", fill="yellow")
    print("DEBUG: Drawing completed. Window should be visible now.")

    # Keep the window open for 5 seconds
    print("DEBUG: Keeping window open for 5 seconds...")
    time.sleep(5)

    # Clean up the display (closes the window)
    print("DEBUG: Calling display.cleanup()...")
    display.cleanup()
    print("DEBUG: Display cleaned up. Exiting.")

except Exception as e:
    print(f"ERROR: An error occurred in minimal Luma Pygame test: {e}")
    # In case of error, sleep to let user see output before terminal closes
    time.sleep(2)
