import sqlite3
import uuid
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DB_PATH = "orders.db"

@tool
def get_order_details(order_id: str) -> str:
    """Fetch order status, total price, and item details from the relational SQL database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT order_id, customer_name, item, price, status FROM orders WHERE order_id = ?", (order_id.upper(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return f"Order {row[0]}: Customer '{row[1]}', Item '{row[2]}', Price ${row[3]:.2f}, Status '{row[4]}'."
    return f"Error: Order ID {order_id} not found in the database."

@tool
def search_return_policy(query: str) -> str:
    """Search vector DB for return guidelines and refund rules."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    docs = vectorstore.similarity_search(query, k=2)
    if docs:
        return "\n\n".join([f"Policy Excerpt: {d.page_content}" for d in docs])
    return "No relevant store policy found."

@tool
def execute_refund_payout(order_id: str, amount: float, idempotency_key: str = None) -> str:
    """Execute payout action, mark order as REFUNDED in SQL DB, and prevent duplicate payouts."""
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Idempotency & DB Verification
    cursor.execute("SELECT price, status FROM orders WHERE order_id = ?", (order_id.upper(),))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return f"EXECUTION_FAILED: Order {order_id} does not exist."
        
    actual_price, current_status = row[0], row[1]
    
    if current_status == 'REFUNDED':
        conn.close()
        return f"EXECUTION_BLOCKED: Order {order_id} has ALREADY been refunded. Duplicate payout prevented."
        
    if abs(amount - actual_price) > 0.01:
        conn.close()
        return f"EXECUTION_REJECTED: Requested refund (${amount:.2f}) does not match order record price (${actual_price:.2f})."
        
    # 2. Perform Transaction
    cursor.execute("UPDATE orders SET status = 'REFUNDED' WHERE order_id = ?", (order_id.upper(),))
    conn.commit()
    conn.close()
    
    return f"SUCCESS: Refund of ${actual_price:.2f} processed for order {order_id}. Idempotency Key: {idempotency_key}."