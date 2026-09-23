# Enterprise Agentic Operations Engine

A stateful customer operations engine built with **LangGraph**, **FastAPI**, and **SQLite**. The system evaluates transactional risk dynamically using relational SQL data, enforces human-in-the-loop (HITL) safety controls for high-value refunds, and maintains state checkpoints on disk.

---

## 🏛 Architecture Overview

```text
                        ┌────────────────────────┐
                        │   Incoming User Chat   │
                        └───────────┬────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   Router Node       │
                         │ (Extract Order ID)  │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
                 ▼                                     ▼
      ┌──────────────────────┐              ┌──────────────────────┐
      │  CRAG Evaluator Node │              │  HITL Evaluator Node │
      │  (Vector Search DB)  │              │  (SQL Price Gate)    │
      └──────────────────────┘              └──────────┬───────────┘
                                                       │
                                            ┌──────────┴──────────┐
                                            │                     │
                                            ▼                     ▼
                                     [Refund <= $50]       [Refund > $50]
                                            │                     │
                                            ▼                     ▼
                                    ┌──────────────┐      ┌──────────────┐
                                    │ Auto-Execute │      │ State PAUSED │
                                    │ Payout Tool  │      │ Admin Approvr│
                                    └──────────────┘      └──────────────┘