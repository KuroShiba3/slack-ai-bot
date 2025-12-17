from langgraph.graph import START, StateGraph

from ...state.state import BaseState
from .nodes import decide_response_method, generate_direct_answer, generate_final_answer, plan_tasks

supervisor_graph = StateGraph(BaseState)
supervisor_graph.add_node(decide_response_method)
supervisor_graph.add_node(generate_direct_answer)
supervisor_graph.add_node(plan_tasks)
supervisor_graph.add_node(generate_final_answer)
supervisor_graph.add_edge(START, "decide_response_method")