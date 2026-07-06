import os
import sys
from fastmcp import FastMCP

# Ensure the workspace directory is in the python path for importing db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db

# Define FastMCP server
mcp = FastMCP("DailyPilot Tools Server")

@mcp.tool()
def add_expense(amount: float, category: str, description: str) -> str:
    """Add a new expense record to the database.
    
    Args:
        amount: The monetary value of the expense (e.g. 500.00). Must be positive.
        category: The group of expense (e.g. food, groceries, travel, shopping, rent, Kaggle).
        description: A brief note explaining what the expense was for.
    """
    try:
        return db.add_expense_db(amount, category, description)
    except Exception as e:
        return f"Error: Failed to add expense to database. Details: {str(e)}"

@mcp.tool()
def add_task(title: str, description: str = "", due_date: str = None) -> str:
    """Add a new task to the task list in the database.
    
    Args:
        title: The name/summary of the task (e.g. 'book train tickets').
        description: Optional details or actions required for the task.
        due_date: Optional due date in YYYY-MM-DD format. Defaults to today's date.
    """
    try:
        return db.add_task_db(title, description, due_date)
    except Exception as e:
        return f"Error: Failed to add task to database. Details: {str(e)}"

if __name__ == "__main__":
    # Ensure database is initialized
    db.init_db()
    # Start the fastmcp stdio server loop
    mcp.run()
