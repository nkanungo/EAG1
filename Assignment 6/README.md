# Assignment 6: MCP Server with Calculator and Image Processing Tools

## Overview

This project implements a FastMCP server that provides a variety of mathematical, image processing, and system automation tools. The server can be used for calculations, image manipulation, and Windows system automation tasks.

## Features

### Mathematical Tools
- Basic arithmetic operations (add, subtract, multiply, divide)
- Advanced mathematical functions (power, square root, cube root)
- Specialized calculations (factorial, log, remainder)
- Trigonometric functions (sin, cos, tan)
- List operations (sum, exponential sum)
- Fibonacci sequence generation

### Image Processing Tools
- Thumbnail creation
- Image format conversion

### System Automation Tools
- Windows Paint automation
- Text writing with color customization

### Additional Tools
- String to ASCII conversion
- Custom mining operation

## Setup

1. **Install Dependencies**:
   ```bash
   pip install mcp pillow pyautogui win32com
   ```

2. **Run the Server**:
   ```bash
   # For development mode
   python mcp_server.py dev

   # For standard mode
   python mcp_server.py
   ```

## Available Tools

### Mathematical Operations
```python
add(a: int, b: int) -> int
subtract(a: int, b: int) -> int
multiply(a: int, b: int) -> int
divide(a: int, b: int) -> float
power(a: int, b: int) -> int
sqrt(a: int) -> float
cbrt(a: int) -> float
factorial(a: int) -> int
log(a: int) -> float
remainder(a: int, b: int) -> int
sin(a: int) -> float
cos(a: int) -> float
tan(a: int) -> float
```

### List Operations
```python
add_list(l: list) -> int
int_list_to_exponential_sum(int_list: list) -> float
fibonacci_numbers(n: int) -> list
```

### Image Processing
```python
create_thumbnail(image_path: str) -> Image
```

### System Automation
```python
write_to_paint(note_for_paint: str, color: str) -> dict
```

### String Operations
```python
strings_to_chars_to_int(string: str) -> list[int]
```

## Usage Examples

### Basic Calculation
```python
result = add(5, 3)  # Returns 8
```

### Image Processing
```python
thumbnail = create_thumbnail("path/to/image.jpg")
```

### Windows Paint Automation
```python
result = write_to_paint("Hello World", "red")
```

## Requirements

- Python 3.7+
- mcp package
- Pillow (PIL)
- pyautogui
- win32com (for Windows automation)

## Notes

- The server can run in two modes: development mode (`dev`) and standard mode
- Windows-specific features require Windows OS
- Image processing features require the Pillow library
- System automation features require additional Windows-specific packages

## License
NA
