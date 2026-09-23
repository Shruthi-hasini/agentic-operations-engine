import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Import the tools created on Day 2
from tools import get_order_details, search_return_policy

load_dotenv()

# ---------------------------------------------------------
# 1. DEFINE THE GRAPH STATE
# ---------------------------------------------------------
# The State keeps track of all messages exchanged during execution.
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------------------------------------------------
# 2. INITIALIZE LLM AND BIND TOOLS
# ---------------------------------------------------------
tools = [get_order_details, search_return_policy]

# Using Gemini 2.5 Flash as the underlying LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0
)

# Bind tools to the model so it knows what function schemas are available
llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------
# 3. DEFINE NODES
# ---------------------------------------------------------
def agent_node(state: AgentState):
    """
    The main agent node that receives state messages and decides
    whether to answer directly or generate a tool call.
    """
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# ToolNode automatically executes whichever tool the LLM outputs in its tool_calls payload
tool_node = ToolNode(tools=tools)


# ---------------------------------------------------------
# 4. CONSTRUCT THE LANGGRAPH WORKFLOW
# ---------------------------------------------------------
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

# Add Edges
builder.add_edge(START, "agent")

# Conditional Edge: Checks if the LLM outputted a tool call.
# If YES -> goes to "tools" node. If NO -> goes to END node.
builder.add_conditional_edges("agent", tools_condition)

# Loop edge: After a tool executes, send the result back to the agent node to evaluate
builder.add_edge("tools", "agent")

# Compile the Graph
graph = builder.compile()


# ---------------------------------------------------------
# 5. TEST EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\n--- TEST 1: SQL Order Query ---")
    query1 = "What is the status of my order ORD1001?"
    result1 = graph.invoke({"messages": [HumanMessage(content=query1)]})
    print("Agent Final Answer:", result1["messages"][-1].content)

    print("\n--- TEST 2: Policy Query ---")
    query2 = "Can I return an item after 40 days?"
    result2 = graph.invoke({"messages": [HumanMessage(content=query2)]})
    print("Agent Final Answer:", result2["messages"][-1].content)