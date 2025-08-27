import rich
import asyncio
from connection import config
from pydantic import BaseModel

from agents import (
    Agent,
    Runner,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered
)

# Output Model 
class TemperatureCheck(BaseModel):
    response: str
    isBelow26: bool 


# Father Checker Agent 
father_checker_agent = Agent(
    name="Father Checker",
    instructions="""
        You are a strict father. 
        If the child sets AC temperature below 26°C, 
        set isBelow26 to True and in response scold the child.
        Otherwise set isBelow26 to False and approve it.
    """,
    output_type=TemperatureCheck
)


# Input Guardrail Function 
@input_guardrail
async def father_guardrail(ctx, agent, input_text):
    result = await Runner.run(father_checker_agent, input_text, run_config=config)


    rich.print("[bold yellow]Father Check Output:[/bold yellow]", result.final_output)

    return GuardrailFunctionOutput(
        output_info=result.final_output.response,
        tripwire_triggered=result.final_output.isBelow26
    )


# Child Agent
child_agent = Agent(
    name='Child Agent',
    instructions="You are a child trying to set the AC temperature.",
    input_guardrails=[father_guardrail]
)


#  Main Function
async def main():
    try:
        # Yeh input guardrail trigger karega (20°C < 26°C)
        result = await Runner.run(child_agent, "AC temperature is 26°C", run_config=config)
        print("Child successfully set AC temperature:", result.final_output)

    except InputGuardrailTripwireTriggered:
        print("Father says: Stop! Temperature below 26°C is not allowed.")
        with open("logs.txt", "a") as log_file:
            log_file.write("Blocked by Father: Temperature below 26°C.\n")


if __name__ == "__main__":
    asyncio.run(main())
