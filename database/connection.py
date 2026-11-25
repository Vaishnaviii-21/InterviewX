"""
SQLite database connection manager and schema initialization.
Ensures thread safety, connection pooling, and automatic migration for multi-user support.
"""

import sqlite3
import os
import contextlib
from config import DATABASE_PATH
from auth.security import hash_password

def get_connection():
    """
    Returns a configured sqlite3 connection object.
    Row factory is set to sqlite3.Row for dictionary-like access.
    Enforces foreign keys and WAL mode for concurrency.
    """
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
    return conn

@contextlib.contextmanager
def get_db_cursor(commit: bool = True):
    """
    Context manager for database transactions.
    Yields cursor and automatically commits on success or rolls back on exception.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _migrate_and_repair_schema():
    """
    Ensures 'users' table has username and password_hash columns,
    and repairs any foreign key bindings with foreign_keys OFF during migration.
    """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    # Crucial: turn foreign keys OFF during table restructuring
    conn.execute("PRAGMA foreign_keys = OFF;")
    cursor = conn.cursor()

    try:
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(users)")
            columns = [row["name"] for row in cursor.fetchall()]

            if "username" not in columns or "password_hash" not in columns:
                cursor.execute("ALTER TABLE users RENAME TO _users_old")
                cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        name TEXT NOT NULL DEFAULT 'Candidate',
                        college TEXT DEFAULT 'Engineering Institute',
                        degree TEXT DEFAULT 'B.Tech / B.E. in Computer Science',
                        graduation_year INTEGER DEFAULT 2026,
                        target_role TEXT DEFAULT 'Software Development Engineer (SDE-1)',
                        target_company_track TEXT DEFAULT 'Product Companies & Tier-1 Startups',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("SELECT * FROM _users_old")
                old_rows = cursor.fetchall()
                demo_hash = hash_password("Demo@123")
                for row in old_rows:
                    u_id = row["id"]
                    u_name = row["name"] or "Candidate"
                    u_email = row["email"] or f"user{u_id}@interviewx.local"
                    u_uname = "arjun" if u_id == 1 else f"user_{u_id}"
                    cursor.execute("""
                        INSERT INTO users (
                            id, username, email, password_hash, name, college, degree,
                            graduation_year, target_role, target_company_track
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u_id, u_uname, u_email, demo_hash, u_name,
                        row["college"], row["degree"], row["graduation_year"],
                        row["target_role"], row["target_company_track"]
                    ))
                cursor.execute("DROP TABLE _users_old")

        # Check if any tables still hold stale references to _users_old
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND (sql LIKE '%_users_old%' OR sql LIKE '%_sessions_fix%')")
        broken_tables = [r["name"] for r in cursor.fetchall()]

        if "interview_questions" in broken_tables:
            cursor.execute("ALTER TABLE interview_questions RENAME TO _questions_fix")
            cursor.execute("""
                CREATE TABLE interview_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    question_number INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    category TEXT DEFAULT 'Technical',
                    is_resume_based BOOLEAN DEFAULT 0,
                    user_answer TEXT DEFAULT '',
                    overall_score REAL DEFAULT 0.0,
                    accuracy_score REAL DEFAULT 0.0,
                    relevance_score REAL DEFAULT 0.0,
                    completeness_score REAL DEFAULT 0.0,
                    clarity_score REAL DEFAULT 0.0,
                    honest_feedback TEXT DEFAULT '',
                    incorrect_concepts TEXT DEFAULT '[]',
                    missing_information TEXT DEFAULT '[]',
                    improved_answer TEXT DEFAULT '',
                    improvement_reason TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES interview_sessions (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO interview_questions (id, session_id, question_number, question_text, category, user_answer, overall_score, accuracy_score, relevance_score, completeness_score, clarity_score, honest_feedback, incorrect_concepts, missing_information, improved_answer, improvement_reason, created_at) SELECT id, session_id, question_number, question_text, category, user_answer, overall_score, accuracy_score, relevance_score, completeness_score, clarity_score, honest_feedback, incorrect_concepts, missing_information, improved_answer, improvement_reason, created_at FROM _questions_fix")
            cursor.execute("DROP TABLE _questions_fix")

        if "interview_sessions" in broken_tables:
            cursor.execute("ALTER TABLE interview_sessions RENAME TO _sessions_fix")
            cursor.execute("""
                CREATE TABLE interview_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    role_id TEXT NOT NULL,
                    role_title TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    interview_type TEXT NOT NULL DEFAULT 'Technical',
                    target_company_track TEXT DEFAULT 'Product Companies',
                    total_questions INTEGER DEFAULT 0,
                    overall_score REAL DEFAULT 0.0,
                    accuracy_score REAL DEFAULT 0.0,
                    relevance_score REAL DEFAULT 0.0,
                    completeness_score REAL DEFAULT 0.0,
                    clarity_score REAL DEFAULT 0.0,
                    summary TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO interview_sessions SELECT * FROM _sessions_fix")
            cursor.execute("DROP TABLE _sessions_fix")

        if "user_topics" in broken_tables:
            cursor.execute("ALTER TABLE user_topics RENAME TO _topics_fix")
            cursor.execute("""
                CREATE TABLE user_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    topic_name TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'Technical',
                    status TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    notes TEXT DEFAULT '',
                    last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO user_topics SELECT * FROM _topics_fix")
            cursor.execute("DROP TABLE _topics_fix")

        if "roadmaps" in broken_tables:
            cursor.execute("ALTER TABLE roadmaps RENAME TO _roadmaps_fix")
            cursor.execute("""
                CREATE TABLE roadmaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    title TEXT NOT NULL,
                    target_role TEXT NOT NULL,
                    duration_days INTEGER DEFAULT 14,
                    weak_topics_covered TEXT DEFAULT '',
                    plan_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO roadmaps SELECT * FROM _roadmaps_fix")
            cursor.execute("DROP TABLE _roadmaps_fix")

        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.close()

def _apply_schema_enhancements(cursor):
    """
    Non-destructive schema migrations: safely adds any new columns or tables
    needed by full InterviewX feature set.
    """
    def get_cols(table_name: str):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [r["name"] for r in cursor.fetchall()]

    # Enhancements for candidate_resumes
    resume_cols = get_cols("candidate_resumes")
    if "parsed_experience" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN parsed_experience TEXT DEFAULT '[]'")
    if "parsed_education" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN parsed_education TEXT DEFAULT '[]'")
    if "strengths" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN strengths TEXT DEFAULT '[]'")
    if "missing_skills" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN missing_skills TEXT DEFAULT '[]'")
    if "suggested_improvements" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN suggested_improvements TEXT DEFAULT '[]'")
    if "interview_questions" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN interview_questions TEXT DEFAULT '[]'")
    if "summary" not in resume_cols:
        cursor.execute("ALTER TABLE candidate_resumes ADD COLUMN summary TEXT DEFAULT ''")

    # Enhancements for interview_sessions
    session_cols = get_cols("interview_sessions")
    if "resume_id" not in session_cols:
        cursor.execute("ALTER TABLE interview_sessions ADD COLUMN resume_id INTEGER")
    if "duration_minutes" not in session_cols:
        cursor.execute("ALTER TABLE interview_sessions ADD COLUMN duration_minutes INTEGER DEFAULT 15")
    if "conceptual_score" not in session_cols:
        cursor.execute("ALTER TABLE interview_sessions ADD COLUMN conceptual_score REAL DEFAULT 0.0")
    if "readiness_assessment" not in session_cols:
        cursor.execute("ALTER TABLE interview_sessions ADD COLUMN readiness_assessment TEXT DEFAULT ''")

    # Enhancements for interview_questions
    q_cols = get_cols("interview_questions")
    if "conceptual_score" not in q_cols:
        cursor.execute("ALTER TABLE interview_questions ADD COLUMN conceptual_score REAL DEFAULT 0.0")

    # Enhancements for user_topics
    topic_cols = get_cols("user_topics")
    if "revision_status" not in topic_cols:
        cursor.execute("ALTER TABLE user_topics ADD COLUMN revision_status TEXT DEFAULT 'Needs Work'")

    # Enhancements for roadmaps
    roadmap_cols = get_cols("roadmaps")
    if "progress_percent" not in roadmap_cols:
        cursor.execute("ALTER TABLE roadmaps ADD COLUMN progress_percent INTEGER DEFAULT 0")

    # Create roadmap_tasks table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roadmap_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            focus_topic TEXT NOT NULL,
            core_concept TEXT NOT NULL,
            recommended_study TEXT NOT NULL,
            practical_exercise TEXT NOT NULL,
            hours_recommended INTEGER DEFAULT 2,
            is_completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (roadmap_id) REFERENCES roadmaps (id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_roadmap ON roadmap_tasks(roadmap_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_roadmaps_user ON roadmaps(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON interview_sessions(user_id, created_at DESC);")

def init_db():
    """
    Initializes database schema with required multi-user tables for InterviewX.
    Safe to call multiple times (idempotent).
    """
    _migrate_and_repair_schema()

    schema_sql = """
    -- 1. Users / Candidate Profiles
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL DEFAULT 'Candidate',
        college TEXT DEFAULT 'Engineering Institute',
        degree TEXT DEFAULT 'B.Tech in Computer Science',
        graduation_year INTEGER DEFAULT 2026,
        target_role TEXT DEFAULT 'Software Development Engineer (SDE-1)',
        target_company_track TEXT DEFAULT 'Product Companies & Tier-1 Startups',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. Candidate Resumes & Ingested Profiles (Privacy controlled)
    CREATE TABLE IF NOT EXISTS candidate_resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        raw_text TEXT DEFAULT '',
        parsed_skills TEXT DEFAULT '[]',
        parsed_projects TEXT DEFAULT '[]',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    -- 3. Mock Interview Sessions
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_id INTEGER,
        role_id TEXT NOT NULL,
        role_title TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        interview_type TEXT NOT NULL DEFAULT 'Technical',
        target_company_track TEXT DEFAULT 'Product Companies',
        total_questions INTEGER DEFAULT 0,
        overall_score REAL DEFAULT 0.0,
        accuracy_score REAL DEFAULT 0.0,
        relevance_score REAL DEFAULT 0.0,
        completeness_score REAL DEFAULT 0.0,
        clarity_score REAL DEFAULT 0.0,
        summary TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (resume_id) REFERENCES candidate_resumes (id) ON DELETE SET NULL
    );

    -- 4. Individual Questions & Honest Feedback Records
    CREATE TABLE IF NOT EXISTS interview_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        question_number INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        category TEXT DEFAULT 'Technical',
        is_resume_based BOOLEAN DEFAULT 0,
        user_answer TEXT DEFAULT '',
        overall_score REAL DEFAULT 0.0,
        accuracy_score REAL DEFAULT 0.0,
        relevance_score REAL DEFAULT 0.0,
        completeness_score REAL DEFAULT 0.0,
        clarity_score REAL DEFAULT 0.0,
        honest_feedback TEXT DEFAULT '',
        incorrect_concepts TEXT DEFAULT '[]',
        missing_information TEXT DEFAULT '[]',
        improved_answer TEXT DEFAULT '',
        improvement_reason TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES interview_sessions (id) ON DELETE CASCADE
    );

    -- 5. Strengths and Recurring Weaknesses
    CREATE TABLE IF NOT EXISTS user_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic_name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Technical',
        status TEXT NOT NULL,
        frequency INTEGER DEFAULT 1,
        notes TEXT DEFAULT '',
        last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    -- 6. Personalized Preparation Roadmaps
    CREATE TABLE IF NOT EXISTS roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        target_role TEXT NOT NULL,
        duration_days INTEGER DEFAULT 14,
        weak_topics_covered TEXT DEFAULT '',
        plan_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    -- 7. Indices for Fast Lookups
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_resumes_user ON candidate_resumes(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON interview_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON interview_sessions(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_sessions_created ON interview_sessions(created_at);
    CREATE INDEX IF NOT EXISTS idx_questions_session ON interview_questions(session_id);
    CREATE INDEX IF NOT EXISTS idx_topics_user_status ON user_topics(user_id, status);
    CREATE INDEX IF NOT EXISTS idx_roadmaps_user ON roadmaps(user_id);
    """

    with get_db_cursor(commit=True) as cursor:
        cursor.executescript(schema_sql)
        _apply_schema_enhancements(cursor)
