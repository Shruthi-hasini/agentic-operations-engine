import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

# Import graph compiled with memory from Day 4
from agent_graph_v2 import graph

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
    Primary chat endpoint. Executes the agent graph for a given thread_id session.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # Run graph execution asynchronously
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]}, 
            config=config
        )
        
        # Check if Human-in-the-Loop (HITL) pause was triggered
        requires_approval = result.get("requires_approval", False)
        approval_granted = result.get("approval_granted", False)
        refund_amount = result.get("refund_amount", 0.0)
        
        if requires_approval and not approval_granted:
            return {
                "status": "PAUSED_PENDING_APPROVAL",
                "thread_id": request.thread_id,
                "refund_amount": refund_amount,
                "response": f"Your refund request of ${refund_amount} exceeds automatic limits ($50) "
                            f"and has been submitted for Admin approval."
            }
            
        # Get final response message from LLM
        last_message = result["messages"][-1].content
        if isinstance(last_message, list):
            final_text = " ".join([x.get("text", "") for x in last_message if isinstance(x, dict)])
        else:
            final_text = str(last_message)

        return {
            "status": "COMPLETED",
            "thread_id": request.thread_id,
            "response": final_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admin/approve")
async def admin_approve_endpoint(request: ApprovalRequest):
    """
    Admin approval endpoint. Updates graph state memory to grant or deny paused refund workflows.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    if request.admin_approved:
        admin_payload = {
            "approval_granted": True,
            "messages": [SystemMessage(content="Admin authorized refund execution.")]
        }
        # Inject approval into graph state memory
        graph.update_state(config, admin_payload)
        
        return {
            "status": "APPROVED",
            "thread_id": request.thread_id,
            "message": "Admin authorization injected. Execution state updated successfully."
        }
    else:
        return {
            "status": "REJECTED",
            "thread_id": request.thread_id,
            "message": "Refund request rejected by Admin."
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)