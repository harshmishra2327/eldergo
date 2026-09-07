"""
ElderGo+ MySQL Database Initializer Script
Reads .env credentials, creates eldergo_db if missing, and executes schema.sql
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME", "eldergo_db")

def parse_sql_statements(sql_text):
    """
    Parses a SQL script into individual executable statements,
    stripping single-line comments (-- and #) while maintaining statement ordering.
    """
    clean_lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith('--') or stripped.startswith('#'):
            continue
        clean_lines.append(line)
    
    clean_sql = "\n".join(clean_lines)
    raw_statements = clean_sql.split(';')
    
    executable_statements = []
    for stmt in raw_statements:
        cleaned_stmt = stmt.strip()
        if cleaned_stmt:
            executable_statements.append(cleaned_stmt)
            
    return executable_statements

def initialize_database():
    print("==================================================")
    print("      ElderGo+ MySQL Database Initializer         ")
    print("==================================================")
    print(f"Connecting to MySQL Host: {DB_HOST}:{DB_PORT} as User: '{DB_USER}'...")

    try:
        # Step 1: Connect to MySQL Server (Server-level connection)
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = connection.cursor()

        # Step 2: Create Database if not exists and select it
        print(f"Creating database '{DB_NAME}' if not exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4;")
        cursor.execute(f"USE `{DB_NAME}`;")
        print(f"Database '{DB_NAME}' selected.")

        # Step 3: Read schema.sql file
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_path):
            print(f"Error: schema.sql file not found at {schema_path}")
            sys.exit(1)

        print("Executing schema.sql DDL and seed statements in correct dependency order...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        statements = parse_sql_statements(schema_sql)
        executed_count = 0

        for statement in statements:
            cursor.execute(statement)
            executed_count += 1

        connection.commit()

        # Step 4: Verify tables created in MySQL
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]

        cursor.close()
        connection.close()

        print("==================================================")
        print("[OK] Database initialization COMPLETED SUCCESSFULLY!")
        print("==================================================")
        print(f"Total Statements Executed: {executed_count}")
        print(f"Tables Created in Database '{DB_NAME}':")
        for table_name in tables:
            print(f"  * {table_name}")
        print("--------------------------------------------------")
        print("Demo Accounts Seeded in MySQL:")
        print("  1. Client:    username='client'    password='client123'")
        print("  2. Companion: username='rahul'     password='companion123'")
        print("  3. Admin:     username='admin'     password='admin123'")
        print("==================================================")

    except mysql.connector.Error as err:
        print("\n[ERROR] MySQL Database Initialization Error:")
        print(f"  Error Code: {err.errno}")
        print(f"  Message:    {err.msg}")
        print("\nPlease check your .env file and ensure MySQL password is correct.")
        sys.exit(1)

if __name__ == "__main__":
    initialize_database()
