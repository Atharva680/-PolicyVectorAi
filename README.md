# Scalable AI-Powered Document Query Engine

## 📌 Project Overview
An enterprise-grade retrieval system designed to handle high-volume document queries (100k+ daily) while maintaining strict cost controls and operational reliability. The project focused on transitioning from a manual, high-cost prototype to a production-ready automated platform.

## 🛠 Tech Stack
*   **Backend:** Python (FastAPI/Flask), Pydantic
*   **Database:** PostgreSQL (pgvector for embeddings)
*   **AI/LLM:** LLM-based tool-calling, Custom Chunking Pipelines
*   **Observability:** Structured Logging (JSON), Latency Monitoring, Token Usage Tracking
*   **Integration:** REST APIs, Background Workers (Celery/RQ)

---

## 🚀 The Engineering Challenge
The existing system faced three critical bottlenecks:
1.  **Scalability:** The infrastructure was not equipped for 100,000+ daily requests, leading to intermittent timeouts and "blind spots" in error tracking.
2.  **Cost Leakage:** API expenditures were scaling linearly with usage due to inefficient prompt construction and redundant data retrieval.
3.  **Operational Debt:** 15+ core business workflows (classification and reporting) were being handled manually by staff, costing hundreds of hours annually.

---

## 💡 The Solution

### 1. Infrastructure & Observability
To support enterprise-grade traffic, I implemented a robust observability layer:
*   **Structured Logging:** Moved from plain-text logs to structured JSON logging, allowing for rapid querying of errors via log aggregators.
*   **Latency Monitoring:** Integrated middleware to track request-response cycles, identifying specific API endpoints causing bottlenecks.
*   **Error Handling:** Implemented a comprehensive retry logic with exponential backoff to handle LLM rate limits and transient network failures.

### 2. Cost & Performance Optimization
I reduced API operating costs by **25%** through a targeted optimization strategy:
*   **Query Pattern Analysis:** Analyzed production logs to identify "expensive" query patterns and redundant token usage.
*   **Pipeline Refactor:** Rewrote the chunking and indexing logic to improve the precision of retrieved context, reducing the number of tokens sent to the LLM per query.
*   **Database Tuning:** Optimized PostgreSQL execution plans and indexing to reduce retrieval latency and backend CPU load.

### 3. Agentic Automation Layer
I eliminated **260+ hours** of manual labor by building a dynamic automation framework:
*   **Dynamic Tool-Calling:** Developed a Python-based agentic layer that allows the LLM to autonomously call internal REST APIs based on the user's intent.
*   **Workflow Digitization:** Replaced 15+ manual reporting and classification tasks with automated background scripts that perform extraction and reporting without human intervention.

---

## 📈 Final Impact
| Metric | Before | After | Improvement |
| :--- | :--- | :--- | :--- |
| **Daily Query Capacity** | Unstable | 100,000+ | $\uparrow$ Scalability |
| **API Operating Cost** | Baseline | -25% | $\downarrow$ Expenditure |
| **Manual Effort** | 260+ hrs/year | $\approx 0$ hrs | $\uparrow$ Productivity |
| **Observability** | Reactive | Proactive | $\uparrow$ Reliability |
