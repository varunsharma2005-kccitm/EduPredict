import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import html
import os
import shutil
from datetime import datetime

from model import model, mae, r2


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="EduPredict | AI Student Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "edupredict.db"


# =========================================================
# DATABASE
# =========================================================
def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    # Keep a backup of the old database before any migration.
    if os.path.exists(DB_NAME):
        backup_file = "edupredict_backup_before_migration.db"
        if not os.path.exists(backup_file):
            shutil.copy2(DB_NAME, backup_file)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            study_hours REAL,
            attendance REAL,
            previous_marks REAL,
            assignment_score REAL,
            sleep_hours REAL,
            predicted_marks REAL,
            performance TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(predictions)")
    old_info = cursor.fetchall()
    old_columns = [row[1] for row in old_info]

    allowed_columns = {
        "id", "student_name", "study_hours", "attendance",
        "previous_marks", "assignment_score", "sleep_hours",
        "predicted_marks", "performance", "created_at"
    }

    rebuild_required = False
    for column in old_info:
        name, not_null, default_value, primary_key = (
            column[1], column[3], column[4], column[5]
        )
        if name == "user_id":
            rebuild_required = True
        elif name not in allowed_columns and not_null == 1 \
                and default_value is None and primary_key == 0:
            rebuild_required = True

    if rebuild_required:
        cursor.execute("DROP TABLE IF EXISTS predictions_new")
        cursor.execute("""
            CREATE TABLE predictions_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                study_hours REAL,
                attendance REAL,
                previous_marks REAL,
                assignment_score REAL,
                sleep_hours REAL,
                predicted_marks REAL,
                performance TEXT,
                created_at TEXT
            )
        """)

        new_columns = [
            "id", "student_name", "study_hours", "attendance",
            "previous_marks", "assignment_score", "sleep_hours",
            "predicted_marks", "performance", "created_at"
        ]
        common_columns = [c for c in new_columns if c in old_columns]

        if common_columns:
            names = ", ".join(common_columns)
            cursor.execute(
                f"INSERT INTO predictions_new ({names}) "
                f"SELECT {names} FROM predictions"
            )

        cursor.execute("DROP TABLE predictions")
        cursor.execute(
            "ALTER TABLE predictions_new RENAME TO predictions"
        )

    cursor.execute("PRAGMA table_info(predictions)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    required_columns = {
        "student_name": "TEXT",
        "study_hours": "REAL",
        "attendance": "REAL",
        "previous_marks": "REAL",
        "assignment_score": "REAL",
        "sleep_hours": "REAL",
        "predicted_marks": "REAL",
        "performance": "TEXT",
        "created_at": "TEXT"
    }

    for column, data_type in required_columns.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE predictions ADD COLUMN {column} {data_type}"
            )

    conn.commit()
    conn.close()


initialize_database()


def save_prediction(
    student_name, study_hours, attendance, previous_marks,
    assignment_score, sleep_hours, predicted_marks, performance
):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO predictions (
                student_name, study_hours, attendance, previous_marks,
                assignment_score, sleep_hours, predicted_marks,
                performance, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_name, study_hours, attendance, previous_marks,
            assignment_score, sleep_hours, predicted_marks, performance,
            datetime.now().strftime("%d-%m-%Y %I:%M %p")
        ))
        conn.commit()
    finally:
        conn.close()


def get_history():
    conn = get_connection()
    try:
        return pd.read_sql_query("""
            SELECT
                id,
                student_name AS 'Student Name',
                study_hours AS 'Study Hours',
                attendance AS 'Attendance',
                previous_marks AS 'Previous Marks',
                assignment_score AS 'Assignment Score',
                sleep_hours AS 'Sleep Hours',
                predicted_marks AS 'Predicted Marks',
                performance AS 'Performance',
                created_at AS 'Date'
            FROM predictions
            ORDER BY id DESC
        """, conn)
    finally:
        conn.close()


# =========================================================
# COMPLETE DARK RED THEME
# =========================================================
st.markdown("""
<style>
/* Main page */
.stApp, [data-testid="stAppViewContainer"] {
    background: #080808 !important;
    color: #f5f5f5 !important;
}
[data-testid="stHeader"] {
    background: rgba(8, 8, 8, 0.95) !important;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #150707 !important;
    border-right: 1px solid #8f1515 !important;
}
[data-testid="stSidebar"] * {
    color: #f5f5f5 !important;
}

/* General text */
h1, h2, h3, h4, h5, h6 {
    color: #ff4545 !important;
}
p, label, span, li, small, .stMarkdown, .stCaption {
    color: #eeeeee;
}
hr {
    border-color: #702020 !important;
}

/* Text, number and textarea fields */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input {
    background: #211313 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #9f2929 !important;
    border-radius: 8px !important;
    caret-color: #ffffff !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #c7aaaa !important;
    -webkit-text-fill-color: #c7aaaa !important;
    opacity: 1 !important;
}

/* Selectbox and multiselect */
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    background: #211313 !important;
    color: #ffffff !important;
    border-color: #9f2929 !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stMultiSelect"] [data-baseweb="select"] * {
    color: #ffffff !important;
}
[data-baseweb="popover"], [data-baseweb="menu"],
[role="listbox"], [role="option"] {
    background: #211313 !important;
    color: #ffffff !important;
}
[role="option"]:hover {
    background: #572020 !important;
}

/* Sliders */
[data-testid="stSlider"] * {
    color: #ffffff !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div {
    border-color: #ff4545;
}

/* Radio buttons, checkboxes and toggles */
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label,
[data-testid="stToggle"] label {
    color: #ffffff !important;
}
[data-testid="stRadio"] [role="radiogroup"] {
    background: transparent !important;
}

/* Forms and expanders */
[data-testid="stForm"] {
    background: #100909 !important;
    border: 1px solid #702020 !important;
    border-radius: 14px !important;
    padding: 20px !important;
}
[data-testid="stExpander"] {
    background: #160c0c !important;
    border: 1px solid #702020 !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: #ffffff !important;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
    background: #a90000 !important;
    color: #ffffff !important;
    border: 1px solid #ff4545 !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    min-height: 42px;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover {
    background: #d71920 !important;
    color: #ffffff !important;
    border-color: #ff7777 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #2a0b0b, #120808) !important;
    border: 1px solid #8f2525 !important;
    padding: 18px !important;
    border-radius: 13px !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #ffffff !important;
}

/* Alerts */
[data-testid="stAlert"] {
    background: #251010 !important;
    color: #ffffff !important;
    border: 1px solid #a83232 !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"] * {
    color: #ffffff !important;
}

/* Tabs */
[data-baseweb="tab-list"] {
    background: #160909 !important;
}
[data-baseweb="tab"],
[data-baseweb="tab"] * {
    color: #ffffff !important;
}
[data-baseweb="tab"][aria-selected="true"] {
    color: #ff5555 !important;
    border-bottom-color: #ff4545 !important;
}

/* Tables and dataframe containers */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    background: #160909 !important;
    color: #ffffff !important;
    border: 1px solid #702020 !important;
    border-radius: 8px !important;
}
[data-testid="stDataFrame"] iframe {
    background: #160909 !important;
}

/* Code blocks and JSON */
[data-testid="stCode"],
.stCodeBlock, pre, code {
    background: #1b1010 !important;
    color: #ffffff !important;
}

/* Custom cards */
.prediction-card {
    background: linear-gradient(135deg, #300808, #100707);
    border: 1px solid #ff4545;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
}
.prediction-number {
    color: #ff4545;
    font-size: 48px;
    font-weight: 800;
}
.prediction-label {
    color: #ffffff;
    font-size: 18px;
}
.advice-card {
    background: #190b0b;
    border-left: 4px solid #ff4545;
    border-radius: 10px;
    padding: 16px;
    margin: 12px 0;
    color: #ffffff;
}
.guide-card {
    background: #170909;
    border: 1px solid #7c2525;
    border-radius: 12px;
    padding: 18px;
    margin: 10px 0;
    color: #ffffff;
}
.small-text {
    color: #c9baba !important;
    font-size: 13px;
}
/* FIX: Suggestion and advice text visibility */
.advice-card,
.guide-card {
    background-color: #190b0b !important;
    color: #ffffff !important;
    border: 1px solid #ff4545 !important;
}

.advice-card *,
.guide-card * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.stAlert,
.stAlert p,
.stAlert div,
.stAlert span {
    background-color: #251010 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)
# =========================================================
# PERFORMANCE AND GUIDANCE
# =========================================================
def get_performance(marks):
    if marks >= 80:
        return "Excellent"
    if marks >= 60:
        return "Good"
    if marks >= 40:
        return "Average"
    return "Needs Improvement"


def generate_advice(
    study_hours, attendance, previous_marks,
    assignment_score, sleep_hours, predicted_marks
):
    strengths, weaknesses, suggestions = [], [], []

    if study_hours >= 6:
        strengths.append("Your daily study time is strong.")
    elif study_hours >= 3:
        strengths.append("You have a reasonable study routine.")
    else:
        weaknesses.append("Your daily study time is relatively low.")
        suggestions.append(
            "Increase study time gradually. Start with 30 extra minutes daily."
        )

    if attendance >= 85:
        strengths.append("Your attendance is excellent.")
    elif attendance >= 75:
        strengths.append("Your attendance is satisfactory.")
    else:
        weaknesses.append("Your attendance needs improvement.")
        suggestions.append(
            "Try to maintain at least 75-85% attendance and attend classes regularly."
        )

    if previous_marks >= 80:
        strengths.append("Your previous academic performance is excellent.")
    elif previous_marks < 50:
        weaknesses.append("Your previous academic scores are low.")
        suggestions.append(
            "Revise basic concepts and solve at least 10 practice questions daily."
        )
    else:
        strengths.append("You have a foundation to build upon.")

    if assignment_score >= 80:
        strengths.append("You are performing well in assignments.")
    elif assignment_score < 60:
        weaknesses.append("Your assignment performance needs attention.")
        suggestions.append(
            "Complete assignments on time and practice practical examples."
        )

    if sleep_hours >= 7:
        strengths.append("Your sleep duration is healthy.")
    elif sleep_hours < 6:
        weaknesses.append("Your sleep duration is lower than recommended.")
        suggestions.append("Try to get around 7-9 hours of sleep.")

    if predicted_marks >= 80:
        review = (
            "Excellent performance! Your current academic indicators are strong. "
            "Focus on consistency and keep challenging yourself."
        )
    elif predicted_marks >= 60:
        review = (
            "Good performance! You have a positive foundation. "
            "Improving weaker areas can help you progress further."
        )
    elif predicted_marks >= 40:
        review = (
            "Average performance. Focus on revision, attendance and regular practice."
        )
    else:
        review = (
            "Your estimated performance needs attention. "
            "Start with basic concepts and small daily goals."
        )

    if not strengths:
        strengths.append("You have started evaluating your academic performance.")
    if not suggestions:
        suggestions.append(
            "Maintain your current routine and keep testing your knowledge."
        )

    return strengths, weaknesses, suggestions, review


def generate_study_plan(study_hours, attendance, previous_marks):
    if study_hours < 2:
        target_hours = 3
    elif study_hours < 4:
        target_hours = 4
    else:
        target_hours = min(study_hours + 1, 8)

    plan = [
        {"time": "30 Minutes", "task": "Revise yesterday's topics",
         "reason": "Strengthen memory and understanding."},
        {"time": "60 Minutes", "task": "Study difficult subjects",
         "reason": "Give more time to weak concepts."},
        {"time": "45 Minutes", "task": "Practice questions",
         "reason": "Improve problem-solving ability."},
        {"time": "30 Minutes", "task": "Assignments and practical work",
         "reason": "Improve academic performance."},
        {"time": "15 Minutes", "task": "Quick revision",
         "reason": "Recall important concepts."}
    ]

    if attendance < 75:
        plan.insert(0, {
            "time": "Daily", "task": "Attend regular classes",
            "reason": "Improve attendance and classroom understanding."
        })

    if previous_marks < 50:
        plan.append({
            "time": "20 Minutes", "task": "Revise basic concepts",
            "reason": "Build a stronger foundation."
        })

    return target_hours, plan


# =========================================================
# DASHBOARD
# =========================================================
def dashboard_page():
    st.title("🎓 EduPredict Dashboard")
    st.markdown("### Welcome to your AI Student Performance Advisor!")

    history = get_history()
    total = len(history)
    average = history["Predicted Marks"].mean() if total else 0
    highest = history["Predicted Marks"].max() if total else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Predictions", total)
    c2.metric("Average Marks", f"{average:.2f}")
    c3.metric("Highest Marks", f"{highest:.2f}")

    st.markdown("---")
    st.subheader("🚀 Getting Started")
    st.markdown("""
EduPredict helps students understand their estimated academic performance
and identify areas that may need improvement.

**What you can do:**
- Predict your expected academic marks.
- Get a detailed performance review.
- Receive personalized improvement suggestions.
- Generate a practical daily study plan.
- Track previous predictions.
""")

    st.markdown("---")
    st.subheader("📊 Recent Predictions")
    if history.empty:
        st.info("No predictions yet. Visit AI Prediction to get started.")
    else:
        st.dataframe(
            history.head(5).drop(columns=["id"]),
            use_container_width=True,
            hide_index=True
        )
        # =========================================================
# AI PREDICTION
# =========================================================
def prediction_page():
    st.title("🤖 AI Student Performance Prediction")
    st.write(
        "Enter your academic information to get a marks estimate "
        "and personalized guidance."
    )

    with st.form("prediction_form", clear_on_submit=False):
        student_name = st.text_input(
            "Student Name", placeholder="Enter your name"
        )
        st.markdown("### 📚 Academic Information")
        col1, col2 = st.columns(2)

        with col1:
            study_hours = st.slider(
                "Daily Study Hours", 0.0, 12.0, 4.0, 0.5
            )
            attendance = st.slider("Attendance (%)", 0, 100, 75)
            previous_marks = st.slider("Previous Marks", 0, 100, 60)

        with col2:
            assignment_score = st.slider("Assignment Score", 0, 100, 70)
            sleep_hours = st.slider(
                "Daily Sleep Hours", 0.0, 12.0, 7.0, 0.5
            )

        submit = st.form_submit_button("🔮 PREDICT & GET MY AI REVIEW")

    if submit:
        if not student_name.strip():
            st.warning("Please enter your name first.")
            return

        # Keep this feature order exactly the same as model.py.
        input_data = pd.DataFrame([{
            "study_hours": float(study_hours),
            "attendance": float(attendance),
            "previous_marks": float(previous_marks),
            "assignment_score": float(assignment_score),
            "sleep_hours": float(sleep_hours)
        }])

        try:
            raw_prediction = float(model.predict(input_data)[0])
            prediction = max(0.0, min(100.0, raw_prediction))
            performance = get_performance(prediction)

            save_prediction(
                student_name.strip(), study_hours, attendance,
                previous_marks, assignment_score, sleep_hours,
                prediction, performance
            )

            st.session_state.latest_result = {
                "name": student_name.strip(),
                "prediction": prediction,
                "raw_prediction": raw_prediction,
                "performance": performance,
                "study_hours": study_hours,
                "attendance": attendance,
                "previous_marks": previous_marks,
                "assignment_score": assignment_score,
                "sleep_hours": sleep_hours
            }

            st.success("Prediction generated and saved successfully!")
            st.markdown("---")
            st.subheader("🎯 Your Prediction Result")

            c1, c2 = st.columns(2)
            c1.metric("Predicted Marks", f"{prediction:.2f}/100")
            c2.metric("Performance", performance)

            if raw_prediction > 100:
                st.caption(
                    f"Model raw estimate: {raw_prediction:.2f}. "
                    "Displayed marks are capped at 100."
                )
            elif raw_prediction < 0:
                st.caption(
                    f"Model raw estimate: {raw_prediction:.2f}. "
                    "Displayed marks are floored at 0."
                )

            st.markdown("### 📋 Your Submitted Information")
            st.dataframe(
                input_data.rename(columns={
                    "study_hours": "Study Hours",
                    "attendance": "Attendance (%)",
                    "previous_marks": "Previous Marks",
                    "assignment_score": "Assignment Score",
                    "sleep_hours": "Sleep Hours"
                }),
                use_container_width=True,
                hide_index=True
            )
            st.info(
                "Your detailed feedback is available in "
                "'AI Review & Guidance' in the sidebar."
            )

        except Exception as error:
            st.error(f"Prediction error: {error}")


# =========================================================
# AI REVIEW AND GUIDANCE
# =========================================================
def review_page():
    st.title("🧠 AI Performance Review & Guidance")
    result = st.session_state.get("latest_result")

    if not result:
        st.info("Please make a prediction first to generate your AI review.")
        return

    st.markdown(f"### Hello, {html.escape(result['name'])}! 👋")
    st.write("Here is your detailed academic performance analysis.")
    st.markdown("---")

    prediction = result["prediction"]
    st.markdown(f"""
        <div class="prediction-card">
            <div class="prediction-label">Your Estimated Academic Score</div>
            <div class="prediction-number">{prediction:.2f}/100</div>
            <div class="prediction-label">{html.escape(result['performance'])}</div>
        </div>
    """, unsafe_allow_html=True)

    strengths, weaknesses, suggestions, review = generate_advice(
        result["study_hours"], result["attendance"],
        result["previous_marks"], result["assignment_score"],
        result["sleep_hours"], prediction
    )

    st.markdown("---")
    st.subheader("📝 Overall AI Review")
    st.markdown(
        f'<div class="advice-card">{html.escape(review)}</div>',
        unsafe_allow_html=True
    )

    st.subheader("🌟 Your Strengths")
    for item in strengths:
        st.success(item)

    st.subheader("⚠️ Areas That Need Improvement")
    if weaknesses:
        for item in weaknesses:
            st.warning(item)
    else:
        st.success("No major weak area identified from your current inputs.")

    st.markdown("---")
    st.subheader("💡 Personalized AI Advice")
    for index, item in enumerate(suggestions, 1):
        st.markdown(
            f'<div class="advice-card"><b>Advice {index}</b><br>'
            f'{html.escape(item)}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("🎯 Your Improvement Roadmap")
    roadmap = [
        "Set a realistic daily study target.",
        "Identify your two weakest subjects.",
        "Revise difficult concepts regularly.",
        "Practice questions every day.",
        "Complete assignments on time.",
        "Review your progress every week."
    ]
    for index, item in enumerate(roadmap, 1):
        st.markdown(f"**Step {index}:** {item}")

    st.markdown("---")
    st.subheader("📅 Your Personalized Daily Study Plan")
    target_hours, plan = generate_study_plan(
        result["study_hours"], result["attendance"],
        result["previous_marks"]
    )
    st.info(
        f"Recommended target: Approximately {target_hours} study hours daily."
    )

    for item in plan:
        st.markdown(f"""
            <div class="guide-card">
                <b>⏰ {html.escape(item['time'])}</b><br>
                <b>📚 {html.escape(item['task'])}</b><br>
                <span class="small-text">{html.escape(item['reason'])}</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📖 Academic Success Tips")
    st.markdown("""
1. Understand concepts instead of memorizing everything.
2. Practice previous-year question papers.
3. Use short revision sessions.
4. Avoid distractions during study hours.
5. Take small breaks between study sessions.
6. Maintain a healthy sleep schedule.
7. Review your mistakes and learn from them.
""")
    st.caption(
        "AI guidance is based on the information you entered. "
        "It is intended for educational support."
    )
    # =========================================================
# PREDICTION HISTORY
# =========================================================
def history_page():
    st.title("📜 Prediction History")
    history = get_history()

    if history.empty:
        st.info("No prediction history available.")
        return

    st.dataframe(
        history.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True
    )

    csv_data = history.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Prediction History",
        data=csv_data,
        file_name="EduPredict_History.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.subheader("📈 Performance Trend")
    chart_data = history.iloc[::-1]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        range(1, len(chart_data) + 1),
        chart_data["Predicted Marks"],
        marker="o"
    )
    ax.set_ylim(0, 100)
    ax.set_title("Student Performance Trend")
    ax.set_xlabel("Prediction Number")
    ax.set_ylabel("Predicted Marks")
    fig.patch.set_facecolor("#160909")
    ax.set_facecolor("#160909")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    ax.grid(alpha=0.2)
    st.pyplot(fig)
    plt.close(fig)


# =========================================================
# ANALYTICS
# =========================================================
def analytics_page():
    st.title("📊 Performance Analytics")
    history = get_history()

    if history.empty:
        st.info("Make predictions first to view analytics.")
        return

    average = history["Predicted Marks"].mean()
    highest = history["Predicted Marks"].max()
    lowest = history["Predicted Marks"].min()

    c1, c2, c3 = st.columns(3)
    c1.metric("Average Marks", f"{average:.2f}")
    c2.metric("Highest Marks", f"{highest:.2f}")
    c3.metric("Lowest Marks", f"{lowest:.2f}")

    st.markdown("---")
    st.subheader("Performance Distribution")
    distribution = history["Performance"].value_counts()

    fig, ax = plt.subplots()
    ax.pie(
        distribution.values,
        labels=distribution.index,
        autopct="%1.1f%%",
        startangle=90
    )
    ax.set_title("Performance Categories")
    fig.patch.set_facecolor("#160909")
    ax.set_facecolor("#160909")
    ax.title.set_color("white")
    ax.tick_params(colors="white")
    st.pyplot(fig)
    plt.close(fig)


# =========================================================
# ABOUT PROJECT
# =========================================================
def about_page():
    st.title("ℹ️ About EduPredict")
    st.markdown("""
## 🎓 EduPredict

EduPredict is an AI-based Student Performance Prediction and Guidance System.
It estimates academic performance using Machine Learning and provides
personalized educational suggestions.

### ⚙️ Technologies Used
- Python
- Streamlit
- Pandas
- Scikit-learn
- Matplotlib
- SQLite

### 🧠 Machine Learning Algorithm
Linear Regression

### 📌 Project Features
- Student Marks Prediction
- AI Performance Review
- Personalized Advice
- Daily Study Plan
- Performance Analytics
- Prediction History
""")

    st.markdown("---")
    st.subheader("📊 Model Evaluation")
    c1, c2 = st.columns(2)
    c1.metric("Mean Absolute Error", f"{mae:.2f}")
    c2.metric("R² Score", f"{r2:.3f}")

    st.warning(
        "This project uses generated sample data for academic demonstration. "
        "Predictions and recommendations are estimates, not guaranteed "
        "examination results."
    )


# =========================================================
# MAIN APPLICATION
# =========================================================
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

with st.sidebar:
    st.title("🎓 EduPredict")
    st.markdown("---")
    st.caption("AI Student Performance Advisor")
    st.markdown("---")

    selected_page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "AI Prediction",
            "AI Review & Guidance",
            "Prediction History",
            "Analytics",
            "About Project"
        ]
    )

    st.markdown("---")
    st.markdown("**EduPredict v3.2**")
    st.caption("Powered by Machine Learning")

if selected_page == "Dashboard":
    dashboard_page()
elif selected_page == "AI Prediction":
    prediction_page()
elif selected_page == "AI Review & Guidance":
    review_page()
elif selected_page == "Prediction History":
    history_page()
elif selected_page == "Analytics":
    analytics_page()
elif selected_page == "About Project":
    about_page()