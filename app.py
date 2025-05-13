import streamlit as st
import sqlite3
import datetime
import os

# ----------- DATABASE SETUP -----------
DB_FILE = "tasks.db"

# Ensure database exists and has correct schema
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            start_time DATETIME,
            end_time DATETIME,
            completed BOOLEAN DEFAULT 0,
            alerted BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Run DB setup
init_db()

# ----------- DATABASE FUNCTIONS -----------
def add_task(text, start_time, end_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (text, start_time, end_time, completed, alerted) VALUES (?, ?, ?, 0, 0)",
              (text, start_time, end_time))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, text, start_time, end_time, completed, alerted FROM tasks ORDER BY start_time ASC")
    tasks = c.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def mark_alerted(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET alerted = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ----------- STREAMLIT UI -----------
st.set_page_config(page_title="🗂️ Task Manager", layout="centered")
st.title("🗂️ Daily Task Manager")

# ----------- ADD TASK FORM -----------
with st.form("add_form"):
    task_text = st.text_input("📝 Task")
    
    start_date = st.date_input("📅 Start Date", value=datetime.date.today())
    start_time = st.time_input("🕒 Start Time", value=datetime.datetime.now().time())
    
    end_date = st.date_input("📅 End Date", value=start_date)
    end_time = st.time_input("🕔 End Time", value=(datetime.datetime.now() + datetime.timedelta(hours=1)).time())
    
    submitted = st.form_submit_button("Add Task")

    if submitted:
        if task_text:
            start_dt = datetime.datetime.combine(start_date, start_time)
            end_dt = datetime.datetime.combine(end_date, end_time)
            if end_dt <= start_dt:
                st.error("❌ End time must be after start time.")
            else:
                add_task(task_text, start_dt, end_dt)
                st.success("✅ Task added successfully!")
                st.rerun()
        else:
            st.warning("⚠️ Please enter a task.")

# ----------- DISPLAY TASKS -----------
tasks = get_tasks()
now = datetime.datetime.now()

st.subheader("📋 Your Tasks")

if not tasks:
    st.info("No tasks added yet.")
else:
    for task in tasks:
        task_id, text, start_str, end_str, completed, alerted = task
        start = datetime.datetime.fromisoformat(start_str)
        end = datetime.datetime.fromisoformat(end_str)
        overdue = now > end and not completed

        col1, col2, col3 = st.columns([6, 2, 2])
        
        # Task display with formatting
        with col1:
            style = "line-through" if completed else "none"
            color = "gray" if completed else ("red" if overdue else "black")
            st.markdown(
                f"<span style='color: {color}; text-decoration: {style}'>"
                f"{text}<br><small>{start.strftime('%b %d, %I:%M %p')} → {end.strftime('%I:%M %p')}</small>"
                f"</span>", unsafe_allow_html=True)

        # Complete button
        with col2:
            if not completed and st.button("✅", key=f"done_{task_id}"):
                update_task_status(task_id, True)
                st.rerun()

        # Delete button
        with col3:
            if st.button("❌", key=f"del_{task_id}"):
                delete_task(task_id)
                st.rerun()

        # Alert for overdue
        if overdue and not alerted:
            st.warning(f"⚠️ Task '{text}' is overdue!")
            mark_alerted(task_id)
