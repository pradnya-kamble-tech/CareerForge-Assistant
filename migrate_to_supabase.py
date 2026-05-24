import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

# Configuration
SQLITE_DB = "data/careerforge.db"
# Get connection string from user or environment
DATABASE_URL = os.environ.get("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL environment variable not set.")
        return

    print("Starting migration from SQLite to Supabase...")

    # 1. Connect to SQLite
    sl_conn = sqlite3.connect(SQLITE_DB)
    sl_conn.row_factory = sqlite3.Row
    sl_cursor = sl_conn.cursor()

    # 2. Connect to Supabase (PostgreSQL)
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()

    try:
        # Debug: Check current schema
        pg_cursor.execute("SELECT current_schema(), current_user")
        schema, user = pg_cursor.fetchone()
        print(f"Current schema: {schema}, Current user: {user}")

        # Drop tables for a clean start
        print("Cleaning up existing tables in public schema...")
        for table in ["logs", "decisions", "resumes", "users"]:
            pg_cursor.execute(f"DROP TABLE IF EXISTS public.\"{table}\" CASCADE")
        pg_conn.commit()

        # Create tables in Supabase first (EXPLICIT PUBLIC SCHEMA)
        print("Initialising tables in public schema...")
        pk_type = "SERIAL PRIMARY KEY"
        
        tables_to_create = {
            "users": f"CREATE TABLE public.\"users\" (id {pk_type}, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
            "resumes": f"CREATE TABLE public.\"resumes\" (id {pk_type}, filename TEXT NOT NULL, score INTEGER DEFAULT 0, score_level TEXT, risk_level TEXT, risk_icon TEXT, skills TEXT, skills_total INTEGER DEFAULT 0, career_preds TEXT, insight TEXT, owner TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
            "decisions": f"CREATE TABLE public.\"decisions\" (id {pk_type}, filename TEXT NOT NULL, score INTEGER DEFAULT 0, risk_level TEXT, insight TEXT, owner TEXT NOT NULL, decision TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
            "logs": f"CREATE TABLE public.\"logs\" (id {pk_type}, action TEXT, \"user\" TEXT, detail TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        }

        for name, sql in tables_to_create.items():
            print(f" - Creating {name}...")
            pg_cursor.execute(sql)
        
        pg_conn.commit()
        print("Commited table creation.")

        # 3. Migrate Users
        print("Migrating Users...")
        sl_cursor.execute("SELECT * FROM users")
        for row in sl_cursor.fetchall():
            pg_cursor.execute(
                "INSERT INTO public.\"users\" (email, password, role, created_at) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
                (row['email'], row['password'], row['role'], row['created_at'])
            )
        
        # 4. Migrate Resumes
        print("Migrating Resumes...")
        sl_cursor.execute("SELECT * FROM resumes")
        for row in sl_cursor.fetchall():
            pg_cursor.execute(
                """INSERT INTO public.\"resumes\" (filename, score, score_level, risk_level, risk_icon, skills, skills_total, career_preds, insight, owner, created_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (row['filename'], row['score'], row['score_level'], row['risk_level'], row['risk_icon'], row['skills'], row['skills_total'], row['career_preds'], row['insight'], row['owner'], row['created_at'])
            )

        # 5. Migrate Decisions
        print("Migrating Decisions...")
        sl_cursor.execute("SELECT * FROM decisions")
        for row in sl_cursor.fetchall():
            pg_cursor.execute(
                "INSERT INTO public.\"decisions\" (filename, score, risk_level, insight, owner, decision, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (row['filename'], row['score'], row['risk_level'], row['insight'], row['owner'], row['decision'], row['created_at'])
            )

        # 6. Migrate Logs
        print("Migrating Logs...")
        sl_cursor.execute("SELECT * FROM logs")
        for row in sl_cursor.fetchall():
            pg_cursor.execute(
                "INSERT INTO public.\"logs\" (action, \"user\", detail, created_at) VALUES (%s, %s, %s, %s)",
                (row['action'], row['user'], row['detail'], row['created_at'])
            )

        pg_conn.commit()
        print("Migration successful! All data moved to Supabase.")

    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        sl_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
