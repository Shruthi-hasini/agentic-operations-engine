import os
import re
import sqlite3
from typing import TypedDict, Annotated, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

from tools import get_order_details, search_return_policy, execute_refund_payout

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)

# State schema
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    order_id: str
    order_amount: float
    requires_approval: bool
    admin_approved: bool
    execution_status: str
    crag_retry_count: int

def router_node(state: AgentState) -> AgentState:
    """Analyze input message, extract SQL order details dynamically, and route query."""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Extract order ID if present and query SQL DB directly
    match = re.search(r"ORD\d{4}", str(last_message).upper())
    
    order_id = state.get("order_id", "")
    order_amount = state.get("order_amount", 0.0)
    
    if match:
        order_id = match.group(0)
        conn = sqlite3.connect("orders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT price FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            order_amount = float(row[0])
            
    return {
        "order_id": order_id,
        "order_amount": order_amount,
        "requires_approval": order_amount > 50.0,
        "execution_status": "ROUTED"
    }

def crag_evaluator_node(state: AgentState) -> AgentState:
    """Corrective RAG (CRAG) node: Grades retrieval quality and forces query rewriting if irrelevant."""
    messages = state["messages"]
    last_user_msg = [m for m in messages if isinstance(m, HumanMessage)][-1].content
    
    # Perform retrieval
    context = search_return_policy.invoke({"query": str(last_user_msg)})
    
    # Grade context quality
    eval_prompt = f"Does this context contain facts to answer: '{last_user_msg}'?\nContext: {context}\nReply ONLY YES or NO."
    grade = llm.invoke(eval_prompt).content.strip().upper()
    
    retry_count = state.get("crag_retry_count", 0)
    
    if "YES" in grade or retry_count >= 1:
        # Valid retrieval or max retry reached
        response = llm.invoke(f"Answer the query accurately using this context: {context}\nQuery: {last_user_msg}")
        return {
            "messages": [AIMessage(content=str(response.content))],
            "execution_status": "COMPLETED"
        }
    else:
        # Fallback: Rewrite query and retry once
        rewritten_query = f"store return policy for {last_user_msg}"
        fallback_context = search_return_policy.invoke({"query": rewritten_query})
        response = llm.invoke(f"Answer using policy context: {fallback_context}\nQuery: {last_user_msg}")
        return {
            "messages": [AIMessage(content=str(response.content))],
            "crag_retry_count": retry_count + 1,
            "execution_status": "COMPLETED_WITH_FALLBACK"
        }

def hitl_evaluator_node(state: AgentState) -> AgentState:
    """Evaluates financial risk against strict SQL amount, pausing or executing payouts."""
    order_id = state.get("order_id", "")
    amount = state.get("order_amount", 0.0)
    requires_approval = state.get("requires_approval", False)
    admin_approved = state.get("admin_approved", False)
    
    if not order_id:
        return {
            "messages": [AIMessage(content="Please provide a valid Order ID (e.g., ORD1001) to process a refund.")],
            "execution_status": "FAILED_MISSING_ORDER"
        }
        
    # Check threshold ($50)
    if requires_approval and not admin_approved:
        return {
            "messages": [AIMessage(content=f"Refund request of ${amount:.2f} for order {order_id} exceeds automatic limit ($50.00). State PAUSED pending Admin approval.")],
            "execution_status": "PAUSED_PENDING_APPROVAL"
        }
        
    # Execute refund tool directly once authorized
    result = execute_refund_payout.invoke({"order_id": order_id, "amount": amount})
    return {
        "messages": [AIMessage(content=f"Execution Update: {result}")],
        "execution_status": "COMPLETED"
    }

def route_next_step(state: AgentState) -> str:
    messages = state["messages"]
    last_msg = str(messages[-1].content).lower()
    
    if "refund" in last_msg or state.get("order_id"):
        return "hitl_evaluator"
    return "crag_evaluator"

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("router", router_node)
builder.add_node("crag_evaluator", crag_evaluator_node)
builder.add_node("hitl_evaluator", hitl_evaluator_node)

builder.set_entry_point("router")
builder.add_conditional_edges("router", route_next_step)
builder.add_edge("crag_evaluator", END)
builder.add_edge("hitl_evaluator", END)

# Persistent SQLite checkpointer
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(conn)

app_graph = builder.compile(checkpointer=memory)
graph = app_graph