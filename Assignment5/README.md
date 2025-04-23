# Mathematical Reasoning Tool

A Python-based calculator that uses Google's Gemini AI to perform mathematical calculations with step-by-step reasoning and verification.

## Features

- 🤖 AI-powered mathematical reasoning using Google's Gemini
- 📝 Step-by-step problem solving with verification
- 🔍 Built-in validation of system prompts
- 🎨 Rich console output with color-coded results
- 🔄 Interactive conversation flow
- ✅ Automatic verification of calculations

## Prerequisites

- Python 3.7+
- Google Gemini API key
- Required Python packages:
  - google-generativeai
  - rich
  - dotenv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chain-of-thought-calculator
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```

## Usage

1. Run the calculator:
```bash
python agent_main.py
```

2. Enter mathematical expressions when prompted. The calculator will:
   - Show step-by-step reasoning
   - Perform calculations
   - Verify results
   - Provide final answers

## System Prompt Validation

The calculator includes a built-in validation system that checks the system prompt against these criteria:

1. ✅ Explicit Reasoning Instructions
2. ✅ Structured Output Format
3. ✅ Separation of Reasoning and Tools
4. ✅ Conversation Loop Support
5. ✅ Instructional Framing
6. ✅ Internal Self-Checks
7. ✅ Reasoning Type Awareness
8. ✅ Error Handling or Fallbacks
9. ✅ Overall Clarity and Robustness

## Example Usage

```
Enter a mathematical expression (or 'quit' to exit): 2 + 2 * 3

[Step 1] Reasoning: First multiply 2 * 3, then add 2
[Step 2] Calculation: 2 * 3 = 6
[Step 3] Verification: 2 * 3 = 6 ✓
[Step 4] Calculation: 2 + 6 = 8
[Step 5] Verification: 2 + 6 = 8 ✓
Final Answer: 8
```

## Project Structure

```
chain-of-thought-calculator/
├── agent_main.py          # Main calculator application
├── prompt_validation.md   # Prompt validation criteria
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
└── README.md            # This file
```

## Error Handling

The calculator includes several error handling mechanisms:
- Invalid mathematical expressions
- API connection issues
- Calculation verification failures
- System prompt validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI
- Rich Python library
- Python-dotenv 