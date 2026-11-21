import os
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_URL"),
)
chat_service = OpenAIChatCompletion(
    service_id="chat",
    ai_model_id=os.getenv("GROQ_MODEL"),
    async_client=client,
)

LABEL_PATTERN = re.compile(r"<[A-Z_]+_\d+>")
ANY_ANGLE_PATTERN = re.compile(r"<([A-Z_]+)>")


def build_system_prompt(labels: list) -> str:
    label_list = ", ".join(labels) if labels else "(none)"
    return (
        "You are PrivacyGuard Copilot, an assistant that works on documents "
        "where personal data has already been replaced by numbered placeholders. "
        f"The placeholders in this document are exactly: {label_list}. "
        "Never guess the real values behind them. "
        "RULES: (1) When you mention a person or personal detail from the "
        "document, write the matching placeholder exactly as listed above, "
        "including the angle brackets and the number. For example, address the "
        "customer with their PERSON placeholder. "
        "(2) NEVER invent new angle-bracket placeholders. If you need a detail "
        "that is not in the list, such as the sender's name, company or "
        "contact info, write it in square brackets like [Your name] or "
        "[Company name]. "
        "Use get_document to read the document. Do the task the user asks for "
        "(summaries, replies, priorities, bullet points). Answer clearly and "
        "briefly in plain text."
    )


class DocumentPlugin:
    """Tools the AI can call. They only expose REDACTED data."""

    def __init__(self, redacted_text: str, counts: dict):
        self.redacted_text = redacted_text
        self.counts = counts

    @kernel_function(
        name="get_document",
        description="Returns the privacy-redacted text of the document.",
    )
    def get_document(self) -> str:
        return self.redacted_text

    @kernel_function(
        name="get_redaction_report",
        description="Returns how many items of each personal-data type were redacted.",
    )
    def get_redaction_report(self) -> str:
        if not self.counts:
            return "No personal data was detected."
        return ", ".join(f"{k}: {v}" for k, v in self.counts.items())


def tidy(reply: str, valid_labels: list) -> str:
    """Turn any placeholder the AI invented into a normal [blank]."""
    reply = reply.replace("**", "")

    def fix(match):
        full = match.group(0)
        if full in valid_labels:
            return full
        words = match.group(1).replace("_", " ").lower()
        return f"[{words}]"

    return ANY_ANGLE_PATTERN.sub(fix, reply)


async def ask(redacted_text: str, counts: dict, question: str) -> str:
    labels = sorted(set(LABEL_PATTERN.findall(redacted_text)))

    kernel = Kernel()
    kernel.add_service(chat_service)
    kernel.add_plugin(DocumentPlugin(redacted_text, counts), plugin_name="document")

    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )
    history = ChatHistory(system_message=build_system_prompt(labels))
    history.add_user_message(question)

    reply = await chat_service.get_chat_message_content(
        chat_history=history, settings=settings, kernel=kernel
    )
    return tidy(str(reply), labels)