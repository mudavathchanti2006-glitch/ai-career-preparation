from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ==========================================================
# GEMINI AI
# ==========================================================

try:
    from google import genai
except ImportError:
    genai = None


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "ai-career-preparation-secret-key-change-this"
)


# ==========================================================
# GEMINI CONFIGURATION
# ==========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = None

if genai is not None and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
        print("Gemini AI configured successfully.")

    except Exception as e:
        print("Gemini initialization error:", e)

else:
    print("Gemini AI is not configured.")
    print("Set GEMINI_API_KEY before using the AI Assistant.")


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DATABASE = "project.db"


# ==========================================================
# SQLITE DATABASE WRAPPERS
# ==========================================================

class SQLiteCursorWrapper:

    def __init__(self, conn, dictionary=False):
        self.conn = conn
        self.cursor = conn.cursor()
        self.dictionary = dictionary

    def execute(self, query, params=None):

        # Convert MySQL-style placeholders to SQLite placeholders
        query = query.replace("%s", "?")

        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchone(self):

        row = self.cursor.fetchone()

        if row is None:
            return None

        if self.dictionary:
            columns = [description[0] for description in self.cursor.description]
            return dict(zip(columns, row))

        return row

    def fetchall(self):

        rows = self.cursor.fetchall()

        if not self.dictionary:
            return rows

        columns = [description[0] for description in self.cursor.description]

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    def close(self):
        self.cursor.close()


class SQLiteConnectionWrapper:

    def __init__(self, db_path):
        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

    def cursor(self, dictionary=False):
        return SQLiteCursorWrapper(
            self.conn,
            dictionary
        )

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


# ==========================================================
# GET DATABASE CONNECTION
# ==========================================================

def get_db_connection():

    try:
        return SQLiteConnectionWrapper(DATABASE)

    except Exception as e:

        print("Database connection error:", e)

        return None


# ==========================================================
# CREATE DATABASE
# ==========================================================

def create_database():

    try:

        conn = sqlite3.connect(DATABASE)

        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                education TEXT,
                skills TEXT,
                career_goal TEXT
            )
        """)

        conn.commit()
        conn.close()

        print("Database initialized successfully.")

    except Exception as e:

        print("Database initialization error:", e)


create_database()


# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        education = request.form.get(
            "education",
            ""
        ).strip()

        skills = request.form.get(
            "skills",
            ""
        ).strip()

        career_goal = request.form.get(
            "career_goal",
            ""
        ).strip()

        # Validation

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill all required fields."
            )

        connection = get_db_connection()

        if connection is None:

            return render_template(
                "register.html",
                error="Database connection failed."
            )

        cursor = connection.cursor()

        try:

            # Check whether email already exists

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                return render_template(
                    "register.html",
                    error="Email already registered."
                )

            # Hash password

            hashed_password = generate_password_hash(
                password
            )

            # Insert user

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    education,
                    skills,
                    career_goal
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    hashed_password,
                    education,
                    skills,
                    career_goal
                )
            )

            connection.commit()

            return redirect(
                url_for("login")
            )

        except Exception as e:

            connection.rollback()

            print(
                "Registration error:",
                e
            )

            return render_template(
                "register.html",
                error="Registration failed. Please try again."
            )

        finally:

            cursor.close()
            connection.close()

    return render_template(
        "register.html"
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            return render_template(
                "login.html",
                error="Enter email and password."
            )

        connection = get_db_connection()

        if connection is None:

            return render_template(
                "login.html",
                error="Database connection failed."
            )

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if user is None:

                return render_template(
                    "login.html",
                    error="Invalid email or password."
                )

            if not check_password_hash(
                user["password"],
                password
            ):

                return render_template(
                    "login.html",
                    error="Invalid email or password."
                )

            # Create session

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            # Clear old chat history when logging in

            session["chat_history"] = []

            return redirect(
                url_for("dashboard")
            )

        except Exception as e:

            print(
                "Login error:",
                e
            )

            return render_template(
                "login.html",
                error="Login failed. Please try again."
            )

        finally:

            cursor.close()
            connection.close()

    return render_template(
        "login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",
        user_name=session.get(
            "user_name",
            "Student"
        )
    )


# ==========================================================
# CODING PRACTICE
# ==========================================================

@app.route("/coding-practice")
def coding_practice():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "coding_practice.html"
    )


# ==========================================================
# AI CAREER ASSISTANT PAGE
# ==========================================================

@app.route("/ai-assistant")
def ai_career_assistant():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "ai_assistant.html"
    )


# ==========================================================
# AI CHAT API
# ==========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():

    # Check login

    if "user_id" not in session:

        return jsonify({
            "answer": "Please login before using the AI Career Assistant."
        }), 401

    # Check Gemini configuration

    if gemini_client is None:

        return jsonify({
            "answer": (
                "Gemini AI is not configured. "
                "Please set GEMINI_API_KEY and restart Flask."
            )
        }), 500

    # Read JSON request

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "answer": "Please send a question."
        }), 400

    user_message = data.get(
        "message",
        ""
    ).strip()

    if not user_message:

        return jsonify({
            "answer": "Please type a question."
        }), 400

    # ======================================================
    # GET STUDENT INFORMATION
    # ======================================================

    connection = get_db_connection()

    student_info = ""

    if connection:

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT
                    name,
                    email,
                    education,
                    skills,
                    career_goal
                FROM users
                WHERE id = %s
                """,
                (session["user_id"],)
            )

            user = cursor.fetchone()

            if user:

                student_info = f"""
Student Information:

Name: {user.get("name", "")}
Education: {user.get("education", "")}
Skills: {user.get("skills", "")}
Career Goal: {user.get("career_goal", "")}
"""

        except Exception as e:

            print(
                "Student information error:",
                e
            )

        finally:

            cursor.close()
            connection.close()

    # ======================================================
    # AI SYSTEM INSTRUCTION
    # ======================================================

    system_instruction = """
You are an intelligent AI assistant inside an application
called AI Career Preparation System.

You should behave like a helpful general-purpose AI assistant.

You can answer questions about:

- Programming
- Python
- Java
- JavaScript
- C
- C++
- HTML
- CSS
- SQL
- Databases
- Flask
- Web development
- Artificial Intelligence
- Machine Learning
- Data Science
- Cloud Computing
- Cyber Security
- Software Engineering
- Projects
- Resume preparation
- Interviews
- Career planning
- College subjects
- Learning roadmaps
- General educational questions

Answer the user's actual question directly.

For coding questions:
- Explain clearly.
- Give working examples when useful.
- Keep code properly formatted.
- Explain errors in simple language.

For career questions:
- Give practical advice.
- Give step-by-step roadmaps.
- Recommend useful skills and projects.

For interview questions:
- Provide questions and answers.
- Include technical and HR questions.

Use simple language suitable for a college student.

Do not claim that you performed an action when you did not.

If the question is unrelated to careers, education, or technology,
you may still answer it normally because this assistant supports
general questions.

Student information is provided only to personalize answers
when useful.
"""

    # ======================================================
    # CONVERSATION HISTORY
    # ======================================================

    history = session.get("chat_history", [])
    recent_history = history[-8:]

    # Build conversation context string from history
    conversation_context = ""
    for item in recent_history:
        role_label = "User" if item["role"] == "user" else "Assistant"
        conversation_context += f"\n{role_label}: {item['text']}"

    # ======================================================
    # CURRENT QUESTION — single user turn (avoids alternation issues)
    # ======================================================

    final_prompt = (
        system_instruction
        + "\n\n"
        + student_info
    )

    if conversation_context:
        final_prompt += (
            "\n\nPrevious conversation:"
            + conversation_context
        )

    final_prompt += (
        "\n\nUser's current question:\n"
        + user_message
    )

    contents = [
        {
            "role": "user",
            "parts": [{"text": final_prompt}]
        }
    ]

    # ======================================================
    # CALL GEMINI
    # ======================================================

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents
        )

        answer = getattr(
            response,
            "text",
            None
        )

        if not answer:

            answer = (
                "Sorry, I could not generate an answer."
            )

        # Save user message

        history.append({
            "role": "user",
            "text": user_message
        })

        # Save AI response

        history.append({
            "role": "model",
            "text": answer
        })

        # Keep only recent messages

        session["chat_history"] = history[-10:]

        session.modified = True

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        print(
            "Gemini API error:",
            e
        )

        return jsonify({
            "answer": (
                "I could not connect to the AI service. "
                "Please check your Gemini API key, model name, "
                "internet connection, and try again."
            )
        }), 500


# ==========================================================
# CLEAR AI CHAT
# ==========================================================

@app.route(
    "/api/clear-chat",
    methods=["POST"]
)
def clear_chat():

    if "user_id" not in session:

        return jsonify({
            "message": "Please login."
        }), 401

    session["chat_history"] = []

    session.modified = True

    return jsonify({
        "message": "Chat history cleared successfully."
    })


# ==========================================================
# CAREER
# ==========================================================

@app.route("/career")
def career():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "career_recommendation.html"
    )


# ==========================================================
# ASSESSMENT
# ==========================================================

@app.route("/assessment")
def assessment():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "assessment.html"
    )


# ==========================================================
# INTERVIEW
# ==========================================================

@app.route("/interview")
def interview():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "interview.html"
    )


# ==========================================================
# RESUME ANALYZER
# ==========================================================

@app.route("/resume-analyzer", methods=["GET", "POST"])
def resume_analyzer():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Provide dummy data since no backend parser is currently implemented
        return render_template(
            "resume_analyzer.html",
            analyzed=True,
            score=85,
            career="Software Engineer",
            skills=["Python", "Flask", "SQL", "HTML", "CSS"],
            word_count=450,
            suggestions=[
                "Add more quantifiable achievements.",
                "Include a link to your GitHub portfolio.",
                "Use stronger action verbs in your experience section."
            ]
        )

    return render_template(
        "resume_analyzer.html"
    )


# ==========================================================
# RESULT
# ==========================================================

@app.route("/result")
def result():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "result.html"
    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/health")
def health():

    database_status = False

    connection = get_db_connection()

    if connection:

        database_status = True

        connection.close()

    return jsonify({
        "application": "AI Career Preparation System",
        "flask": "running",
        "database": (
            "connected"
            if database_status
            else "not connected"
        ),
        "gemini": (
            "configured"
            if gemini_client
            else "not configured"
        )
    })


# ==========================================================
# 404 ERROR
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    <a href="/">Go Home</a>
    """, 404


# ==========================================================
# 500 ERROR
# ==========================================================

@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Server Error</h1>
    <p>Something went wrong on the server.</p>
    <a href="/">Go Home</a>
    """, 500


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    print("")
    print("=" * 60)
    print("AI CAREER PREPARATION SYSTEM")
    print("=" * 60)
    print("")

    print("Home: http://127.0.0.1:5000/")
    print("Login: http://127.0.0.1:5000/login")
    print("Register: http://127.0.0.1:5000/register")
    print("Dashboard: http://127.0.0.1:5000/dashboard")
    print("Coding Practice: http://127.0.0.1:5000/coding-practice")
    print("AI Assistant: http://127.0.0.1:5000/ai-assistant")
    print("Health: http://127.0.0.1:5000/health")

    print("")

    print(
        "Database:",
        DATABASE
    )

    print(
        "Gemini:",
        "Configured"
        if gemini_client
        else "NOT CONFIGURED"
    )

    print("")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
        use_reloader=False
    )
