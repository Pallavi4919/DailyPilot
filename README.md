# DailyPilot – Your AI Copilot for Everyday Life

DailyPilot is a production-ready, multi-agent AI assistant designed to streamline your daily expenses, tasks, and deadlines. Built using **Python**, **Streamlit**, the **Google Agent Development Kit (ADK)**, and a custom **Model Context Protocol (MCP) Server**, DailyPilot allows users to manage their lives using natural language.

---

## 🚀 Key Google x Kaggle Concepts Demonstrated

### 1. Google ADK Multi-Agent System
DailyPilot implements a hierarchical multi-agent coordination system:
*   **Orchestrator Agent**: Processes composite natural language inputs (e.g. *"Spent ₹500 on groceries, book train tickets, Kaggle deadline tomorrow"*), breaks them down, and routes tasks to the specialist sub-agents.
*   **Finance Agent**: Focuses on parsing, validating, and recording financial expenses.
*   **Task Agent**: Focuses on parsing, validating, and creating to-do items.
*   **Reminder Agent**: Extracts deadline details, parses relative dates, and logs deadlines.
*   **Daily Coach Agent**: Aggregates all pending items and spending history to produce a motivating morning briefing.

### 2. Model Context Protocol (MCP) Server
An MCP Server is implemented in `mcp_server.py` using the high-level `fastmcp` SDK. It exposes:
*   `add_expense` tool: Atomically logs expenses in SQLite database.
*   `add_task` tool: Atomically inserts tasks in SQLite database.

Our agents communicate with this server using the **MCP Stdio Transport** client, starting the server dynamically as a child subprocess without needing a separate port/host configuration.

### 3. Agent Tool Calling
Specialist agents are equipped with capabilities through **Function Calling**:
*   The Finance Agent maps its findings to the `add_expense_tool` (which calls the MCP Server).
*   The Task Agent maps tasks to the `add_task_tool` (which calls the MCP Server).
*   The Reminder Agent maps deadlines to the `add_deadline_tool` (local SQLite wrapper).
*   The Orchestrator Agent routes text segments using delegation tools (`delegate_expense`, `delegate_task`, `delegate_deadline`).

### 4. Security & Robustness
*   **Safe Environment**: Credentials are kept out of source code by utilizing a `.env` file loaded via `python-dotenv`.
*   **Input Validation**: Numerical values are verified to be positive, string fields are stripped and verified non-empty, and date formatting is standardized.
*   **SQL Injection Prevention**: All SQLite queries use parameterized SQL inputs (`?` placeholders) to prevent SQL injection vulnerabilities.
*   **API Key Fallback UI**: If no API key is found in the `.env` file, the UI provides a fallback input block in the sidebar so you can input it securely for that session.

---

## 📁 Project Structure

```text
CapestoneProjectKagg/
├── .env.example          # Template for environment configuration
├── .env                  # Environment file (ignored in git, created for local use)
├── requirements.txt      # Python dependencies
├── db.py                 # SQLite helper functions & schema setup
├── mcp_server.py         # FastMCP Server exposing tools
├── agents.py             # Google ADK agent configurations and delegation logic
├── app.py                # Streamlit Multi-Page Web Interface
└── README.md             # Project documentation (this file)
```

---

## 🛠️ Setup & Installation

### 1. Clone & Navigate
Navigate to your project directory:
```bash
cd CapestoneProjectKagg
```

### 2. Install Dependencies
Make sure you have Python 3.10+ installed. Install the required libraries:
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` and paste your Google Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
   *(Alternatively, you can launch the app and paste the API key directly in the sidebar textbox!)*

---

## 🎮 How to Run

Start the Streamlit application:
```bash
streamlit run app.py
```

This will automatically:
1. Initialize the SQLite database `dailypilot.db`.
2. Launch the Streamlit dashboard on your local browser (usually `http://localhost:8501`).
3. Connect to the MCP Server background subprocess when natural language requests are submitted.

---

## 💡 How to Test the Multi-Agent System

1.  Navigate to the **AI Inbox** page in the Streamlit Sidebar.
2.  Input a natural language request, for example:
    > *"Spent ₹800 on dinner, prepare presentation slides, Kaggle submission on 2026-07-15"*
3.  Click **Process with DailyPilot**.
4.  Observe the Orchestrator Agent calling the specialist agents (Finance, Task, Reminder) and returning a clean consolidation log.
5.  Go to the **Dashboard**, **Finance Tracker**, and **Tasks Manager** pages to verify that the entries are recorded, totals are calculated, and lists are populated in real-time.
