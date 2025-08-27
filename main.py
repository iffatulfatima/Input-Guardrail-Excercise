import rich
import asyncio
from connection import config
from pydantic import BaseModel

from agents import (
    Agent, Runner, input_guardrail, GuardrailFunctionOutput, InputGuardrailTripwireTriggered
)

# Output Model for Teacher Agent
class ClassChangeCheck(BaseModel):
    response: str
    isClasstimeChangeRequest: bool 


# Teacher Agent 
teacher_checker_agent = Agent(
    name="Teacher Agent",
    instructions="""
        You are a teacher agent. 
        If the student asks to change the class timings, 
        set isClasstimeChangeRequest to True and politely refuse.
        Otherwise, set it to False and continue teaching.
    """,
    output_type=ClassChangeCheck
)


# Guardrail Function
@input_guardrail
async def class_timing_guardrail(ctx, agent, input):
    result = await Runner.run(teacher_checker_agent, input, run_config=config)

    rich.print("[bold yellow]Teacher's Check Output:[/bold yellow]", result.final_output)

    return GuardrailFunctionOutput(
        output_info=result.final_output.response,
        tripwire_triggered=result.final_output.isClasstimeChangeRequest
    )


# Main Student Agent
student_agent = Agent(
    name='Student Agent',
    instructions="You are a student talking to your teacher.",
    input_guardrails=[class_timing_guardrail]
)


# Main Execution
async def main():
    try:
        # This input should trigger the guardrail
        result = await Runner.run(student_agent, "I want to change my class timings 😭😭", run_config=config)
        print("Message sent to teacher:", result.final_output)

    except InputGuardrailTripwireTriggered:
        print("[red]Request Blocked: Class timing change not allowed.[/red]")
        with open("logs.txt", "a") as log_file:
            log_file.write("Blocked: Attempted to change class timings.\n")


if __name__ == "__main__":
    asyncio.run(main())
