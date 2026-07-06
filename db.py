import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dailypilot.db")

def get_connection():
    """Establish a connection to the SQLite database with safe defaults."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initialize database tables with correct schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Expenses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        date TEXT DEFAULT (date('now'))
    )
    """)
    
    # 2. Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        due_date TEXT
    )
    """)
    
    # 3. Deadlines Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending'
    )
    """)
    
    conn.commit()
    conn.close()

# --- Expense Database Operations ---

def add_expense_db(amount: float, category: str, description: str) -> str:
    """Inserts a new expense into the database with input validation."""
    # 1. Input Validation
    if amount <= 0:
        raise ValueError("Expense amount must be greater than zero.")
    if not category.strip():
        raise ValueError("Category cannot be empty.")
    if not description.strip():
        raise ValueError("Description cannot be empty.")
        
    category = category.strip()
    description = description.strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (amount, category, description) VALUES (?, ?, ?)",
            (amount, category, description)
        )
        conn.commit()
        return f"Successfully recorded expense: ₹{amount:.2f} for '{description}' ({category})"
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_expenses():
    """Retrieve all expenses sorted by date descending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, category, description, date FROM expenses ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_monthly_total() -> float:
    """Calculate the total expense for the current month."""
    conn = get_connection()
    cursor = conn.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = ?",
        (current_month,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result[0] is not None else 0.0

# --- Task Database Operations ---

def add_task_db(title: str, description: str = "", due_date: str = None) -> str:
    """Inserts a new task with validation."""
    if not title.strip():
        raise ValueError("Task title cannot be empty.")
    
    title = title.strip()
    description = description.strip() if description else ""
    
    # Simple due date validation format (YYYY-MM-DD) if provided
    if due_date:
        due_date = due_date.strip()
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            # If not valid format, default to today
            due_date = datetime.now().strftime("%Y-%m-%d")
    else:
        due_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tasks (title, description, status, due_date) VALUES (?, ?, 'pending', ?)",
            (title, description, due_date)
        )
        conn.commit()
        return f"Successfully added task: '{title}'"
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_tasks():
    """Retrieve all tasks sorted by due date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, status, due_date FROM tasks ORDER BY status DESC, due_date ASC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def complete_task_db(task_id: int):
    """Mark a task as completed."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_task_db(task_id: int):
    """Delete a task from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Deadline Database Operations ---

def add_deadline_db(title: str, due_date: str) -> str:
    """Inserts a new deadline with validation."""
    if not title.strip():
        raise ValueError("Deadline title cannot be empty.")
    if not due_date.strip():
        raise ValueError("Deadline due date cannot be empty.")
        
    title = title.strip()
    due_date = due_date.strip()
    
    # Try parsing date relative terms or check format
    # Simple validation for YYYY-MM-DD
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        # Fallback to today if parsing fails
        due_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO deadlines (title, due_date, status) VALUES (?, ?, 'pending')",
            (title, due_date)
        )
        conn.commit()
        return f"Successfully added deadline: '{title}' on {due_date}"
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_deadlines():
    """Retrieve all deadlines sorted by date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, due_date, status FROM deadlines ORDER BY status DESC, due_date ASC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def complete_deadline_db(deadline_id: int):
    """Mark a deadline as completed."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE deadlines SET status = 'completed' WHERE id = ?", (deadline_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_deadline_db(deadline_id: int):
    """Delete a deadline from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM deadlines WHERE id = ?", (deadline_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Initialize DB on import if file does not exist ---
if not os.path.exists(DB_PATH):
    init_db()
