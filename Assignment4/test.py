import pyautogui
import time
from datetime import datetime

filename = "mouse_position_log.txt"

print("You have 10 seconds to move your mouse to the desired location (e.g., Text Tool in Paint)...")
time.sleep(10)

x, y = pyautogui.position()

with open(filename, "a") as file:
    file.write(f"{datetime.now()} - Mouse position: x={x}, y={y}\n")

print(f"Mouse position saved to {filename}")
