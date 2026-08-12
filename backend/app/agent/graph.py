"""LangGraph agent for travel planning with Langfuse tracing."""

import logging
from contextlib import contextmanager
from typing import Generator

from langgraph.graph import END, StateGraph

from app.agent.llm import get_langfuse_client
from app.agent.nodes import create_agent_nodes
from app.agent.state import AgentState
from app.config import settings
from app.constraints.validator import ConstraintValidator
from app.retrieval.embedder import Embedder
from app.retrieval.hybrid import HybridSearcher
from app.retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


class TravelPlannerAgent:
    """LangGraph-based travel planner agent with Langfuse tracing."""

    def __init__(
        self,
        embedder: Embedder,
        searcher: HybridSearcher,
        reranker: Reranker,
        validator: ConstraintValidator,
    ):
        self.embedder = embedder
        self.searcher = searcher
        self.reranker = reranker
        self.validator = validator
        self.nodes = create_agent_nodes(embedder, searcher, reranker, validator)
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

    def _get_langfuse(self):
        """Get shared Langfuse client."""
        return get_langfuse_client()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(AgentState)

        # Add nodes (all async now)
        graph.add_node("extract_prefs", self.nodes["extract_prefs"])
        graph.add_node("retrieve_places", self.nodes["retrieve_places"])
        graph.add_node("plan_day", self.nodes["plan_day"])
        graph.add_node("critic", self.nodes["critic"])
        graph.add_node("finalize", self.nodes["finalize"])

        # Define edges
        graph.set_entry_point("extract_prefs")
        graph.add_edge("extract_prefs", "retrieve_places")
        graph.add_edge("retrieve_places", "plan_day")
        graph.add_edge("plan_day", "critic")

        # Loop: critic -> (plan_day or finalize)
        graph.add_conditional_edges(
            "critic",
            self.nodes["should_continue_loop"],
            {
                "plan_day": "plan_day",
                "finalize": "finalize",
            },
        )

        graph.add_edge("finalize", END)

        return graph

    def run(self, user_input: str) -> dict:
        """Run the agent synchronously (uses asyncio under the hood)."""
        import asyncio

        return asyncio.run(self.arun(user_input))

    async def arun(self, user_input: str) -> dict:
        """Run the agent with async/await support for LLM calls."""
        initial_state: AgentState = {
            "user_input": user_input,
            "preferences": None,
            "retrieved_places": [],
            "current_day": 0,
            "day_plans": [],
            "violations": [],
            "iteration": 0,
            "itinerary_result": None,
            "error": None,
        }

        langfuse = self._get_langfuse()

        try:
            if langfuse:
                with langfuse.start_as_current_observation(
                    name="itinerary-generation",
                    input={"user_input": user_input},
                    metadata={"type": "itinerary", "framework": "langgraph"},
                ) as trace:
                    result = await self.compiled_graph.ainvoke(initial_state)

                    # Add metadata to trace
                    if result.get("preferences"):
                        trace.metadata = {
                            "destination": result["preferences"].destination,
                            "days": result["preferences"].days,
                            "people": result["preferences"].people,
                            "budget": result["preferences"].budget,
                            "style": result["preferences"].style,
                        }

                    # Flush to ensure traces are sent
                    langfuse.flush()
                    return result
            else:
                logger.warning("Langfuse not configured - tracing disabled")
                return await self.compiled_graph.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            if langfuse:
                langfuse.flush()
            raise
