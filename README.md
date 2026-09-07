# ElderGo+ Full-Stack Application Setup & Run Guide

ElderGo+ is a modern, full-stack web platform built using **Flask (Python)** and **MySQL** that connects independent seniors with verified companions for medical visits, shopping, transportation, and daily routine support.

---

## Features Implemented

* **User Authentication**: Secure Registration & Login with password hashing (`scrypt`) for Clients, Companions, and Admins.
* **Client Dashboard**:
  * Pickup and destination selection.
  * **Find Companion** booking request form.
  * **30-Second Cancellation Countdown** timer badge.
  * **5-Minute Connection Timeout** with **Request Again** option.
  * Companion details, hourly rate (₹/hour), and 4-digit OTP display screen.
  * Interactive OpenStreetMap (Leaflet.js) live tracking map.
  * Fare breakdown summary, payment status, and 5-star feedback submission.
* **Companion Dashboard**:
  * Online/Offline duty status toggle switch.
  * Hourly rate setting (₹/hour) synced with client quotes.
  * Real-time incoming booking request cards with Accept / Reject.
  * 4-Digit OTP verification screen to start ride transit.
  * Start Ride and End Ride duty completion controls.
  * Interactive route navigation live map.
  * Booking history table & earnings statistics.
* **Admin Dashboard**:
  * Live statistics cards for clients, companions, active bookings, active rides, and pending verifications.
  * Companion verification document review with **Approve** and **Reject** controls.
  * Instant client-side search filtering across Client, Companion, and Booking management tables.

---

## Prerequisites

1. **Python 3.8+** installed on your system.
2. **MySQL Server** installed and running on `localhost:3306`.

---

## Setup & Running Instructions

### Step 1: Install Python Dependencies

Open PowerShell or Command Prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

---

### Step 2: Configure MySQL Password in `.env` File

Open the `.env` file in your root folder:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_actual_mysql_password_here
DB_NAME=eldergo_db
DB_PORT=3306
SECRET_KEY=eldergo_secret_key_2026
FLASK_ENV=development
```

> ⚠️ **Important**: Replace `your_actual_mysql_password_here` with your real local MySQL root password.

---

### Step 3: Initialize the MySQL Database

Run the database setup script to automatically create `eldergo_db`, all tables, and seed initial demo accounts:

```bash
python init_db.py
```

Expected output:
```text
==================================================
      ElderGo+ MySQL Database Initializer         
==================================================
Connecting to MySQL Host: localhost:3306 as User: 'root'...
Creating database 'eldergo_db' if not exists...
Database 'eldergo_db' ready.
Executing schema.sql DDL and seed statements...
==================================================
✓ Database initialization COMPLETED SUCCESSFULLY!
==================================================
```

---

### Step 4: Start the Flask Backend Application

Start the Flask web server:

```bash
python app.py
```

Expected output:
```text
==================================================
  Starting ElderGo+ Full-Stack Flask Web Server   
==================================================
  Connected to MySQL Database: 'eldergo_db' on localhost:3306
  URL: http://127.0.0.1:5000
==================================================
```

---

### Step 5: Open & Test the Website

Open your browser and navigate to:

👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

#### Demo Accounts Available in Database:

| Role | Username | Password | Dashboard URL |
| :--- | :--- | :--- | :--- |
| **Client** | `client` | `client123` | [http://127.0.0.1:5000/client-dashboard](http://127.0.0.1:5000/client-dashboard) |
| **Companion** | `rahul` | `companion123` | [http://127.0.0.1:5000/companion-dashboard](http://127.0.0.1:5000/companion-dashboard) |
| **Admin** | `admin` | `admin123` | [http://127.0.0.1:5000/admin-dashboard](http://127.0.0.1:5000/admin-dashboard) |

---

## File Structure

```text
major project/
├── app.py                  # Main Flask Server & REST APIs
├── init_db.py              # MySQL Database Setup & Seeder Script
├── schema.sql              # MySQL DDL Schema & Table Definitions
├── requirements.txt        # Python Packages
├── .env                    # Local MySQL Credentials (DO NOT COMMIT)
├── .env.example            # Environment Template
├── README.md               # Documentation & Guide
├── static/
│   ├── css/
│   │   └── style.css       # Custom Glassmorphism Styling
│   ├── js/
│   │   ├── api.js          # Flask REST API Client Helper
│   │   └── auth.js         # Authentication Navigation Helper
│   └── images/             # Asset Images
└── templates/
    ├── index.html          # Landing Page
    ├── login.html          # User / Companion / Admin Login Page
    ├── register.html       # Role Registration Page
    ├── client_dashboard.html    # Client Booking Dashboard
    ├── companion_dasboard.html # Companion Assistance Dashboard
    └── admin_dasboard.html     # Admin Control Center
```