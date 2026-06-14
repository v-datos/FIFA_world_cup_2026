# Architecture Blueprint & Technology Integration

## 1. Stack Allocation
* **Frontend Framework:** Streamlit (Python) running custom CSS injection layers (`unsafe_allow_html=True`) to alter standard component models into specific layouts.
* **Data Warehouse:** Google Cloud BigQuery (processing StatsBomb schema event streams).
* **Orchestration & Automation:** Google Antigravity Python SDK (running asynchronous background background loops to handle data scraping and BigQuery metric updates).
* **NLP Processing Hub:** Google AI Studio (Prototyping and serving the core text-distillation prompts).

## 2. Component Blueprint