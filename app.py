import os
import sys
import asyncio
from datetime import datetime
import streamlit as st

# Ensure the current directory is in the import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db
import agents

# Page configuration
st.set_page_config(
    page_title="DailyPilot – Your AI Copilot for Everyday Life",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Key Validation / Input Fallback
if not os.getenv("GEMINI_API_KEY"):
    st.sidebar.warning("⚠️ GEMINI_API_KEY is not configured in .env.")
    api_key_input = st.sidebar.text_input("Provide Gemini API Key", type="password", help="Your API key will only be used for the current session.")
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.sidebar.success("API Key loaded successfully!")
else:
    st.sidebar.success("🔑 Gemini API Key detected in environment.")

# Sidebar navigation
st.sidebar.title("✈️ DailyPilot")
st.sidebar.markdown("*Your AI Copilot for Everyday Life*")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate to",
    ["Dashboard", "AI Inbox", "Finance Tracker", "Tasks Manager"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Google x Kaggle Agents Capstone")
st.sidebar.caption("Built with Python, Streamlit, Google ADK & MCP Server")

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
    }
    
    /* Metrics glassmorphism style */
    .metric-container {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
    }
    
    .metric-card {
        flex: 1;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 255, 255, 0.25);
    }
    
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 36px;
        font-weight: 800;
        margin-top: 8px;
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-title {
        font-size: 14px;
        font-weight: 500;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Coach Summary accent block */
    .coach-box {
        background: linear-gradient(135deg, rgba(29, 38, 113, 0.2) 0%, rgba(195, 55, 100, 0.1) 100%);
        border-left: 5px solid #ff007f;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    .coach-title {
        font-family: 'Outfit', sans-serif;
        font-size: 20px;
        font-weight: 600;
        color: #ff007f;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .table-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to run async methods synchronously inside Streamlit
def run_async_fn(async_fn, *args, **kwargs):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_fn(*args, **kwargs))

# Ensure database tables exist
db.init_db()

# ==========================================
# 1. PAGE: DASHBOARD
# ==========================================
if page == "Dashboard":
    st.markdown("# ✈️ DailyPilot Dashboard")
    st.markdown("*Overview of your financial and task statuses, curated by your AI Coach.*")
    st.markdown("---")
    
    # 1. Fetch values from SQLite
    expenses_total = db.get_monthly_total()
    pending_tasks = len([t for t in db.get_all_tasks() if t['status'] == 'pending'])
    upcoming_deadlines = len([d for d in db.get_all_deadlines() if d['status'] == 'pending'])
    
    # 2. Render Cards
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-title">💳 Total Expenses (This Month)</div>
            <div class="metric-value">₹{expenses_total:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">📋 Pending Tasks</div>
            <div class="metric-value">{pending_tasks}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">⏳ Upcoming Deadlines</div>
            <div class="metric-value">{upcoming_deadlines}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Daily Coach Summary
    st.markdown("## 🧠 Daily Coach Priority Summary")
    if not os.getenv("GEMINI_API_KEY"):
        st.info("⚠️ Add your Gemini API key in the sidebar to enable the Daily Coach summary.")
    else:
        with st.spinner("AI Coach is analyzing your schedule and spending patterns..."):
            try:
                coach_summary = run_async_fn(agents.generate_daily_coach_summary)
                st.markdown(f"""
                <div class="coach-box">
                    <div class="coach-title">✨ Coach Insights</div>
                    <div>{coach_summary}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Coach summary generation failed: {str(e)}")
                
    # 4. Deadlines List
    st.markdown("## 📅 Upcoming Deadlines")
    deadlines = db.get_all_deadlines()
    pending_deadlines = [d for d in deadlines if d['status'] == 'pending']
    
    if not pending_deadlines:
        st.success("No upcoming deadlines! Keep it up.")
    else:
        for d in pending_deadlines:
            cols = st.columns([0.6, 0.2, 0.2])
            cols[0].markdown(f"🎯 **{d['title']}**")
            cols[1].markdown(f"📅 Due: `{d['due_date']}`")
            if cols[2].button("Mark Completed", key=f"dead_{d['id']}"):
                db.complete_deadline_db(d['id'])
                st.success(f"Completed: {d['title']}!")
                st.rerun()

# ==========================================
# 2. PAGE: AI INBOX
# ==========================================
elif page == "AI Inbox":
    st.markdown("# 📥 AI Inbox – Natural Language Parser")
    st.markdown("Type whatever happens in your day, and DailyPilot will automatically parse, classify, and delegate actions to Finance, Tasks, and Reminder agents.")
    st.markdown("---")
    
    st.markdown("### 💬 Express your day in natural language:")
    user_prompt = st.text_area(
        "Enter expenses, tasks, deadlines, or combination of them:",
        placeholder="Spent ₹500 on groceries, book train tickets, Kaggle deadline tomorrow.",
        height=100
    )
    
    if st.button("🚀 Process with DailyPilot"):
        if not user_prompt.strip():
            st.error("Please enter some text for the AI Inbox to process.")
        elif not os.getenv("GEMINI_API_KEY"):
            st.error("A Gemini API Key is required. Please set it in the sidebar or check your '.env' file.")
        else:
            with st.spinner("Orchestrator Agent routing items..."):
                try:
                    result = run_async_fn(agents.run_orchestrator, user_prompt)
                    st.success("DailyPilot processing completed!")
                    st.markdown("### 📋 Orchestrator Execution Summary:")
                    st.info(result)
                except Exception as e:
                    st.error(f"Failed to process prompt. Details: {str(e)}")

# ==========================================
# 3. PAGE: FINANCE TRACKER
# ==========================================
elif page == "Finance Tracker":
    st.markdown("# 💳 Finance Tracker")
    st.markdown("Monitor expenses and calculate monthly spendings.")
    st.markdown("---")
    
    col1, col2 = st.columns([0.4, 0.6])
    
    # Left Column: Add Expense Form
    with col1:
        st.markdown("### ➕ Log Expense Manually")
        with st.form("manual_expense"):
            amount = st.number_input("Amount (INR)", min_value=0.01, step=10.0, format="%.2f")
            category = st.selectbox("Category", ["Food", "Groceries", "Travel/Transit", "Kaggle/Work", "Shopping", "Entertainment", "Utilities", "Other"])
            description = st.text_input("Description", placeholder="E.g., Dinner at restaurant, Bus pass")
            submit_expense = st.form_submit_button("Record Expense")
            
            if submit_expense:
                if not description.strip():
                    st.error("Please enter a description.")
                else:
                    try:
                        msg = db.add_expense_db(amount, category, description)
                        st.success(msg)
                    except Exception as e:
                        st.error(f"Failed to save expense: {str(e)}")
                        
    # Right Column: View Expenses
    with col2:
        st.markdown("### 📊 Monthly Expenditure Total")
        total = db.get_monthly_total()
        st.markdown(f"## **₹{total:,.2f}**")
        
        st.markdown("### 📜 Expense History")
        expenses = db.get_all_expenses()
        if not expenses:
            st.info("No recorded expenses yet.")
        else:
            # Format display table
            expense_data = []
            for e in expenses:
                expense_data.append({
                    "Date": e["date"],
                    "Description": e["description"],
                    "Category": e["category"],
                    "Amount": f"₹{e['amount']:.2f}"
                })
            st.table(expense_data)

# ==========================================
# 4. PAGE: TASKS MANAGER
# ==========================================
elif page == "Tasks Manager":
    st.markdown("# 📋 Tasks & Deadlines Manager")
    st.markdown("Manage your personal lists, complete tasks, and track deadlines.")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📋 Tasks", "📅 Deadlines"])
    
    # Tab 1: Tasks
    with tab1:
        col1, col2 = st.columns([0.4, 0.6])
        
        with col1:
            st.markdown("### ➕ Add Task Manually")
            with st.form("manual_task"):
                title = st.text_input("Task Title", placeholder="E.g., Book train tickets")
                description = st.text_area("Details (Optional)", placeholder="E.g., Reservation for 2AC tickets")
                due_date = st.date_input("Due Date", min_value=datetime.today())
                submit_task = st.form_submit_button("Create Task")
                
                if submit_task:
                    if not title.strip():
                        st.error("Please enter a task title.")
                    else:
                        try:
                            msg = db.add_task_db(title, description, due_date.strftime("%Y-%m-%d"))
                            st.success(msg)
                        except Exception as e:
                            st.error(f"Failed to save task: {str(e)}")
                            
        with col2:
            st.markdown("### ⏳ Active Tasks")
            tasks = db.get_all_tasks()
            pending_tasks = [t for t in tasks if t['status'] == 'pending']
            
            if not pending_tasks:
                st.success("All tasks completed! Enjoy your day.")
            else:
                for t in pending_tasks:
                    st.markdown(f"**{t['title']}**")
                    if t['description']:
                        st.caption(t['description'])
                    st.caption(f"📅 Due: {t['due_date']}")
                    
                    c1, c2 = st.columns([0.2, 0.8])
                    if c1.button("Complete", key=f"t_done_{t['id']}"):
                        db.complete_task_db(t['id'])
                        st.success("Task completed!")
                        st.rerun()
                    if c2.button("Delete", key=f"t_del_{t['id']}"):
                        db.delete_task_db(t['id'])
                        st.warning("Task deleted.")
                        st.rerun()
                    st.markdown("---")
                    
            st.markdown("### ✅ Completed Tasks")
            completed_tasks = [t for t in tasks if t['status'] == 'completed']
            if not completed_tasks:
                st.caption("No completed tasks yet.")
            else:
                for t in completed_tasks:
                    st.markdown(f"~~{t['title']}~~ (Completed)")
                    if st.button("Delete", key=f"t_comp_del_{t['id']}"):
                        db.delete_task_db(t['id'])
                        st.rerun()

    # Tab 2: Deadlines
    with tab2:
        col1, col2 = st.columns([0.4, 0.6])
        
        with col1:
            st.markdown("### ➕ Add Deadline Manually")
            with st.form("manual_deadline"):
                d_title = st.text_input("Deadline Title", placeholder="E.g., Kaggle final entry submission")
                d_date = st.date_input("Deadline Date", min_value=datetime.today())
                submit_d = st.form_submit_button("Record Deadline")
                
                if submit_d:
                    if not d_title.strip():
                        st.error("Please enter a deadline title.")
                    else:
                        try:
                            msg = db.add_deadline_db(d_title, d_date.strftime("%Y-%m-%d"))
                            st.success(msg)
                        except Exception as e:
                            st.error(f"Failed to record deadline: {str(e)}")
                            
        with col2:
            st.markdown("### 📅 Track Deadlines")
            deadlines = db.get_all_deadlines()
            p_deadlines = [d for d in deadlines if d['status'] == 'pending']
            
            if not p_deadlines:
                st.success("No active deadlines!")
            else:
                for d in p_deadlines:
                    st.markdown(f"🎯 **{d['title']}**")
                    st.caption(f"📅 Date: `{d['due_date']}`")
                    
                    c1, c2 = st.columns([0.3, 0.7])
                    if c1.button("Complete", key=f"d_done_{d['id']}"):
                        db.complete_deadline_db(d['id'])
                        st.success("Deadline marked as completed!")
                        st.rerun()
                    if c2.button("Delete", key=f"d_del_{d['id']}"):
                        db.delete_deadline_db(d['id'])
                        st.warning("Deadline deleted.")
                        st.rerun()
                    st.markdown("---")
                    
            st.markdown("### ✅ Completed Deadlines")
            c_deadlines = [d for d in deadlines if d['status'] == 'completed']
            if not c_deadlines:
                st.caption("No completed deadlines yet.")
            else:
                for d in c_deadlines:
                    st.markdown(f"~~{d['title']}~~ (Completed)")
                    if st.button("Delete", key=f"d_comp_del_{d['id']}"):
                        db.delete_deadline_db(d['id'])
                        st.rerun()
