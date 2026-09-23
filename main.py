import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables FIRST
load_dotenv()

# Import graph compiled from agent_graph_v2
from agent_graph_v2 import app_graph as graph

app = FastAPI(
    title="Enterprise Agentic Operations Engine",
    description="Production-Grade FastAPI Microservice with Agentic RAG, Tool Calling, and Human-in-the-Loop State Control.",
    version="1.0.0"
)

# ---------------------------------------------------------
# REQUEST / RESPONSE SCHEMAS (Pydantic Validation)
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ApprovalRequest(BaseModel):
    thread_id: str
    admin_approved: bool

# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    """Health check endpoint for container monitoring."""
    return {"status": "healthy", "service": "agentic-operations-engine"}

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main conversation endpoint. Executes state graph and evaluates risk thresholds.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # Run state graph with thread memory
        output_state = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        # Extract variables directly from graph state
        messages = output_state.get("messages", [])
        last_msg = messages[-1].content if messages else "No response generated."
        status = output_state.get("execution_status", "COMPLETED")
        amount = output_state.get("order_amount", 0.0)
        order_id = output_state.get("order_id", "")
        
        # Format response text cleanly based on execution state
        if status == "PAUSED_PENDING_APPROVAL":
            response_text = f"Refund request of ${amount:.2f} for order {order_id} exceeds automatic limit ($50.00). State PAUSED pending Admin approval."
        else:
            response_text = str(last_msg)
            
        return {
            "status": status,
            "thread_id": request.thread_id,
            "order_id": order_id,
            "refund_amount": amount,
            "response": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/approve")
async def admin_approve_endpoint(request: ApprovalRequest):
    """
    Admin approval endpoint. Injects approval into thread memory state to grant or deny paused refund workflows.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        if request.admin_approved:
            # Update state memory key 'admin_approved' to align with AgentState schema
            admin_payload = {
                "admin_approved": True,
                "messages": [SystemMessage(content="Admin authorized refund execution.")]
            }
            graph.update_state(config, admin_payload)
            
            return {
                "status": "APPROVED",
                "thread_id": request.thread_id,
                "message": "Admin authorization injected. State updated successfully. Re-send chat request to resume payout."
            }
        else:
            admin_payload = {
                "admin_approved": False,
                "execution_status": "REJECTED_BY_ADMIN",
                "messages": [SystemMessage(content="Admin rejected refund execution.")]
            }
            graph.update_state(config, admin_payload)
            
            return {
                "status": "REJECTED",
                "thread_id": request.thread_id,
                "message": "Refund request rejected by Admin."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)