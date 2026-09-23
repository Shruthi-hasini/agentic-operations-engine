import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import search_return_policy

load_dotenv()

def evaluate_rag_pipeline():
    print("--- RUNNING RAG EVALUATION BENCHMARK ---\n")
    
    # Test cases to benchmark vector retrieval
    test_cases = [
        {
            "query": "What is the return window for a full refund?",
            "expected_fact": "30 days from delivery"
        },
        {
            "query": "What happens if I return an item after 30 days?",
            "expected_fact": "Eligible for store credit only"
        },
        {
            "query": "Are refunds over $50 processed automatically?",
            "expected_fact": "Requires manual authorization from an admin"
        }
    ]
    
    evaluator_llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)
    
    total_faithfulness = 0
    total_precision = 0
    
    for idx, case in enumerate(test_cases, 1):
        query = case["query"]
        expected = case["expected_fact"]
        
        # 1. Execute Retrieval Tool
        retrieved_context = search_return_policy.invoke({"query": query})
        
        # 2. Evaluate Context Precision (Did ChromaDB fetch the right info?)
        eval_prompt = f"""
        Evaluate if the retrieved context contains the information needed to answer the query.
        Query: {query}
        Retrieved Context: {retrieved_context}
        Expected Fact: {expected}
        
        Return ONLY a JSON object with two fields:
        "context_precision_score": (float between 0.0 and 1.0)
        "reason": "short explanation"
        """
        
        eval_response = evaluator_llm.invoke(eval_prompt).content
        
        # Parse text content safely
        if isinstance(eval_response, list):
            eval_text = " ".join([x.get("text", "") for x in eval_response if isinstance(x, dict)])
        else:
            eval_text = str(eval_response)
            
        print(f"Test #{idx}: '{query}'")
        print(f"Context Retrieved: {retrieved_context[:100]}...")
        print(f"Evaluation Output: {eval_text}\n" + "-"*50)

if __name__ == "__main__":
    evaluate_rag_pipeline()