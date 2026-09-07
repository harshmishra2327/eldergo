"""
ElderGo+ Quick Database Inspector Script
Run this script using `python view_db.py` to inspect all stored data in MySQL.
"""

import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME", "eldergo_db")

def print_table(title, rows, columns):
    print(f"\n==================================================")
    print(f" TABLE: {title.upper()} ({len(rows)} records)")
    print(f"==================================================")
    if not rows:
        print(" (No records found)")
        return

    # Calculate column widths
    col_widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            val_str = str(row.get(col, ''))
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            col_widths[col] = max(col_widths[col], len(val_str))

    header = " | ".join(f"{col.upper():<{col_widths[col]}}" for col in columns)
    print(header)
    print("-" * len(header))

    for row in rows:
        row_str = " | ".join(
            f"{(str(row.get(col, ''))[:37] + '...') if len(str(row.get(col, '')))>40 else str(row.get(col, '')):<{col_widths[col]}}"
            for col in columns
        )
        print(row_str)

def main():
    print(f"Connecting to MySQL ({DB_HOST}:{DB_PORT}) Database: '{DB_NAME}'...\n")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)

        # 1. Users
        cursor.execute("SELECT id, username, email, role, full_name, phone, emergency_contact, status, created_at FROM users")
        users = cursor.fetchall()
        print_table("users", users, ["id", "username", "email", "role", "full_name", "phone", "emergency_contact", "status"])

        # 2. Companions
        cursor.execute("SELECT id, user_id, city, preferred_service, hourly_rate, rating, verification_status FROM companions")
        companions = cursor.fetchall()
        print_table("companions", companions, ["id", "user_id", "city", "preferred_service", "hourly_rate", "rating", "verification_status"])

        # 3. Bookings
        cursor.execute("SELECT id, booking_code, client_id, companion_id, service_type, booking_date, status, total_fare FROM bookings")
        bookings = cursor.fetchall()
        print_table("bookings", bookings, ["id", "booking_code", "client_id", "companion_id", "service_type", "booking_date", "status", "total_fare"])

        # 4. Verifications
        cursor.execute("SELECT id, companion_id, companion_name, document_type, status FROM verifications")
        verifications = cursor.fetchall()
        print_table("verifications", verifications, ["id", "companion_id", "companion_name", "document_type", "status"])

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"[ERROR] Could not connect to MySQL database: {err}")

if __name__ == "__main__":
    main()
