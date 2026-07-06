import os
import sys
import uuid
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Ensure the current directory is in the import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db

# Load environment variables
load_dotenv()

# MCP stdio client parameters
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")
server_params = StdioServerParameters(
    command="python",
    args=[MCP_SERVER_PATH],
)

# --- Define Sub-agent Tools ---

async def add_expense_tool(amount: float, category: str, description: str) -> str:
    """Add a new expense record using the MCP server.
    
    Args:
        amount: The monetary value of the expense (must be greater than 0, e.g. 500.0).
        category: The category of the expense (e.g. food, groceries, travel, shopping, rent, Kaggle).
        description: A brief explanation of the expense (e.g. 'groceries from supermarket').
    """
    if amount <= 0:
        return "Error: Expense amount must be greater than zero."
    if not category or not category.strip():
        return "Error: Category cannot be empty."
    if not description or not description.strip():
        return "Error: Description cannot be empty."

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "add_expense",
                    arguments={
                        "amount": float(amount),
                        "category": str(category),
                        "description": str(description)
                    }
                )
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                return str(result)
    except Exception as e:
        return f"Error calling MCP Expense Tool: {str(e)}"

async def add_task_tool(title: str, description: str = "", due_date: str = None) -> str:
    """Add a new task to the task list using the MCP server.
    
    Args:
        title: The name/summary of the task (e.g. 'book train tickets'). Must not be empty.
        description: Optional details or actions required for the task.
        due_date: Optional due date in YYYY-MM-DD format. Defaults to today's date.
    """
    if not title or not title.strip():
        return "Error: Task title cannot be empty."

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "add_task",
                    arguments={
                        "title": str(title),
                        "description": str(description) if description else "",
                        "due_date": str(due_date) if due_date else None
                    }
                )
                if hasattr(result, "content") and result.content:
                    return result.content[0].text
                return str(result)
    except Exception as e:
        return f"Error calling MCP Task Tool: {str(e)}"

async def add_deadline_tool(title: str, due_date: str) -> str:
    """Add a new deadline to track in the system.
    
    Args:
        title: The name/details of the deadline (e.g. 'Kaggle deadline'). Must not be empty.
        due_date: The deadline date in YYYY-MM-DD format (must not be empty).
    """
    if not title or not title.strip():
        return "Error: Deadline title cannot be empty."
    if not due_date or not due_date.strip():
        return "Error: Deadline due date cannot be empty."

    try:
        # Reminder Agent directly uses db layer (or standard python functions) as requested
        return db.add_deadline_db(title, due_date)
    except Exception as e:
        return f"Error adding deadline: {str(e)}"

# --- Define Sub-agent Helper Executors ---

async def run_finance_agent(text: str) -> str:
    """Execute the Finance Agent to extract and log an expense."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    agent = Agent(
        name="finance_agent",
        model=model_name,
        instruction=(
            "You are the Finance Agent for DailyPilot. Your job is to extract details "
            "for an expense (amount, category, description) from the input text and save "
            "it using the 'add_expense_tool'. Be precise. If amount or description are missing, "
            "ask for clarification or report what was missing."
        ),
        tools=[add_expense_tool]
    )
    runner = InMemoryRunner(agent=agent)
    session_id = f"finance-{uuid.uuid4()}"
    runner.session_service.create_session_sync(app_name=runner.app_name, user_id="user", session_id=session_id)
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
    response_text = ""
    async for event in runner.run_async(new_message=content, user_id="user", session_id=session_id):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
    return response_text or "Finance Agent completed execution."

async def run_task_agent(text: str) -> str:
    """Execute the Task Agent to extract and log a task."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    agent = Agent(
        name="task_agent",
        model=model_name,
        instruction=(
            "You are the Task Agent for DailyPilot. Your job is to extract task details "
            "(title, description, due date) from the input text and save it using the 'add_task_tool'. "
            "If a due date is specified (e.g. 'tomorrow', 'next Monday', or a date like YYYY-MM-DD), "
            "format it as YYYY-MM-DD. If no due date is provided, do not pass it (defaulting to today). "
            "Be concise."
        ),
        tools=[add_task_tool]
    )
    runner = InMemoryRunner(agent=agent)
    session_id = f"task-{uuid.uuid4()}"
    runner.session_service.create_session_sync(app_name=runner.app_name, user_id="user", session_id=session_id)
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
    response_text = ""
    async for event in runner.run_async(new_message=content, user_id="user", session_id=session_id):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
    return response_text or "Task Agent completed execution."

async def run_reminder_agent(text: str) -> str:
    """Execute the Reminder Agent to extract and log a deadline."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    agent = Agent(
        name="reminder_agent",
        model=model_name,
        instruction=(
            "You are the Reminder Agent for DailyPilot. Your job is to extract deadline details "
            "(title, due_date) from the input text and save it using the 'add_deadline_tool'. "
            "Calculate or parse the due_date relative to today. The current date is provided in "
            "the system prompt. Format due_date strictly as YYYY-MM-DD. "
            "Note: today's date context is critical for tomorrow/next week parsing."
        ),
        tools=[add_deadline_tool]
    )
    runner = InMemoryRunner(agent=agent)
    session_id = f"reminder-{uuid.uuid4()}"
    runner.session_service.create_session_sync(app_name=runner.app_name, user_id="user", session_id=session_id)
    
    # Inject current date context
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    enriched_text = f"Today's date is {today}. Input: {text}"
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=enriched_text)])
    response_text = ""
    async for event in runner.run_async(new_message=content, user_id="user", session_id=session_id):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
    return response_text or "Reminder Agent completed execution."

# --- Define Orchestrator Agent Tools ---

async def delegate_expense(expense_info: str) -> str:
    """Delegate expense log request to the Finance Agent.
    
    Args:
        expense_info: Natural language text details describing the expense.
    """
    return await run_finance_agent(expense_info)

async def delegate_task(task_info: str) -> str:
    """Delegate task creation request to the Task Agent.
    
    Args:
        task_info: Natural language text details describing the task.
    """
    return await run_task_agent(task_info)

async def delegate_deadline(deadline_info: str) -> str:
    """Delegate deadline creation request to the Reminder Agent.
    
    Args:
        deadline_info: Natural language text details describing the deadline.
    """
    return await run_reminder_agent(deadline_info)

# --- Define Main Orchestrator Execution ---

async def run_orchestrator(prompt: str) -> str:
    """Run the main Orchestrator Agent which breaks down the input and routes to sub-agents."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Instantiate the Orchestrator
    orchestrator = Agent(
        name="orchestrator_agent",
        model=model_name,
        instruction=(
            "You are the Orchestrator Agent for DailyPilot. Your task is to process natural language "
            "input from the user's daily life, which can be a composite message containing multiple items. "
            "For example: 'Spent ₹500 on groceries, book train tickets, Kaggle deadline tomorrow.'\n\n"
            "You must:\n"
            "1. Analyze the user's prompt and extract distinct items.\n"
            "2. Identify each item as an Expense, Task, or Deadline.\n"
            "3. Delegate each identified item to its respective specialist tool:\n"
            "   - Use 'delegate_expense' for expenses.\n"
            "   - Use 'delegate_task' for tasks.\n"
            "   - Use 'delegate_deadline' for deadlines/reminders.\n"
            "4. Combine the results of all delegations into a single, clean, structured response for the user, "
            "summarizing what was logged (e.g. Expense, Task, Deadline details) and confirm success."
        ),
        tools=[delegate_expense, delegate_task, delegate_deadline]
    )
    
    runner = InMemoryRunner(agent=orchestrator)
    session_id = f"orchestrator-{uuid.uuid4()}"
    runner.session_service.create_session_sync(app_name=runner.app_name, user_id="user", session_id=session_id)
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    response_text = ""
    
    async for event in runner.run_async(new_message=content, user_id="user", session_id=session_id):
        # We can print event content or capture tool calls for diagnostics
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            
    return response_text or "DailyPilot processed your request."

# --- Daily Coach Generator ---

async def generate_daily_coach_summary() -> str:
    """Generate a daily priority summary using SQLite records and a Gemini model call directly."""
    # Retrieve current data
    expenses = db.get_all_expenses()
    tasks = [t for t in db.get_all_tasks() if t['status'] == 'pending']
    deadlines = [d for d in db.get_all_deadlines() if d['status'] == 'pending']
    monthly_total = db.get_monthly_total()
    
    # Format the data into context
    context = f"DailyPilot Data Context:\n"
    context += f"- Monthly Expenses Total: ₹{monthly_total:.2f}\n"
    context += f"- Pending Tasks ({len(tasks)}):\n"
    for t in tasks[:5]:
        context += f"  * {t['title']} (Due: {t['due_date']})\n"
    context += f"- Upcoming Deadlines ({len(deadlines)}):\n"
    for d in deadlines[:5]:
        context += f"  * {d['title']} (Due: {d['due_date']})\n"
        
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # We can instantiate a simple coach agent to summarize the priorities
    coach = Agent(
        name="daily_coach_agent",
        model=model_name,
        instruction=(
            "You are the Daily Coach for DailyPilot. Analyze the user's current expenses, "
            "pending tasks, and upcoming deadlines. Generate a short, motivating, and highly structured "
            "summary of their day. Provide 2-3 specific priorities for today (prioritizing immediate "
            "deadlines or tasks) and a brief tip on budget if their expenses are high. Keep it professional "
            "yet friendly."
        )
    )
    
    runner = InMemoryRunner(agent=coach)
    session_id = f"coach-{uuid.uuid4()}"
    runner.session_service.create_session_sync(app_name=runner.app_name, user_id="user", session_id=session_id)
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=context)])
    response_text = ""
    async for event in runner.run_async(new_message=content, user_id="user", session_id=session_id):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            
    return response_text or "Review your tasks and deadlines for a productive day!"
