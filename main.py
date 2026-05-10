from fastapi import FastAPI, UploadFile, File
import io
from pydantic import BaseModel, Field
from typing import Literal, Optional
import joblib
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# Utility function to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


DB_NAME = "ogpredictions.db"


def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            marks INTEGER,
            accuracy INTEGER,
            time_taken INTEGER,
            attempts INTEGER,
            difficulty_level TEXT,
            topic_coverage INTEGER,
            consistency_score INTEGER,
            predicted_skill TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_students_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# Create FastAPI app
app = FastAPI(
    title="AI Skill Predictor API",
    description="A learning analytics API that predicts student skill levels using ML and provides AI-powered guidance.",
    version="1.0.0"
)

# SQLite database setup
create_table()
create_students_table()


# ==================================
# AUTH SCHEMAS & ENDPOINTS
# ==================================

class AdminAuth(BaseModel):
    username: str
    password: str


@app.post("/admin/login")
def admin_login(data: AdminAuth):
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        return {"message": "Admin login successful"}
    return {"error": "Invalid admin credentials"}


# ==================================
# DATABASE HELPERS
# ==================================

def save_prediction(data, predicted_skill):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions (
            name, marks, accuracy, time_taken, attempts,
            difficulty_level, topic_coverage, consistency_score,
            predicted_skill, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.name, data.marks, data.accuracy, data.time_taken,
        data.attempts, data.difficulty_level, data.topic_coverage,
        data.consistency_score, predicted_skill,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_history(limit: int = 50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, marks, accuracy, time_taken, attempts,
               difficulty_level, topic_coverage, consistency_score,
               predicted_skill, created_at
        FROM predictions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0], "name": r[1], "marks": r[2], "accuracy": r[3],
            "time_taken": r[4], "attempts": r[5], "difficulty_level": r[6],
            "topic_coverage": r[7], "consistency_score": r[8],
            "predicted_skill": r[9], "created_at": r[10]
        }
        for r in rows
    ]


def get_history_filtered(name: str = None, limit: int = 50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if name:
        cursor.execute("""
            SELECT id, name, marks, accuracy, time_taken, attempts,
                   difficulty_level, topic_coverage, consistency_score,
                   predicted_skill, created_at
            FROM predictions
            WHERE name = ?
            ORDER BY id DESC
            LIMIT ?
        """, (name, limit))
    else:
        cursor.execute("""
            SELECT id, name, marks, accuracy, time_taken, attempts,
                   difficulty_level, topic_coverage, consistency_score,
                   predicted_skill, created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0], "name": r[1], "marks": r[2], "accuracy": r[3],
            "time_taken": r[4], "attempts": r[5], "difficulty_level": r[6],
            "topic_coverage": r[7], "consistency_score": r[8],
            "predicted_skill": r[9], "created_at": r[10]
        }
        for r in rows
    ]


def get_user_progress(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT created_at, predicted_skill
        FROM predictions
        WHERE name = ?
        ORDER BY created_at ASC
    """, (name,))

    rows = cursor.fetchall()
    conn.close()

    return [{"date": r[0], "skill": r[1]} for r in rows]


def get_skill_distribution():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT predicted_skill, COUNT(*)
        FROM predictions
        GROUP BY predicted_skill
    """)

    rows = cursor.fetchall()
    conn.close()

    return {skill: count for skill, count in rows}


# ==================================
# ML PIPELINE
# ==================================

model = joblib.load("skill_model.pkl")
scaler = joblib.load("scaler.pkl")
difficulty_encoder = joblib.load("difficulty_encoder.pkl")


# ==================================
# INPUT SCHEMAS
# ==================================

class StudentAuth(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)


class SkillInput(BaseModel):
    name: str = Field(..., min_length=1)
    marks: int = Field(..., ge=0, le=100)
    accuracy: int = Field(..., ge=0, le=100)
    time_taken: int = Field(..., gt=0)
    attempts: int = Field(..., ge=1)
    difficulty_level: Literal["easy", "medium", "hard"]
    topic_coverage: int = Field(..., ge=0, le=100)
    consistency_score: int = Field(..., ge=0, le=100)


# ==================================
# ENDPOINTS
# ==================================

@app.get("/")
def home():
    return {"message": "AI Skill Predictor API is running"}


@app.post("/predict")
def predict_skill(data: SkillInput):
    input_df = pd.DataFrame([{
        "marks": data.marks,
        "accuracy": data.accuracy,
        "time_taken": data.time_taken,
        "attempts": data.attempts,
        "difficulty_level": data.difficulty_level,
        "topic_coverage": data.topic_coverage,
        "consistency_score": data.consistency_score
    }])

    input_df["difficulty_level"] = difficulty_encoder.transform(
        input_df["difficulty_level"]
    )

    input_scaled = scaler.transform(input_df)
    prediction = model.predict(input_scaled)
    predicted_skill = prediction[0]

    save_prediction(data, predicted_skill)

    return {
        "name": data.name,
        "predicted_skill_level": predicted_skill
    }


@app.post("/improvement-plan")
async def get_improvement_plan(data: SkillInput):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Gemini API key not configured."}

    prompt = f"""
You are a learning coach. A student just completed a test with these results:
- Marks: {data.marks}/100
- Accuracy: {data.accuracy}%
- Time taken: {data.time_taken} minutes
- Attempts: {data.attempts}
- Difficulty: {data.difficulty_level}
- Topic coverage: {data.topic_coverage}%
- Consistency score: {data.consistency_score}%

Give a short, practical 4-week improvement plan with specific weekly goals.
Be encouraging. Use bullet points. Keep it under 200 words.
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}",
                headers={"content-type": "application/json"},
                json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
            )
            result = response.json()

        if "candidates" in result and result["candidates"]:
            plan = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"plan": plan}
        else:
            return {"error": "No plan generated.", "raw": result}

    except httpx.TimeoutException:
        return {"error": "Request timed out."}
    except Exception as e:
        return {"error": str(e)}


@app.get("/history")
def fetch_history(limit: int = 50):
    return {"count": limit, "data": get_history(limit)}


@app.get("/analytics/skills")
def skill_analytics():
    return get_skill_distribution()


@app.get("/history/filter")
def fetch_history_filtered(name: str = None, limit: int = 50):
    return {"name": name, "count": limit, "data": get_history_filtered(name, limit)}


@app.get("/progress")
def user_progress(name: str):
    return {"name": name, "progress": get_user_progress(name)}


@app.post("/student/register")
def register_student(data: StudentAuth):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO students (username, password_hash, created_at)
            VALUES (?, ?, ?)
        """, (
            data.username,
            hash_password(data.password),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return {"message": "Student registered successfully"}

    except sqlite3.IntegrityError:
        return {"error": "Username already exists"}

    finally:
        conn.close()


@app.post("/student/login")
def login_student(data: StudentAuth):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password_hash FROM students WHERE username = ?
    """, (data.username,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": "User not found"}

    if row[0] != hash_password(data.password):
        return {"error": "Invalid password"}

    return {"message": "Login successful", "username": data.username}


# ==================================
# BATCH PREDICTION
# ==================================

@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    contents = await file.read()

    try:
        df_input = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        return {"error": f"Could not read CSV: {str(e)}"}

    required_cols = [
        "marks", "accuracy", "time_taken", "attempts",
        "difficulty_level", "topic_coverage", "consistency_score"
    ]
    missing = [c for c in required_cols if c not in df_input.columns]
    if missing:
        return {"error": f"Missing columns: {missing}"}

    valid_difficulty = ["easy", "medium", "hard"]
    invalid_rows = df_input[~df_input["difficulty_level"].isin(valid_difficulty)]
    if not invalid_rows.empty:
        return {"error": "Invalid difficulty_level values found. Must be: easy, medium, hard"}

    try:
        df_input["difficulty_level_encoded"] = difficulty_encoder.transform(
            df_input["difficulty_level"]
        )

        features = df_input[[
            "marks", "accuracy", "time_taken", "attempts",
            "difficulty_level_encoded", "topic_coverage", "consistency_score"
        ]].copy()
        features.columns = [
            "marks", "accuracy", "time_taken", "attempts",
            "difficulty_level", "topic_coverage", "consistency_score"
        ]

        features_scaled = scaler.transform(features)
        predictions = model.predict(features_scaled)

        df_result = df_input[required_cols].copy()
        df_result["predicted_skill"] = predictions

        return {
            "total": len(df_result),
            "results": df_result.to_dict(orient="records")
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}


# ==================================
# AI CHAT ASSISTANT
# ==================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    student_name: str
    message: str
    history: list[ChatMessage] = []


def get_student_context(name: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT marks, accuracy, time_taken, attempts,
               difficulty_level, topic_coverage, consistency_score,
               predicted_skill, created_at
        FROM predictions
        WHERE name = ?
        ORDER BY id DESC
        LIMIT 1
    """, (name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "marks": row[0], "accuracy": row[1], "time_taken": row[2],
        "attempts": row[3], "difficulty_level": row[4],
        "topic_coverage": row[5], "consistency_score": row[6],
        "predicted_skill": row[7], "created_at": row[8],
    }


def get_student_history_summary(name: str) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT predicted_skill, created_at
        FROM predictions
        WHERE name = ?
        ORDER BY id ASC
    """, (name,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No previous predictions found."

    return "\n".join([f"  - {r[1]}: {r[0]}" for r in rows])


def build_system_prompt(student_name: str) -> str:
    ctx = get_student_context(student_name)
    history_summary = get_student_history_summary(student_name)

    if ctx:
        latest_block = f"""
Most recent test result for {student_name}:
- Marks: {ctx['marks']}/100
- Accuracy: {ctx['accuracy']}%
- Time taken: {ctx['time_taken']} minutes
- Attempts: {ctx['attempts']}
- Difficulty level: {ctx['difficulty_level']}
- Topic coverage: {ctx['topic_coverage']}%
- Consistency score: {ctx['consistency_score']}%
- Predicted skill level: {ctx['predicted_skill']}
- Recorded at: {ctx['created_at']}

Skill progression history:
{history_summary}
"""
    else:
        latest_block = f"No prediction data found yet for {student_name}."

    return f"""You are an intelligent learning assistant inside the AI Skill Predictor Tool.
You are talking to a student named {student_name}.

Your job is to:
1. Explain their predicted skill level clearly and encouragingly
2. Identify which specific metrics are holding them back
3. Give concrete, actionable study tips based on their actual scores
4. Answer any questions about their performance honestly but supportively
5. Suggest a weekly improvement plan if asked

Here is their data:
{latest_block}

Tone: supportive, clear, and practical. Never make the student feel bad.
Keep responses concise — 3 to 5 sentences unless they ask for a detailed plan.
Do not mention that you are Claude or an AI model by Anthropic. You are the AI assistant of this platform.
"""


@app.post("/chat")
async def chat_with_ai(data: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Gemini API key not configured."}

    system_prompt = build_system_prompt(data.student_name)

    messages = [{"role": m.role, "content": m.content} for m in data.history]
    messages.append({"role": "user", "content": data.message})

    all_messages = [
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "Understood. I am ready to help."}]}
    ]

    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        all_messages.append({"role": role, "parts": [{"text": m["content"]}]})

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}",
                headers={"content-type": "application/json"},
                json={"contents": all_messages}
            )
            result = response.json()

        if "candidates" in result and result["candidates"]:
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"reply": reply}
        else:
            return {"error": "No response from AI.", "raw": result}

    except httpx.TimeoutException:
        return {"error": "AI assistant timed out. Please try again."}
    except Exception as e:
        return {"error": f"AI assistant error: {str(e)}"}