"""LangGraph agent for travel planning."""

from typing import Literal

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import create_agent_nodes
from app.retrieval.embedder import Embedder
from app.retrieval.hybrid import HybridSearcher
from app.retrieval.reranker import Reranker
from app.constraints.validator import ConstraintValidator


class TravelPlannerAgent:
    """LangGraph-based travel planner agent."""

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

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(AgentState)

        # Add nodes
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

        return graph.compile()

    def run(self, user_input: str) -> dict:
        """Run the agent with user input.

        Args:
            user_input: Natural language input like "Tokyo 3 days, 2 people, 500000 yen"

        Returns:
            AgentState with itinerary_result
        """
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

        result = self.graph.invoke(initial_state)
        return result

    async def arun(self, user_input: str) -> dict:
        """Async version of run."""
        import asyncio

        def run_sync():
            return self.run(user_input)

        return await asyncio.to_thread(run_sync)
