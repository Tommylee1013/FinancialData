from __future__ import annotations

import json

from openai import OpenAI

from .config import DEFAULT_CHAT_DB, DEFAULT_FINANCE_DB, agent_model, load_openai_api_key
from .store import ChatStore
from .tools import FinancialTools, TOOL_DEFINITIONS


INSTRUCTIONS = """You are FinDash Research, a careful financial markets research assistant.
Use the provided read-only database tools whenever the user asks about a measurable market, macro, rate, freight, industry, FX, volatility, or sentiment series.
State the observation date and distinguish database facts from your interpretation. Never invent unavailable values.
Keep answers concise but analytical. Use English unless the user asks for another language.
This is research support, not personalized investment advice."""


class AgentService:
    def __init__(self, finance_db=DEFAULT_FINANCE_DB, chat_db=DEFAULT_CHAT_DB):
        self.store = ChatStore(chat_db)
        self.tools = FinancialTools(finance_db)
        self.model = agent_model()
        self.api_key = load_openai_api_key()

    def status(self):
        return {"configured": bool(self.api_key), "model": self.model,
                "chatDatabase": str(self.store.path), "financeDatabase": self.tools.database_path}

    def create_conversation(self, title="New research", context=None):
        return self.store.create_conversation(title, context)

    def list_conversations(self):
        return self.store.list_conversations()

    def get_conversation(self, conversation_id):
        return self.store.get_conversation(conversation_id, include_messages=True)

    def delete_conversation(self, conversation_id):
        return self.store.delete_conversation(conversation_id)

    def chat(self, conversation_id, message, context=None):
        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise KeyError("Conversation not found")
        user_message_id = self.store.add_message(conversation_id, "user", message)
        self.store.rename_from_first_message(conversation_id, message)
        history = [{"role": row["role"], "content": row["content"]} for row in conversation["messages"][-20:]]
        if context:
            history.append({"role": "system", "content": "Current FinDash screen context: " + json.dumps(context, default=str)})
        history.append({"role": "user", "content": message})
        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(model=self.model, instructions=INSTRUCTIONS, input=history, tools=TOOL_DEFINITIONS)
        tool_count = 0
        while tool_count < 8:
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                break
            tool_outputs = []
            for call in calls:
                arguments = json.loads(call.arguments or "{}")
                result = self.tools.execute(call.name, arguments)
                self.store.add_tool_call(conversation_id, user_message_id, call.name, arguments, result)
                tool_outputs.append({"type": "function_call_output", "call_id": call.call_id,
                                     "output": json.dumps(result, default=str)})
                tool_count += 1
            response = client.responses.create(model=self.model, instructions=INSTRUCTIONS,
                                               previous_response_id=response.id, input=tool_outputs, tools=TOOL_DEFINITIONS)
        answer = response.output_text or "No text response was generated."
        usage = getattr(response, "usage", None)
        assistant_id = self.store.add_message(conversation_id, "assistant", answer, response_id=response.id,
                                              input_tokens=getattr(usage, "input_tokens", None),
                                              output_tokens=getattr(usage, "output_tokens", None))
        return {"message": {"id": assistant_id, "role": "assistant", "content": answer},
                "conversation": self.get_conversation(conversation_id), "toolCalls": tool_count}
