from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document

def init_vector_db():
    # Store return & refund policies
    policy_documents = [
        Document(
            page_content="Items can be returned within 30 days of delivery for a full refund. "
                         "Items returned after 30 days are only eligible for store credit.",
            metadata={"category": "return_window"}
        ),
        Document(
            page_content="Refunds exceeding $50 require manual authorization from an admin. "
                         "Automatic refunds are processed instantly for amounts under $50.",
            metadata={"category": "refund_limits"}
        ),
        Document(
            page_content="Damaged or defective items are eligible for free return shipping within 14 days.",
            metadata={"category": "damaged_goods"}
        )
    ]
    
    # FastEmbed Embeddings run locally on CPU (no paid API key needed)
    embeddings = FastEmbedEmbeddings()
    
    # Index documents into persistent ChromaDB
    vectorstore = Chroma.from_documents(
        documents=policy_documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("✅ Vector Database (ChromaDB) successfully initialized with policy documents!")

if __name__ == "__main__":
    init_vector_db()