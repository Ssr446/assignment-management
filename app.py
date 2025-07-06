import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------- Custom CSS ----------
def load_custom_css():
    st.markdown("""
        <style>
            .main {
                background-color: #f5f7fa;
            }
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 16px;
                margin-top: 10px;
            }
            .stButton>button:hover {
                background-color: #45a049;
                
            }
            .stDataFrame {
                background-color: white;
                border-radius: 10px;
            }
            .stTextInput>div>div>input {
                background-color: black;
                padding: 10px;
                border-radius: 5px;
            }
            .stDateInput>div>input {
                background-color: #f0f2f6;
                padding: 10px;
                border-radius: 5px;
            }
            .due-soon {
                background-color: black;
                padding: 8px;
                border-radius: 5px;
                border-left: 5px solid #ffc107;
                margin-bottom: 10px;
            }
            .overdue {
                background-color: red;
                padding: 8px;
                border-radius: 5px;
                border-left: 5px solid #dc3545;
                margin-bottom: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

# ---------- Database Initialization ----------
def init_db():
    conn = sqlite3.connect('assignments.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY,
        title TEXT,
        subject TEXT,
        marks INTEGER,
        due_date TEXT,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users (id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY,
        assignment_id INTEGER,
        student_id INTEGER,
        submission_date TEXT,
        status TEXT,
        FOREIGN KEY (assignment_id) REFERENCES assignments (id),
        FOREIGN KEY (student_id) REFERENCES users (id)
    )''')

    users = [
        (1, 'teacher1', 'password', 'teacher'),
        (2, 'coordinator1', 'password', 'coordinator'),
        (3, 'student1', 'password', 'student'),
        (4, 'student2', 'password', 'student'),
        (5, 'student3', 'password', 'student')
    ]

    c.executemany('INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)', users)

    conn.commit()
    conn.close()

# ---------- Login ----------
def login(username, password):
    conn = sqlite3.connect('assignments.db')
    c = conn.cursor()
    c.execute('SELECT id, username, role FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()
    conn.close()
    return user

# ---------- Data Fetch ----------
def get_assignments():
    conn = sqlite3.connect('assignments.db')
    df = pd.read_sql_query('SELECT * FROM assignments', conn)
    conn.close()
    return df

def get_assignment_status():
    conn = sqlite3.connect('assignments.db')
    query = '''
    SELECT 
        a.id, a.title, a.subject, a.marks, a.due_date,
        u.username as student,
        CASE WHEN s.status IS NULL THEN 'Not Submitted' ELSE s.status END as status
    FROM 
        assignments a
    CROSS JOIN 
        users u
    LEFT JOIN 
        submissions s ON a.id = s.assignment_id AND u.id = s.student_id
    WHERE 
        u.role = 'student'
    ORDER BY 
        a.id, u.username
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_assignment(title, subject, marks, due_date, created_by):
    conn = sqlite3.connect('assignments.db')
    c = conn.cursor()
    c.execute('INSERT INTO assignments (title, subject, marks, due_date, created_by) VALUES (?, ?, ?, ?, ?)',
              (title, subject, marks, due_date, created_by))
    conn.commit()
    conn.close()

def submit_assignment(assignment_id, student_id):
    conn = sqlite3.connect('assignments.db')
    c = conn.cursor()
    submission_date = datetime.now().strftime('%Y-%m-%d')

    c.execute('SELECT id FROM submissions WHERE assignment_id = ? AND student_id = ?', (assignment_id, student_id))
    if c.fetchone():
        c.execute('UPDATE submissions SET status = ?, submission_date = ? WHERE assignment_id = ? AND student_id = ?',
                 ('Completed', submission_date, assignment_id, student_id))
    else:
        c.execute('INSERT INTO submissions (assignment_id, student_id, submission_date, status) VALUES (?, ?, ?, ?)',
                 (assignment_id, student_id, submission_date, 'Completed'))

    conn.commit()
    conn.close()

def get_student_assignments(student_id):
    conn = sqlite3.connect('assignments.db')
    query = '''
    SELECT 
        a.id, a.title, a.subject, a.marks, a.due_date,
        CASE WHEN s.status IS NULL THEN 'Not Started' ELSE s.status END as status
    FROM 
        assignments a
    LEFT JOIN 
        submissions s ON a.id = s.assignment_id AND s.student_id = ?
    '''
    df = pd.read_sql_query(query, conn, params=(student_id,))
    conn.close()
    return df

# ---------- Due Date Check ----------
def check_due_status(due_date_str, status):
    if status == 'Completed':
        return "completed"
    
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    today = datetime.now()
    
    if due_date < today:
        return "overdue"
    elif due_date <= today + timedelta(days=3):
        return "due_soon"
    else:
        return "normal"

# ---------- Main ----------
def main():
    load_custom_css()
    init_db()
    
    st.markdown("<h1 style='color:#003566;'>📚 Assignment Management System</h1>", unsafe_allow_html=True)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.container():
            st.markdown("### 🔐 Login to Continue")
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                user = login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.role = user[2]
                    st.success(f"Welcome {user[1]} 👋")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
    else:
        st.sidebar.markdown(f"👤 **User:** {st.session_state.username}")
        st.sidebar.markdown(f"🎓 **Role:** {st.session_state.role.capitalize()}")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

        role = st.session_state.role

        if role == 'teacher':
            st.header("📊 Teacher Dashboard")
            st.subheader("📌 Assignment Submission Overview")
            df = get_assignment_status()
            st.dataframe(df if not df.empty else pd.DataFrame({'Status': ['No data available']}))

        elif role == 'coordinator':
            st.header("🗂️ Coordinator Dashboard")

            with st.expander("➕ Create Assignment"):
                title = st.text_input("Assignment Title")
                subject = st.text_input("Subject")
                marks = st.number_input("Marks", min_value=1, value=10)
                due_date = st.date_input("Due Date")

                if st.button("Submit Assignment"):
                    add_assignment(title, subject, marks, due_date.strftime('%Y-%m-%d'), st.session_state.user_id)
                    st.success("Assignment added successfully 🎉")
                    st.rerun()

            st.subheader("📄 All Assignments")
            df = get_assignments()
            st.dataframe(df if not df.empty else pd.DataFrame({'Info': ['No assignments found']}))

        elif role == 'student':
            st.header("📚 Student Dashboard")
            
            # Display due soon and overdue assignments at the top
            df = get_student_assignments(st.session_state.user_id)
            
            if not df.empty:
                # Separate out assignments that need attention
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Find incomplete assignments
                incomplete_df = df[(df['status'] != 'Completed')]
                
                # Check for overdue assignments
                overdue_df = incomplete_df[incomplete_df['due_date'] < today]
                if not overdue_df.empty:
                    st.markdown("<div class='overdue'><strong>⚠️ OVERDUE ASSIGNMENTS</strong></div>", unsafe_allow_html=True)
                    for _, row in overdue_df.iterrows():
                        st.markdown(f"<div class='overdue'>📝 <strong>{row['title']}</strong> - {row['subject']} - Due: {row['due_date']}</div>", unsafe_allow_html=True)
                
                # Check for assignments due soon (within 3 days)
                soon_due_df = incomplete_df[
                    (incomplete_df['due_date'] >= today) & 
                    (incomplete_df['due_date'] <= (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'))
                ]
                if not soon_due_df.empty:
                    st.markdown("<div class='due-soon'><strong>⏰ DUE SOON</strong></div>", unsafe_allow_html=True)
                    for _, row in soon_due_df.iterrows():
                        st.markdown(f"<div class='due-soon'>📝 <strong>{row['title']}</strong> - {row['subject']} - Due: {row['due_date']}</div>", unsafe_allow_html=True)
                
                # Display all assignments with status indicators
                st.subheader("📋 All Assignments")
                for _, row in df.iterrows():
                    due_status = check_due_status(row['due_date'], row['status'])
                    
                    # Create a custom header based on due status
                    header_text = f"📝 {row['title']} - {row['subject']}"
                    
                    if due_status == "overdue":
                        header_text = f"📝 {row['title']} - {row['subject']} ⚠️ OVERDUE"
                    elif due_status == "due_soon":
                        header_text = f"📝 {row['title']} - {row['subject']} ⏰ DUE SOON"
                    
                    with st.expander(header_text):
                        st.markdown(f"**📅 Due Date:** {row['due_date']}")
                        
                        # Show days remaining or overdue
                        due_date = datetime.strptime(row['due_date'], '%Y-%m-%d')
                        today = datetime.now()
                        days_diff = (due_date - today).days
                        
                        if row['status'] == 'Completed':
                            st.markdown(f"**📌 Status:** `{row['status']} ✅`")
                        elif days_diff < 0:
                            st.markdown(f"**📌 Status:** `{row['status']}` - **{abs(days_diff)} days overdue** 🚨")
                        elif days_diff == 0:
                            st.markdown(f"**📌 Status:** `{row['status']}` - **Due today!** ⚡")
                        else:
                            st.markdown(f"**📌 Status:** `{row['status']}` - **{days_diff} days remaining** ⏳")
                        
                        if row['status'] != 'Completed':
                            if st.button("✅ Mark as Complete", key=f"complete_{row['id']}"):
                                submit_assignment(row['id'], st.session_state.user_id)
                                st.success("Assignment marked as completed ✅")
                                st.rerun()
            else:
                st.info("No assignments available.")

if __name__ == "__main__":
    main()
