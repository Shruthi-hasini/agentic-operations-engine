# Enterprise Agentic Customer Support & Operations Engine

A production-grade microservice built with **FastAPI**, **LangGraph**, **ChromaDB**, **SQLite**, and **Docker**. 

Features an **Agentic RAG pipeline** with dynamic tool calling, **Corrective RAG (CRAG)** context evaluation, and a **Human-in-the-Loop (HITL)** approval gate for high-risk financial transactions.

---

## 🛠️ System Architecture

```text
               ┌───────────────────────────┐
               │    Incoming User Query    │
               └─────────────┬─────────────┘
                             │
                ┌────────────▼────────────┐
                │  LangGraph Router Node  │
                └─┬─────────────────────┬─┘
                  │                     │
(Policy Question) │                     │ (Order/Refund Query)
                  ▼                     ▼
       ┌──────────────────┐    ┌──────────────────┐
       │ Chroma Vector DB │    │  SQLite Database │
       │  (Policy Docs)   │    │  (Orders Table)  │
       └─────────┬────────┘    └────────┬─────────┘
                 │                      │
                 └──────────┬───────────┘
                            │
               ┌────────────▼────────────┐
               │ Context Evaluator (CRAG)│
               └────────────┬────────────┘
                            │
               ┌────────────▼────────────┐
               │ Refund > $50 Threshold? │
               └─┬─────────────────────┬─┘
                 │ YES                 │ NO
                 ▼                     ▼
      ┌────────────────────┐  ┌──────────────────┐
      │ Pause State (HITL) │  │ Auto-Execute API │
      │ Admin Approval Req │  │   & Respond      │
      └────────────────────┘  └──────────────────┘