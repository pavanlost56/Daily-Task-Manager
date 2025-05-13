import sqlite3
import datetime
import streamlit as st

# Connect to SQLite database
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()

# Create tasks table if not exists
c.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    start_time DATETIME,
    end_time DATETIME,
    completed BOOLEAN,
    alerted BOOLEAN
)
''')
conn.commit()

# Function to add tasks to the database
def add_task(text, start_time, end_time):
    c.execute("INSERT INTO tasks (text, start_time, end_time, completed, alerted) VALUES (?, ?, ?, 0, 0)", 
              (text, start_time, end_time))
    conn.commit()

# Function to update the status of a task to completed
def update_task_status(task_id, status):
    c.execute("UPDATE tasks SET completed = ? WHERE id = ?", (status, task_id))
    conn.commit()

# Function to delete a task
def delete_task(task_id):
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

# Function to mark an alerted task
def mark_alerted(task_id):
    c.execute("UPDATE tasks SET alerted = 1 WHERE id = ?", (task_id,))
    conn.commit()

# Function to fetch all tasks from the database
def get_tasks():
    try:
        c.execute("SELECT id, text, start_time, end_time, completed, alerted FROM tasks ORDER BY start_time ASC")
        return c.fetchall()
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return []

# Form for adding tasks
with st.form("add_form"):
    task_text = st.text_input("📝 Task")
    
    # Start Date & Time
    start_date = st.date_input("📅 Start Date", value=datetime.date.today())
    start_time = st.time_input("🕒 Start Time", value=datetime.datetime.now().time())
    
    # End Date & Time
    end_date = st.date_input("📅 End Date", value=start_date)
    end_time = st.time_input("🕔 End Time", value=(datetime.datetime.now() + datetime.timedelta(hours=1)).time())
    
    submitted = st.form_submit_button("Add Task")

    if submitted:
        if task_text:
            start_dt = datetime.datetime.combine(start_date, start_time)
            end_dt = datetime.datetime.combine(end_date, end_time)
            
            # Validate that end time is after start time
            if end_dt <= start_dt:
                st.error("❌ End time must be after start time.")
            else:
                add_task(task_text, start_dt, end_dt)
                st.success("✅ Task added!")
                st.rerun()  # Refresh to show updated task list
        else:
            st.warning("⚠️ Please enter a task.")

# Fetch and display tasks
tasks = get_tasks()
now = datetime.datetime.now()

for task in tasks:
    task_id, text, start_str, end_str, completed, alerted = task
    start = datetime.datetime.fromisoformat(start_str)  # Convert start_time string to datetime
    end = datetime.datetime.fromisoformat(end_str)  # Convert end_time string to datetime
    overdue = now > end and not completed

    col1, col2, col3 = st.columns([6, 2, 2])

    with col1:
        style = "line-through" if completed else "none"
        color = "gray" if completed else ("red" if overdue else "black")
        st.markdown(
            f"<span style='color: {color}; text-decoration: {style}'>"
            f"{text}<br><small>{start.strftime('%b %d, %I:%M %p')} → {end.strftime('%I:%M %p')}</small>"
            f"</span>", unsafe_allow_html=True)

    with col2:
        if not completed and st.button("✅", key=f"done_{task_id}"):
            update_task_status(task_id, True)
            st.rerun()

    with col3:
        if st.button("❌", key=f"del_{task_id}"):
            delete_task(task_id)
            st.rerun()

    if overdue and not alerted:
        st.warning(f"⚠️ Task '{text}' is overdue!")
        mark_alerted(task_id)
