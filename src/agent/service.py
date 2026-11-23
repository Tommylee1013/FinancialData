from __future__ import annotations

import json
import threading
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .config import DEFAULT_CHAT_DB, DEFAULT_FINANCE_DB, agent_model, load_openai_api_key
from .store import ChatStore
from .tools import FinancialTools


INSTRUCTIONS = """You are FinDash Research, a careful financial markets research assistant.
Use the provided read-only database tools whenever the user asks about a measurable market, macro, rate, freight, industry, FX, volatility, or sentiment series.
State the observation date and distinguish database facts from your interpretation. Never invent unavailable values.
Keep answers concise but analytical. Use English unless the user asks for another language.
This is research support, not personalized investment advice."""

AGENT_PROFILES = {
    "risk": ("Risk Management Agent", "Minimize portfolio and market risk. Quantify tail risk, volatility, drawdowns and correlations before offering mitigation ideas.", ["financial", "risk", "allocation"]),
    "portfolio": ("Portfolio Management Agent", "Construct diversified portfolios. Inspect the available asset universe, compare optimization methods and explain weights and risk-return trade-offs.", ["financial", "allocation"]),
    "trader": ("Trader Agent", "Analyze a single instrument for conditional trade setups using trend, momentum, volatility and risk/reward. Never present signals as certainty or execute trades.", ["financial", "risk"]),
    "research": ("Research Agent", "Analyze a single company or instrument using its own price series and relevant peer, index and sector data. Cite observed dates and separate facts from interpretation.", ["financial"]),
    "macro": ("Macro Agent", "Analyze market-wide, economic, industry and sector regimes. Compare related macro, rates, volatility, FX and index series; cite observation dates.", ["financial"]),
    "manager": ("Manager", "Orchestrate the specialist agents. Delegate each distinct question to the most relevant specialist, and call multiple specialists in parallel when the request spans domains. Wait for their results, then synthesize the evidence, dates, disagreements, assumptions, and risks into one balanced answer. Do not imply a specialist was consulted unless its delegation tool returned a result.", ["financial", "risk", "allocation"]),
}


class AgentService:
    def __init__(self, finance_db=DEFAULT_FINANCE_DB, chat_db=DEFAULT_CHAT_DB, allocation_service=None):
        self.store = ChatStore(chat_db)
        self.tools = FinancialTools(finance_db)
        self.allocation = allocation_service
        self.model = agent_model()
        self.api_key = load_openai_api_key()
        self._event_lock = threading.Lock()
        self._event_runs = {}

    def _begin_run(self, run_id, conversation_id):
        if not run_id:
            return
        with self._event_lock:
            while len(self._event_runs) >= 100:
                self._event_runs.pop(next(iter(self._event_runs)))
            self._event_runs[run_id] = {"conversationId": conversation_id, "status": "running", "events": []}
        self._emit_run_event(run_id, "run_started", "manager", "Research run started")

    def _emit_run_event(self, run_id, event_type, agent_id, message, **details):
        if not run_id:
            return
        event = {
            "id": 0,
            "type": event_type,
            "agentId": agent_id,
            "agentName": AGENT_PROFILES.get(agent_id, (agent_id,))[0],
            "message": str(message)[:300],
            "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        event.update({key: value for key, value in details.items() if value is not None})
        with self._event_lock:
            run = self._event_runs.get(run_id)
            if run is None:
                return
            event["id"] = len(run["events"]) + 1
            run["events"].append(event)

    def _finish_run(self, run_id, error=None):
        if not run_id:
            return
        with self._event_lock:
            run = self._event_runs.get(run_id)
            if run is None:
                return
        self._emit_run_event(run_id, "run_failed" if error else "run_completed", "manager",
                             "Run failed" if error else "Final response ready")
        with self._event_lock:
            run = self._event_runs.get(run_id)
            if run is not None:
                run["status"] = "failed" if error else "complete"

    def get_run_events(self, run_id, after=0):
        with self._event_lock:
            run = self._event_runs.get(run_id)
            if run is None:
                return {"events": [], "status": "pending"}
            return {"events": [event for event in run["events"] if event["id"] > after],
                    "status": run["status"]}

    @staticmethod
    def _tool_result_summary(result):
        if isinstance(result, dict):
            symbol = result.get("symbol")
            observations = result.get("observations")
            if isinstance(observations, list):
                span = ""
                if observations:
                    span = f", {observations[0].get('date', '')}–{observations[-1].get('date', '')}"
                return f"{symbol or 'Series'}: {len(observations)} observations{span}"
            if symbol:
                return f"{symbol}: {', '.join(str(key) for key in list(result)[:5])}"
            return ", ".join(str(key) for key in list(result)[:5]) or "Completed"
        if isinstance(result, list):
            return f"{len(result)} records returned"
        return "Completed"

    def _build_graph(self, agent_id, screen_context=None, nested_tool_messages=None, run_id=None):
        def execute_tool(name, arguments, operation):
            args_summary = ", ".join(f"{key}={value}" for key, value in arguments.items())
            self._emit_run_event(run_id, "tool_started", agent_id, f"Running {name}", tool=name, detail=args_summary)
            try:
                result = operation()
            except Exception:
                self._emit_run_event(run_id, "tool_failed", agent_id, f"{name} failed", tool=name)
                raise
            self._emit_run_event(run_id, "tool_completed", agent_id,
                                 f"{name}: {self._tool_result_summary(result)}", tool=name)
            self._emit_run_event(run_id, "evidence_received", agent_id,
                                 "Evidence returned; agent continues its analysis", tool=name)
            return result

        @tool
        def search_instruments(query: str, limit: int = 10):
            """Search FinDash instruments by symbol or name."""
            return execute_tool("search_instruments", {"query": query, "limit": limit},
                                lambda: self.tools.search_instruments(query, limit))

        @tool
        def get_financial_series(symbol: str, limit: int = 240):
            """Read a time series from FinDash DuckDB for a ticker or instrument symbol."""
            return execute_tool("get_financial_series", {"symbol": symbol, "limit": limit},
                                lambda: self.tools.get_financial_series(symbol, limit))

        @tool
        def get_market_snapshot(symbols: list[str]):
            """Compare latest values and changes for several financial instruments."""
            return execute_tool("get_market_snapshot", {"symbols": symbols},
                                lambda: self.tools.get_market_snapshot(symbols))

        @tool
        def quantify_risk(symbol: str, limit: int = 250, confidence: float = 0.95, window: int = 20):
            """Calculate historical volatility, rolling standard deviation, max drawdown and historical VaR/CVaR for an instrument series."""
            return execute_tool("quantify_risk", {"symbol": symbol, "confidence": confidence, "window": window},
                                lambda: self.tools.quantify_risk(symbol, limit, confidence, window))

        profile = AGENT_PROFILES.get(agent_id, AGENT_PROFILES["research"])
        available = set(profile[2])
        selected_tools = [search_instruments, get_financial_series, get_market_snapshot]
        if "risk" in available:
            selected_tools.append(quantify_risk)
        allocation_tools = []
        if self.allocation:
            @tool
            def allocation_universe():
                """List available assets for portfolio allocation, including IDs and asset classes."""
                return execute_tool("allocation_universe", {}, self.allocation.universe)

            @tool
            def optimize_allocation(asset_ids: list[str], method: str = "mvo", lookback_years: int = 5,
                                    objective: str = "max_sharpe", risk_aversion: float = 2.0,
                                    max_weight: float = 1.0, long_only: bool = True):
                """Run FinDash portfolio optimization on selected asset IDs. No trades are placed."""
                payload = {"assetIds": asset_ids, "method": method, "lookbackYears": lookback_years,
                           "riskFreeRate": 3.5, "params": {"objective": objective,
                           "riskAversion": risk_aversion, "maxWeight": max_weight, "longOnly": long_only}}
                return execute_tool("optimize_allocation", {"method": method, "assets": len(asset_ids)},
                                    lambda: self.allocation.optimize(payload))
            allocation_tools = [allocation_universe, optimize_allocation]

        if agent_id == "manager":
            def make_delegate_tool(delegate_id):
                delegate_name = AGENT_PROFILES[delegate_id][0]

                def delegate(task: str):
                    """Run one specialist analysis and return its evidence and conclusion to the Manager."""
                    self._emit_run_event(run_id, "agent_started", delegate_id,
                                         f"Delegated by Manager: {task}", detail=task[:180])
                    specialist = self._build_graph(delegate_id, screen_context, nested_tool_messages, run_id)
                    context_text = ""
                    if screen_context:
                        context_text = "FinDash page context: " + json.dumps(screen_context, default=str) + "\n\n"
                    specialist_prompt = (
                        f"Manager delegation: {task}\n\n"
                        "Return a concise handoff to the Manager: key findings, observed dates and sources, "
                        "interpretation, uncertainty, and any missing data. Do not answer unrelated parts of the request."
                    )
                    try:
                        result = specialist.invoke(
                            {"messages": [
                                SystemMessage(content=(
                                    f"{INSTRUCTIONS}\n\nYou are operating as {delegate_name}. "
                                    f"{AGENT_PROFILES[delegate_id][1]}"
                                )),
                                HumanMessage(content=context_text + specialist_prompt),
                            ]},
                            config={"recursion_limit": 10},
                        )
                    except Exception:
                        self._emit_run_event(run_id, "agent_failed", delegate_id, "Specialist execution failed")
                        raise
                    if nested_tool_messages is not None:
                        nested_tool_messages.extend(
                            item for item in result["messages"]
                            if getattr(item, "type", "") == "tool"
                        )
                    answer = self._visible_text(result["messages"][-1].content)
                    self._emit_run_event(run_id, "agent_completed", delegate_id,
                                         "Specialist findings returned to Manager")
                    self._emit_run_event(run_id, "synthesis_progress", "manager",
                                         f"Manager received {delegate_name} findings and is continuing synthesis")
                    return {"agent": delegate_name, "findings": answer or "No user-facing findings returned."}

                delegate.__name__ = f"delegate_{delegate_id}_agent"
                return tool(
                    f"delegate_{delegate_id}_agent",
                    description=(
                        f"Delegate a focused subtask to the {delegate_name}. The specialist uses its role-specific "
                        "read-only data tools and returns findings for you to synthesize. Use when relevant; "
                        "multiple specialist tools may be called together for cross-domain questions."
                    ),
                )(delegate)

            specialist_tools = [make_delegate_tool(key) for key in ("risk", "portfolio", "trader", "research", "macro")]
            selected_tools.extend(specialist_tools)

        # gpt-6-luna exposes function tools through the Responses API; ChatOpenAI
        # otherwise defaults to /v1/chat/completions.
        llm = ChatOpenAI(model=self.model, api_key=self.api_key, use_responses_api=True)
        return create_react_agent(llm, [*selected_tools, *allocation_tools])

    @staticmethod
    def _visible_text(content):
        """Return only user-facing text blocks; never persist/display reasoning payloads."""
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return ""
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part).strip()

    def status(self):
        return {"configured": bool(self.api_key), "model": self.model,
                "framework": "LangChain + LangGraph", "allocationTools": bool(self.allocation),
                "agents": [{"id": key, "name": value[0], "description": value[1]} for key, value in AGENT_PROFILES.items()],
                "chatDatabase": str(self.store.path), "financeDatabase": self.tools.database_path}

    def create_conversation(self, title="New research", context=None):
        return self.store.create_conversation(title, context)

    def list_conversations(self):
        return self.store.list_conversations()

    def get_conversation(self, conversation_id):
        return self.store.get_conversation(conversation_id, include_messages=True)

    def delete_conversation(self, conversation_id):
        return self.store.delete_conversation(conversation_id)

    def chat(self, conversation_id, message, context=None, agent_id=None, run_id=None):
        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise KeyError("Conversation not found")
        user_message_id = self.store.add_message(conversation_id, "user", message)
        self.store.rename_from_first_message(conversation_id, message)
        agent_id = agent_id or conversation.get("context", {}).get("agentId", "research")
        if agent_id not in AGENT_PROFILES:
            raise ValueError(f"Unknown agent: {agent_id}")
        self._begin_run(run_id, conversation_id)
        screen_context = context or conversation.get("context") or {}
        # Graph tool closures capture this request's page context for delegation.
        nested_tool_messages = []
        self._emit_run_event(run_id, "agent_started", agent_id, f"{AGENT_PROFILES[agent_id][0]} is analyzing the request")
        self._emit_run_event(run_id, "analysis_started", agent_id,
                             "Reviewing the request and selecting relevant data tools")
        try:
            graph = self._build_graph(agent_id, screen_context, nested_tool_messages, run_id)
        except Exception:
            self._emit_run_event(run_id, "agent_failed", agent_id, "Agent setup failed")
            self._finish_run(run_id, error=True)
            raise
        history = []
        for row in conversation["messages"][-20:]:
            if row["role"] == "user": history.append(HumanMessage(content=row["content"]))
            elif row["role"] == "assistant": history.append(AIMessage(content=row["content"]))
        prompt = message
        if screen_context:
            prompt = "FinDash page context (use as the primary data scope when relevant): " + json.dumps(screen_context, default=str) + "\n\nUser request: " + message
        agent_name, agent_instructions, _ = AGENT_PROFILES[agent_id]
        try:
            result = graph.invoke({"messages": [SystemMessage(content=f"{INSTRUCTIONS}\n\nYou are operating as {agent_name}. {agent_instructions}"), *history, HumanMessage(content=prompt)]},
                                       config={"recursion_limit": 12})
        except Exception:
            self._emit_run_event(run_id, "agent_failed", agent_id, "Agent execution failed")
            self._finish_run(run_id, error=True)
            raise
        answer_message = result["messages"][-1]
        answer = self._visible_text(answer_message.content)
        if not answer:
            answer = "The model returned no user-facing text. Please try again."
        tool_messages = [item for item in result["messages"] if getattr(item, "type", "") == "tool"]
        all_tool_messages = [*tool_messages, *nested_tool_messages]
        for item in all_tool_messages:
            self.store.add_tool_call(conversation_id, user_message_id, item.name, {}, item.content)
        assistant_id = self.store.add_message(conversation_id, "assistant", answer)
        self._emit_run_event(run_id, "agent_completed", agent_id, "Answer synthesized and saved")
        self._finish_run(run_id)
        return {"message": {"id": assistant_id, "role": "assistant", "content": answer},
                "conversation": self.get_conversation(conversation_id), "toolCalls": len(all_tool_messages)}
