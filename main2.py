import asyncio
from pydantic import BaseModel
import rich
from connection import config

from agents import (
    Agent,
    Runner,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered
)

# ---------------- Output Model ----------------
class GateCheck(BaseModel):
    response: str
    isOtherInstitute: bool  # True agar student GIAIC ka nahi hai


# ---------------- Gate Keeper Checker Agent ----------------
gate_checker_agent = Agent(
    name="Gate Keeper Checker",
    instructions="""
        You are a gate keeper. 
        If the student does NOT have a GIAIC card, 
        set isOtherInstitute to True and deny entry with a warning message.
        If they have a GIAIC card, set isOtherInstitute to False and allow them to enter.
    """,
    output_type=GateCheck
)


# ---------------- Input Guardrail Function ----------------
@input_guardrail
async def gatekeeper_guardrail(ctx, agent, input_text):
    # Gate checker agent ko run karo
    result = await Runner.run(gate_checker_agent, input_text, run_config=config)

    # Debug print
    rich.print("[bold yellow]Gate Keeper Check Output:[/bold yellow]", result.final_output)

    # Guardrail decision
    return GuardrailFunctionOutput(
        output_info=result.final_output.response,
        tripwire_triggered=result.final_output.isOtherInstitute
    )


# ---------------- Student Agent ----------------
student_agent = Agent(
    name='Student Agent',
    instructions="You are a student trying to enter the GIAIC.",
    input_guardrails=[gatekeeper_guardrail]
)


# ---------------- Main Function ----------------
async def main():
    try:
        # Test case: Student without GIAIC card
        result = await Runner.run(student_agent, "I am from Aptech and I don't have a GIAIC card", run_config=config)
        print("Student entered:", result.final_output)

    except InputGuardrailTripwireTriggered:
        print("Gate Keeper: Stop! You are not from GIAIC, entry denied.")
        with open("logs.txt", "a") as log_file:
            log_file.write("Blocked at Gate: Student from another institute.\n")


if __name__ == "__main__":
    asyncio.run(main())
