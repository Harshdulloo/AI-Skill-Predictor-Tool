import streamlit as st
import requests
import pandas as pd

# ==================================
# PAGE CONFIG (MUST BE FIRST)
# ==================================
st.set_page_config(
    page_title="AI Skill Predictor",
    page_icon="🧠",
    layout="centered"
)

try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except:
    BACKEND_URL = "http://127.0.0.1:8000"

# ==================================
# SESSION STATE INIT
# ==================================
if "student_logged_in" not in st.session_state:
    st.session_state.student_logged_in = False
    st.session_state.student_name = None

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==================================
# AUTH GUARDS
# ==================================
def require_student_login():
    if not st.session_state.student_logged_in:
        st.warning("⚠️ Student login required.")
        st.stop()

def require_admin_login():
    if not st.session_state.admin_logged_in:
        st.warning("⚠️ Admin login required.")
        st.stop()

# ==================================
# ROLE-BASED SIDEBAR
# ==================================
st.sidebar.title("Navigation")

# CASE 1: No one is logged in (PUBLIC)
if not st.session_state.student_logged_in and not st.session_state.admin_logged_in:
    menu = st.sidebar.radio(
        "Menu",
        ["Project Overview", "Student Login", "Admin Login"]
    )

# CASE 2: Student logged in
elif st.session_state.student_logged_in:
    menu = st.sidebar.radio(
        "Student Menu",
        ["Skill Prediction", "My History", "My Progress", "AI Assistant"]
    )

# CASE 3: Admin logged in
elif st.session_state.admin_logged_in:
    menu = st.sidebar.radio(
        "Admin Menu",
        ["Admin Overview", "Student Analytics", "Batch Prediction"]
    )

# ==================================
# PROJECT OVERVIEW (PUBLIC HOME PAGE)
# ==================================
if menu == "Project Overview":

    st.title("AI Skill Predictor Tool")

    st.subheader("Project Overview")

    st.write(
        """
        The AI Skill Predictor Tool is a learning analytics application designed
        to evaluate and track a student's skill level based on test performance
        and behavioral patterns.
        """
    )

    st.write(
        """
        This system uses machine learning to analyze multiple performance factors
        and predicts a skill level as Beginner, Intermediate, or Advanced.
        """
    )

    st.divider()

    st.subheader("What this project does")

    st.markdown(
        """
        - Allows students to register and log in securely
        - Predicts a student's skill level using an AI model
        - Stores predictions in a database for future analysis
        - Shows students their personal history and progress
        - Provides administrators with a complete analytics dashboard
        """
    )

    st.divider()

    st.subheader("How the prediction works")

    st.markdown(
        """
        The system evaluates multiple performance indicators, including:
        - Accuracy of answers
        - Difficulty level of the test
        - Consistency in performance
        - Number of attempts required
        - Time taken to complete the test
        """
    )

    st.write(
        """
        Based on these inputs, the machine learning model identifies patterns
        and predicts the most suitable skill level.
        """
    )

    st.divider()

    st.subheader("Student features")

    st.markdown(
        """
        - Predict skill level
        - AI-powered personalized improvement plan
        - AI Learning Assistant for skill guidance
        - View personal prediction history
        - Track skill progress over time
        - Access only personal data
        """
    )

    st.divider()

    st.subheader("Admin features")

    st.markdown(
        """
        - View all student predictions
        - Analyze overall skill distribution
        - Identify top-performing students
        - Analyze individual student performance
        - Batch CSV prediction for entire class
        - Export prediction data for reporting
        """
    )

    st.divider()

    st.subheader("Technologies used")

    st.markdown(
        """
        - Frontend: Streamlit  
        - Backend: FastAPI  
        - Database: SQLite  
        - Machine Learning: Scikit-learn  
        - AI Assistant: Google Gemini API  
        - Data Analysis and Visualization: Pandas, Plotly  
        """
    )

    st.divider()

    st.subheader("Project goal")

    st.write(
        """
        The goal of this project is to demonstrate how artificial intelligence,
        data analytics, and full-stack development can be combined to build
        a practical, secure, and scalable learning evaluation system.
        """
    )

    st.info("Use the sidebar to log in as a student or admin to continue.")


elif menu == "Student Login":
    st.title("👤 Student Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            res = requests.post(
                f"{BACKEND_URL}/student/login",
                json={"username": username, "password": password}
            ).json()

            if "message" in res:
                st.session_state.student_logged_in = True
                st.session_state.student_name = res["username"]
                st.success("Login successful")
                st.rerun()
            else:
                st.error(res["error"])

    with col2:
        if st.button("Register"):
            res = requests.post(
                f"{BACKEND_URL}/student/register",
                json={"username": username, "password": password}
            ).json()

            if "message" in res:
                st.success("Registered successfully. Please login.")
            else:
                st.error(res["error"])

# ==================================
# ADMIN LOGIN
# ==================================
elif menu == "Admin Login":
    st.title("🔐 Admin Login")

    u = st.text_input("Admin Username")
    p = st.text_input("Admin Password", type="password")

    if st.button("Login as Admin"):
        res = requests.post(
            f"{BACKEND_URL}/admin/login",
            json={"username": u, "password": p}
        ).json()

        if "message" in res:
            st.session_state.admin_logged_in = True
            st.success("Admin login successful")
            st.rerun()
        else:
            st.error("Invalid admin credentials")

# ==================================
# SKILL PREDICTION (STUDENT)
# ==================================
elif menu == "Skill Prediction":
    require_student_login()

    st.title("🧠 Skill Prediction")
    st.caption(f"Logged in as **{st.session_state.student_name}**")

    with st.form("predict_form"):
        marks = st.number_input("Marks", 0, 100, 70)
        accuracy = st.number_input("Accuracy (%)", 0, 100, 75)
        time_taken = st.number_input("Time Taken (minutes)", 1, 120, 30)
        attempts = st.number_input("Attempts", 1, 10, 2)
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        topic = st.number_input("Topic Coverage (%)", 0, 100, 80)
        consistency = st.number_input("Consistency Score (%)", 0, 100, 75)

        submit = st.form_submit_button("Predict")

    if submit:
        payload = {
            "name": st.session_state.student_name,
            "marks": marks,
            "accuracy": accuracy,
            "time_taken": time_taken,
            "attempts": attempts,
            "difficulty_level": difficulty,
            "topic_coverage": topic,
            "consistency_score": consistency
        }

        res = requests.post(
            f"{BACKEND_URL}/predict",
            json=payload
        ).json()

        st.success(f"Predicted Skill Level: **{res['predicted_skill_level']}**")

        # Store payload for improvement plan button
        st.session_state.last_prediction_payload = payload
        st.session_state.show_plan_button = True

# Show improvement plan button after prediction
if st.session_state.get("show_plan_button") and menu == "Skill Prediction":

    if st.button("📋 Get my improvement plan"):
        with st.spinner("Generating your personalized plan..."):
            plan_res = requests.post(
                f"{BACKEND_URL}/improvement-plan",
                json=st.session_state.last_prediction_payload
            ).json()

            if "plan" in plan_res:
                st.markdown("### 📚 Your 4-Week Improvement Plan")
                st.markdown(plan_res["plan"])
            else:
                st.error(plan_res.get("error", "Something went wrong."))

# ==================================
# MY HISTORY (STUDENT)
# ==================================
elif menu == "My History":
    require_student_login()

    st.title("📜 My History")

    res = requests.get(
        f"{BACKEND_URL}/history/filter",
        params={"name": st.session_state.student_name}
    ).json()

    df = pd.DataFrame(res["data"])
    st.dataframe(df, use_container_width=True)

# ==================================
# MY PROGRESS (STUDENT)
# ==================================
elif menu == "My Progress":
    require_student_login()

    st.title("📈 My Progress")

    res = requests.get(
        f"{BACKEND_URL}/progress",
        params={"name": st.session_state.student_name}
    ).json()

    df = pd.DataFrame(res["progress"])

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["skill_value"] = df["skill"].map({
            "Beginner": 1,
            "Intermediate": 2,
            "Advanced": 3
        })
        st.line_chart(df.set_index("date")["skill_value"])

# ==================================
# ADMIN OVERVIEW DASHBOARD
# ==================================
elif menu == "Admin Overview":
    require_admin_login()

    st.title("🛠 Admin Overview Dashboard")

    res = requests.get(f"{BACKEND_URL}/history").json()
    df = pd.DataFrame(res["data"])

    if df.empty:
        st.info("No data available.")
    else:
        # ---------------- KPIs ----------------
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Predictions", len(df))
        col2.metric("Total Students", df["name"].nunique())
        col3.metric("Avg Consistency", round(df["consistency_score"].mean(), 2))

        st.divider()

        # ---------------- SKILL DISTRIBUTION ----------------
        st.subheader("🎯 Skill Distribution (Overall)")

        skill_counts = df["predicted_skill"].value_counts()

        donut_df = pd.DataFrame({
            "Skill": skill_counts.index,
            "Count": skill_counts.values
        })

        st.plotly_chart(
            {
                "data": [{
                    "labels": donut_df["Skill"],
                    "values": donut_df["Count"],
                    "type": "pie",
                    "hole": 0.4
                }],
                "layout": {
                    "title": "Skill Level Proportion"
                }
            },
            use_container_width=True
        )

        # ---------------- DIFFICULTY VS SKILL ----------------
        st.subheader("📘 Difficulty vs Skill Outcome")

        pivot = pd.crosstab(
            df["difficulty_level"],
            df["predicted_skill"]
        )

        st.dataframe(pivot, use_container_width=True)
        st.bar_chart(pivot)

        # ---------------- CONSISTENCY VS SKILL ----------------
        st.subheader("📊 Consistency Score Distribution by Skill")

        st.plotly_chart(
            {
                "data": [
                    {
                        "y": df[df["predicted_skill"] == skill]["consistency_score"],
                        "type": "box",
                        "name": skill
                    }
                    for skill in df["predicted_skill"].unique()
                ],
                "layout": {
                    "title": "Consistency Score vs Skill Level",
                    "yaxis": {"title": "Consistency Score"}
                }
            },
            use_container_width=True
        )

        # ---------------- LEADERBOARD ----------------
        st.subheader("🏆 Leaderboard (Top Consistent Students)")
        leaderboard = (
            df.groupby("name")["consistency_score"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
        )
        st.dataframe(leaderboard.reset_index(name="Avg Consistency Score"))

        # ---------------- MONTHLY TREND ----------------
        st.subheader("📅 Monthly Skill Improvement Trend")
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["month"] = df["created_at"].dt.to_period("M").astype(str)
        monthly = df.groupby("month").size()
        st.line_chart(monthly)

        # ---------------- CSV EXPORT ----------------
        st.subheader("⬇️ Export Data")
        st.download_button(
            "Download Predictions CSV",
            data=df.to_csv(index=False),
            file_name="predictions.csv",
            mime="text/csv"
        )

        st.divider()
        st.subheader("📜 All Predictions")
        st.dataframe(df, use_container_width=True)

# ==================================
# STUDENT ANALYTICS (ADMIN)
# ==================================
elif menu == "Student Analytics":
    require_admin_login()

    st.title("🔎 Student Analytics")

    student_name = st.text_input("Enter student username")

    if st.button("Load Student Analytics"):
        if not student_name.strip():
            st.warning("Please enter a student name.")
        else:
            res = requests.get(
                f"{BACKEND_URL}/history/filter",
                params={"name": student_name}
            ).json()

            df = pd.DataFrame(res["data"])

            if df.empty:
                st.info("No data found for this student.")
            else:
                st.subheader("📜 Prediction History")
                st.dataframe(df, use_container_width=True)

                st.subheader("📊 Skill Distribution")
                st.bar_chart(df["predicted_skill"].value_counts())

                st.subheader("📈 Skill Progress")
                df["created_at"] = pd.to_datetime(df["created_at"])
                df["skill_value"] = df["predicted_skill"].map({
                    "Beginner": 1,
                    "Intermediate": 2,
                    "Advanced": 3
                })
                st.line_chart(df.set_index("created_at")["skill_value"])

# ==================================
# BATCH PREDICTION (ADMIN)
# ==================================
elif menu == "Batch Prediction":
    require_admin_login()

    st.title("📂 Batch Skill Prediction")
    st.write("Upload a CSV file to predict skill levels for multiple students at once.")

    # ---------- Download sample CSV ----------
    sample_data = pd.DataFrame([
        {
            "marks": 78, "accuracy": 82, "time_taken": 28,
            "attempts": 1, "difficulty_level": "hard",
            "topic_coverage": 85, "consistency_score": 80
        },
        {
            "marks": 45, "accuracy": 50, "time_taken": 55,
            "attempts": 4, "difficulty_level": "easy",
            "topic_coverage": 60, "consistency_score": 40
        },
        {
            "marks": 60, "accuracy": 65, "time_taken": 35,
            "attempts": 2, "difficulty_level": "medium",
            "topic_coverage": 70, "consistency_score": 65
        },
    ])

    st.download_button(
        "⬇️ Download Sample CSV Template",
        data=sample_data.to_csv(index=False),
        file_name="sample_batch.csv",
        mime="text/csv"
    )

    st.divider()

    # ---------- File uploader ----------
    uploaded_file = st.file_uploader(
        "Upload your CSV file",
        type=["csv"],
        help="CSV must have columns: marks, accuracy, time_taken, attempts, difficulty_level, topic_coverage, consistency_score"
    )

    if uploaded_file:
        # Show preview
        preview_df = pd.read_csv(uploaded_file)
        st.subheader("📋 Preview")
        st.dataframe(preview_df.head(10), use_container_width=True)
        st.caption(f"Total rows: {len(preview_df)}")

        # Reset file pointer
        uploaded_file.seek(0)

        if st.button("🚀 Run Batch Prediction"):
            with st.spinner(f"Predicting skill levels for {len(preview_df)} students..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/predict/batch",
                        files={"file": ("batch.csv", uploaded_file, "text/csv")}
                    ).json()

                    if "error" in res:
                        st.error(f"Error: {res['error']}")
                    else:
                        results_df = pd.DataFrame(res["results"])

                        st.success(f"✅ Predicted {res['total']} students successfully!")

                        # ---------- Skill distribution ----------
                        st.subheader("🎯 Skill Distribution")
                        skill_counts = results_df["predicted_skill"].value_counts()
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Beginner", skill_counts.get("Beginner", 0))
                        col2.metric("Intermediate", skill_counts.get("Intermediate", 0))
                        col3.metric("Advanced", skill_counts.get("Advanced", 0))
                        st.bar_chart(skill_counts)

                        # ---------- Results table ----------
                        st.subheader("📊 Full Results")
                        st.dataframe(results_df, use_container_width=True)

                        # ---------- Download results ----------
                        st.download_button(
                            "⬇️ Download Results CSV",
                            data=results_df.to_csv(index=False),
                            file_name="batch_predictions.csv",
                            mime="text/csv"
                        )

                except Exception as e:
                    st.error(f"Could not reach backend: {e}")

# ==================================
# AI ASSISTANT (STUDENT)
# ==================================
elif menu == "AI Assistant":
    st.session_state.show_plan_button = False
    require_student_login()

    st.title("AI Learning Assistant")
    st.caption(f"Logged in as **{st.session_state.student_name}**")

    st.write(
        "Ask me anything about your skill level, what to improve, "
        "or what to study next. I have access to your prediction history."
    )

    # ---- Session state for chat history ----
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ---- Render existing messages ----
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ---- Suggested starter questions (shown only at start) ----
    if not st.session_state.chat_history:
        st.markdown("**Try asking:**")
        cols = st.columns(2)
        starters = [
            "Why did I get this skill level?",
            "What should I focus on this week?",
            "How can I improve my consistency score?",
            "Give me a 4-week study plan.",
        ]
        for i, q in enumerate(starters):
            if cols[i % 2].button(q, key=f"starter_{i}"):
                st.session_state._pending_message = q
                st.rerun()

    # ---- Handle a starter button click ----
    pending = st.session_state.pop("_pending_message", None)

    # ---- Chat input ----
    user_input = st.chat_input("Ask about your performance...")

    # Use either typed input or button-triggered input
    final_input = user_input or pending

    if final_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.write(final_input)

        # Build history payload for backend (last 10 turns to stay within context)
        history_payload = st.session_state.chat_history[-10:]

        # Call /chat endpoint
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/chat",
                        json={
                            "student_name": st.session_state.student_name,
                            "message": final_input,
                            "history": history_payload,
                        }
                    ).json()

                    if "reply" in res:
                        reply = res["reply"]
                        st.write(reply)
                    else:
                        reply = f"Sorry, something went wrong: {res.get('error', 'Unknown error')}"
                        st.error(reply)

                except Exception as e:
                    reply = f"Could not reach the AI assistant: {e}"
                    st.error(reply)

        # Save both turns to history
        st.session_state.chat_history.append({"role": "user", "content": final_input})
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # ---- Clear chat button ----
    if st.session_state.chat_history:
        st.divider()
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()

# ==================================
# LOGOUTS
# ==================================
st.sidebar.markdown("---")

if st.session_state.student_logged_in:
    if st.sidebar.button("🚪 Student Logout"):
        st.session_state.student_logged_in = False
        st.session_state.student_name = None
        st.rerun()

if st.session_state.admin_logged_in:
    if st.sidebar.button("🚪 Admin Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()