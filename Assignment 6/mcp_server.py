# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import time
import subprocess

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


@mcp.tool()
async def write_to_paint(note_for_paint: str, color: str) -> dict:
    """Open Windows Paint and write text using the text tool at specified coordinates."""
    try:
        import pyautogui
        import time
        import win32com.client
        import win32gui
        import win32con
        
        # Start Paint
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.Run("mspaint")
        time.sleep(3)  # Wait for Paint to open

        # Get Paint window handle
        def enum_windows_callback(hwnd, results):
            if win32gui.GetWindowText(hwnd).startswith("Untitled - Paint"):
                results.append(hwnd)
            return True

        paint_windows = []
        win32gui.EnumWindows(enum_windows_callback, paint_windows)
        
        if not paint_windows:
            raise Exception("Could not find Paint window")

        paint_hwnd = paint_windows[0]
        
        # Activate Paint window and maximize it
        win32gui.ShowWindow(paint_hwnd, win32con.SW_MAXIMIZE)
        win32gui.SetForegroundWindow(paint_hwnd)
        time.sleep(1)

        # Get window dimensions
        rect = win32gui.GetWindowRect(paint_hwnd)
        window_left = rect[0]
        window_top = rect[1]

        # Select rectangle tool (R key)
        pyautogui.press('r')
        time.sleep(1)

        # Draw rectangle at position (600, 500) with width 300 and height 200
        start_x = window_left + 600
        start_y = window_top + 500
        end_x = start_x + 300
        end_y = start_y + 200

        # Move to start position and draw rectangle
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        pyautogui.moveTo(end_x, end_y)
        pyautogui.mouseUp()
        time.sleep(1)

        # First try using keyboard shortcut for text tool (A key)
        pyautogui.press('a')
        time.sleep(1)

        # Then click the text tool icon as backup
        pyautogui.moveTo(423, 107)
        pyautogui.click()
        time.sleep(1)

        # Click inside the rectangle to start typing
        text_x = start_x + 150  # Center of rectangle
        text_y = start_y + 100  # Center of rectangle
        pyautogui.moveTo(text_x, text_y)
        pyautogui.click()
        time.sleep(1)

        # Ensure text tool is selected by pressing 'A' again
        pyautogui.press('a')
        time.sleep(0.5)
        
        # Click again to ensure text input is active
        pyautogui.click()
        time.sleep(0.5)

        # Type the text with a small delay between characters
        pyautogui.write(note_for_paint, interval=0.1)
        time.sleep(1)

        # Press Enter to finish typing
        pyautogui.press('enter')
        time.sleep(0.5)

        # Click outside the text box to ensure it's finalized
        pyautogui.click(text_x + 100, text_y + 100)
        time.sleep(0.5)

        return {
            "content": [
                TextContent(
                    type="text",
                    text="Text written to Paint successfully."
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error writing to Paint: {str(e)}"
                )
            ]
        }

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
