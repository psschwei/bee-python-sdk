"""
Stream assistant events

WARNING: Streaming support is experimental. Some handlers in AssistantEventHandler will not be called as expected
"""

import os
from pprint import pprint

from openai import AssistantEventHandler, OpenAI
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads.runs import RunStep, RunStepDelta, ToolCall


def heading(text: str) -> str:
    """Helper function for centering text."""
    return "\n" + f" {text} ".center(80, "=") + "\n"


client = OpenAI(api_key=os.getenv("BEE_API_KEY"), base_url=f'{os.getenv("BEE_API")}/v1')

print(heading("Create assistant with code_interpreter tool enabled."))
assistant = client.beta.assistants.create(
    model="meta-llama/llama-3-1-70b-instruct", tools=[{"type": "code_interpreter"}]
)
print("Assistant:")
pprint(assistant.model_dump())

print(heading("Run model and get answer"))
thread = client.beta.threads.create(
    messages=[{"role": "user", "content": "Generate first 10 fibonacci numbers using python"}]
)


class EventHandler(AssistantEventHandler):
    """NOTE: Streaming is work in progress, not all methods are implemented"""

    def on_event(self, event: AssistantStreamEvent) -> None:
        print(f"event > {event.event}")

    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_run_step_delta(self, delta: RunStepDelta, snapshot: RunStep) -> None:
        if delta.step_details.type != "tool_calls":
            print(f"{delta.step_details.type} > {getattr(delta.step_details, delta.step_details.type)}")

    def on_tool_call_created(self, tool_call: ToolCall) -> None:
        """Not implemented yet"""

    def on_tool_call_done(self, tool_call: ToolCall) -> None:
        """Not implemented yet"""


with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    event_handler=EventHandler(),
) as stream:
    stream.until_done()

client.beta.assistants.delete(assistant_id=assistant.id)
