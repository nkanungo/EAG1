import os
from dotenv import load_dotenv
import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
import json

# Initialize console
console = Console()

def setup_gemini():
    """Setup Gemini API"""
    try:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        console.print(f"[red]Error setting up Gemini: {e}[/red]")
        return False

def show_reasoning(steps):
    """Show the step-by-step reasoning process"""
    console.print("[blue]Reasoning Steps:[/blue]")
    for i, step in enumerate(steps, 1):
        console.print(Panel(
            f"{step}",
            title=f"Step {i}",
            border_style="cyan"
        ))

def calculate(expression):
    """Calculate the result of an expression"""
    try:
        result = eval(expression)
        console.print(f"[green]Result:[/green] {result}")
        return result
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return None

def verify(expression, expected):
    """Verify if a calculation is correct"""
    try:
        result = eval(expression)
        if abs(result - expected) < 0.0001:  # Allow for floating point imprecision
            console.print(f"[green]✓ Verification successful: {expression} = {expected}[/green]")
            return True
        else:
            console.print(f"[red]✗ Verification failed: {expression} = {result} (expected {expected})[/red]")
            return False
    except Exception as e:
        console.print(f"[red]Error during verification: {str(e)}[/red]")
        return False

def validate_system_prompt(prompt):
    """Validate the system prompt against requirements from prompt_validation.md"""
    validation_results = {
        "explicit_reasoning": any(phrase in prompt.lower() for phrase in [
            "step by step",
            "explain your thinking",
            "think before you answer"
        ]),
        "structured_output": all(format in prompt.lower() for format in [
            "function_call",
            "final_answer"
        ]),
        "tool_separation": all(tool in prompt.lower() for tool in [
            "show_reasoning",
            "calculate",
            "verify"
        ]),
        "conversation_loop": "update" in prompt.lower() or "previous" in prompt.lower(),
        "instructional_framing": "format" in prompt.lower() and "example" in prompt.lower(),
        "internal_self_checks": "verify" in prompt.lower() and "check" in prompt.lower(),
        "reasoning_type_awareness": any(term in prompt.lower() for term in [
            "arithmetic",
            "logic",
            "lookup"
        ]),
        "fallbacks": any(phrase in prompt.lower() for phrase in [
            "if uncertain",
            "if unsure",
            "if fails"
        ]),
        "overall_clarity": "The prompt has good structure but could improve with better error handling and reasoning type awareness."
    }
    
    # Print validation results in JSON format
    console.print("\n[blue]System Prompt Validation Results:[/blue]")
    console.print(json.dumps(validation_results, indent=2))
    
    return all(validation_results.values())

def main():
    try:
        if not setup_gemini():
            return

        console.print(Panel("Mathematical Reasoning Calculator", border_style="cyan"))

        system_prompt = """You are a mathematical reasoning agent that solves problems step by step, explaining your thinking process.
You have access to these tools:
- show_reasoning(steps: list) - Show your step-by-step reasoning process
- calculate(expression: str) - Calculate the result of an expression
- verify(expression: str, expected: float) - Verify if a calculation is correct

First show your reasoning, then calculate and verify each step. If uncertain about a calculation, double-check your work.
For arithmetic problems, use precise calculations. For logic problems, explain your reasoning clearly.
If a verification fails, re-examine the previous steps.

Respond with EXACTLY ONE line in one of these formats:
1. FUNCTION_CALL: function_name|param1|param2|...
2. FINAL_ANSWER: [answer]

Example: For the problem "2 + 2", you might respond:
FUNCTION_CALL: show_reasoning|["Adding two numbers", "2 + 2 = 4"]
FUNCTION_CALL: calculate|"2 + 2"
FUNCTION_CALL: verify|"2 + 2"|4
FINAL_ANSWER: [4]"""

        # Validate system prompt before proceeding
        if not validate_system_prompt(system_prompt):
            console.print("\n[red]System prompt validation failed. Please update the prompt and try again.[/red]")
            return

        problem = "(23 + 8) * (15 - 7)"
        console.print(Panel(f"Problem: {problem}", border_style="cyan"))

        # Initialize conversation
        prompt = f"{system_prompt}\n\nSolve this problem step by step: {problem}"
        conversation_history = []

        # Initialize the model
        model = genai.GenerativeModel('gemini-2.0-flash')

        while True:
            try:
                response = model.generate_content(prompt)
                
                if not response or not response.text:
                    break

                result = response.text.strip()
                print('********', result)
                console.print(f"\n[yellow]Assistant:[/yellow] {result}")

                if result.startswith("FUNCTION_CALL:"):
                    _, function_info = result.split(":", 1)
                    parts = [p.strip() for p in function_info.split("|")]
                    func_name = parts[0]
                    
                    if func_name == "show_reasoning":
                        # Safely parse the list of steps
                        steps_str = parts[1].strip('[]')
                        steps = [step.strip('"') for step in steps_str.split(',')]
                        show_reasoning(steps)
                        prompt += f"\nUser: Next step?"
                        
                    elif func_name == "calculate":
                        expression = parts[1].strip('"')
                        calc_result = calculate(expression)
                        if calc_result is not None:
                            prompt += f"\nUser: Result is {calc_result}. Let's verify this step."
                            conversation_history.append((expression, float(calc_result)))
                            
                    elif func_name == "verify":
                        expression = parts[1].strip('"')
                        expected = float(parts[2])
                        verify(expression, expected)
                        prompt += f"\nUser: Verified. Next step?"
                        
                elif result.startswith("FINAL_ANSWER:"):
                    if conversation_history:
                        final_answer = float(result.split("[")[1].split("]")[0])
                        verify(problem, final_answer)
                    break
                
                prompt += f"\nAssistant: {result}"

            except Exception as e:
                console.print(f"[red]Error during generation: {e}[/red]")
                break

        console.print("\n[green]Calculation completed![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()
