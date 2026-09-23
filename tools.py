import sqlite3
from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# ---------------------------------------------------------
# TOOL 1: Relational Database Lookup (SQL Tool)
# ---------------------------------------------------------
@tool
def get_order_details(order_id: str) -> str:
    """
    Use this tool to look up specific customer order details such as status, 
    amount, item name, or delivery date using an Order ID (e.g., 'ORD1001').
    """
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id.upper(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return (f"Order ID: {row[0]} | Customer: {row[1]} | Item: {row[2]} | "
                f"Amount: ${row[3]} | Status: {row[4]} | Delivery Date: {row[5]}")
    else:
        return f"Error: No order found with ID {order_id}."


# ---------------------------------------------------------
# TOOL 2: Vector Search Lookup (ChromaDB Tool)
# ---------------------------------------------------------
@tool
def search_return_policy(query: str) -> str:
    """
    Use this tool to search store policies regarding returns, refund rules, 
    timelines, store credits, and damaged goods guidelines.
    """
    embeddings = FastEmbedEmbeddings()
    vectorstore = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings
    )
    
    # Retrieve top 2 most relevant policy chunks
    docs = vectorstore.similarity_search(query, k=2)
    
    if not docs:
        return "No relevant policy information found."
        
    results = "\n\n".join([f"Policy Excerpt: {doc.page_content}" for doc in docs])
    return results


# ---------------------------------------------------------
# Test execution when running tools.py directly
# ---------------------------------------------------------
if __name__ == "__main__":
    print("--- Testing Tool 1: SQL Order Lookup ---")
    print(get_order_details.invoke({"order_id": "ORD1001"}))
    
    print("\n--- Testing Tool 2: Policy Vector Search ---")
    print(search_return_policy.invoke({"query": "What is the refund rule for items over $50?"}))