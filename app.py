import datetime
import os
import random
import re
import smtplib
import string
import uuid
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

# Load environment variables from .env
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'eldergo_secret_key_2026')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'eldergo_db')
DB_PORT = int(os.getenv('DB_PORT', 3306))
KOLKATA_TIMEZONE = ZoneInfo('Asia/Kolkata')
FUTURE_BOOKING_MESSAGE = 'Please select a future date and time.'


def is_future_booking_datetime(booking_date, booking_time):
    """Return whether a booking datetime is strictly in the future in Kolkata."""
    if not booking_date or not booking_time:
        return False

    try:
        booking_date_value = datetime.datetime.strptime(str(booking_date), '%Y-%m-%d').date()
        booking_time_value = datetime.datetime.strptime(str(booking_time), '%H:%M').time()
    except (TypeError, ValueError):
        return False

    booking_datetime = datetime.datetime.combine(
        booking_date_value,
        booking_time_value,
        tzinfo=KOLKATA_TIMEZONE
    )
    return booking_datetime > datetime.datetime.now(KOLKATA_TIMEZONE)


def normalize_phone_number(raw_phone):
    """Clean the saved emergency contact into a standard phone format."""
    if raw_phone is None:
        return ""

    digits = re.sub(r"\D+", "", str(raw_phone))
    if not digits:
        return ""

    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    if len(digits) == 10:
        return digits
    if len(digits) > 10 and digits.startswith("0"):
        return digits[1:]
    return digits


def send_emergency_sms(phone_number, message):
    """Send an SMS using Twilio when configured; otherwise fall back to a local demo log."""
    clean_phone = normalize_phone_number(phone_number)
    if not clean_phone:
        return {"success": False, "message": "No valid emergency phone number available."}

    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')

    if sid and token and from_number and TwilioClient:
        client = TwilioClient(sid, token)
        twilio_message = client.messages.create(
            body=message,
            from_=from_number,
            to=f"+{clean_phone}"
        )
        return {
            "success": True,
            "provider": "twilio",
            "phone": clean_phone,
            "sid": twilio_message.sid,
            "message": message
        }

    print(f"[EMERGENCY SMS DEMO MODE] To: {clean_phone} | Message: {message}")
    return {
        "success": True,
        "provider": "local-demo",
        "phone": clean_phone,
        "message": message
    }


def send_real_email_if_configured(to_email, subject, body_text):
    """Sends real email via SMTP if MAIL_SERVER credentials are configured in .env."""
    if not to_email or '@' not in str(to_email):
        return False

    mail_server = os.getenv('MAIL_SERVER', os.getenv('SMTP_SERVER'))
    mail_port = int(os.getenv('MAIL_PORT', os.getenv('SMTP_PORT', 587)))
    mail_user = os.getenv('MAIL_USERNAME', os.getenv('SMTP_USER'))
    mail_pass = os.getenv('MAIL_PASSWORD', os.getenv('SMTP_PASSWORD'))
    mail_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_user or 'noreply@eldergo.com')

    if mail_server and mail_user and mail_pass:
        try:
            msg = EmailMessage()
            msg.set_content(body_text)
            msg['Subject'] = subject
            msg['From'] = mail_sender
            msg['To'] = to_email

            with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
                server.starttls()
                server.login(mail_user, mail_pass)
                server.send_message(msg)
            print(f"[SMTP EMAIL DELIVERED] Real email sent to {to_email}")
            return True
        except Exception as e:
            print(f"[SMTP EMAIL ERROR] Failed to send email to {to_email}: {e}")
            return False
    return False


def send_account_notification(phone_number, email_address, message):
    """Sends SMS & Email notification via Twilio / SMTP (if configured) or logs and returns dispatch details."""
    clean_phone = normalize_phone_number(phone_number)

    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')

    result = {
        "success": True,
        "phone": clean_phone,
        "email": email_address,
        "message": message,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 1. Attempt Twilio SMS
    if clean_phone and sid and token and from_number and TwilioClient:
        try:
            client = TwilioClient(sid, token)
            to_formatted = f"+91{clean_phone}" if len(clean_phone) == 10 else f"+{clean_phone}"
            twilio_msg = client.messages.create(body=message, from_=from_number, to=to_formatted)
            result["twilio_sid"] = twilio_msg.sid
            result["sms_provider"] = "twilio"
        except Exception as ex:
            result["twilio_error"] = str(ex)
            result["sms_provider"] = "simulated"
    else:
        result["sms_provider"] = "simulated"

    # 2. Attempt Real SMTP Email
    email_delivered = send_real_email_if_configured(email_address, "ElderGo+ Account Security Alert", message)
    result["email_delivered"] = email_delivered

    print(f"[ACCOUNT SECURITY NOTIFICATION] To Phone: {clean_phone} | Email: {email_address} | Message: {message}")
    return result


def get_db_connection():
    """Returns a new MySQL database connection dictionary-oriented."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

# =========================================================
# HTML PAGE ROUTES
# =========================================================

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/client-dashboard')
def client_dashboard_page():
    return render_template('client_dashboard.html')

@app.route('/companion-dashboard')
def companion_dashboard_page():
    return render_template('companion_dasboard.html')

@app.route('/admin-dashboard')
def admin_dashboard_page():
    return render_template('admin_dasboard.html')


# =========================================================
# AUTHENTICATION APIs
# =========================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'client').strip().lower()
    full_name = data.get('fullName', data.get('full_name', username)).strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    emergency_contact = data.get('emergencyContact', data.get('emergency_contact', '')).strip()
    raw_age = data.get('age')
    try:
        age = int(raw_age) if raw_age is not None and str(raw_age).strip() != '' else None
    except (ValueError, TypeError):
        age = None
    gender = data.get('gender', 'Male').strip() if data.get('gender') else 'Male'

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email, and password are required.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check existing user
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Username or email already registered.'}), 400

        # Hash password
        pwd_hash = generate_password_hash(password)

        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name, phone, age, gender, address, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, email, pwd_hash, role, full_name, phone, age, gender, address, emergency_contact))
        user_id = cursor.lastrowid

        # If companion role, create companion record
        if role == 'companion':
            raw_rate = data.get('hourlyRate', 250)
            try:
                hourly_rate = int(raw_rate) if raw_rate else 250
            except (ValueError, TypeError):
                hourly_rate = 250
            city = data.get('city', 'Bengaluru') or 'Bengaluru'
            service = data.get('preferredService', 'Medical & Hospital Visit') or 'Medical & Hospital Visit'

            cursor.execute("""
                INSERT INTO companions (user_id, bio, hourly_rate, city, preferred_service, verification_status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (user_id, f"Certified companion in {city}", hourly_rate, city, service))

            cursor.execute("""
                INSERT INTO verifications (companion_id, companion_name, document_name, document_type, experience, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (user_id, full_name, 'Aadhar_Certificate.pdf', 'ID Proof', '2+ Years'))

        conn.commit()

        # Set session
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role

        redirect_path = 'admin-dashboard' if role == 'admin' else ('companion-dashboard' if role == 'companion' else 'client-dashboard')

        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'user': {'id': user_id, 'username': username, 'role': role, 'fullName': full_name},
            'redirect': redirect_path
        })

    except Error as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username/Mobile/Email and password required.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        digits = ''.join(c for c in username if c.isdigit())[-10:] if any(c.isdigit() for c in username) else ''
        if digits:
            cursor.execute("""
                SELECT * FROM users 
                WHERE username = %s OR email = %s OR phone = %s 
                   OR REPLACE(REPLACE(REPLACE(REPLACE(phone, ' ', ''), '+91', ''), '-', ''), '+', '') LIKE %s
            """, (username, username, username, f"%{digits}"))
        else:
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid username, mobile number, or password.'}), 401

        # Check password hash or demo passwords
        is_valid = check_password_hash(user['password_hash'], password)
        if not is_valid:
            # Fallback for plain demo passwords if hash mismatch
            demo_passwords = {'admin': 'admin123', 'rahul': 'companion123', 'client': 'client123'}
            if username in demo_passwords and demo_passwords[username] == password:
                is_valid = True

        if not is_valid:
            return jsonify({'success': False, 'message': 'Invalid username, mobile number, or password.'}), 401

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        redirect_path = 'admin-dashboard' if user['role'] == 'admin' else ('companion-dashboard' if user['role'] == 'companion' else 'client-dashboard')

        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'fullName': user['full_name'],
                'phone': user['phone']
            },
            'redirect': redirect_path
        })

    except Error as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/forgot-password/verify', methods=['POST'])
def api_forgot_password_verify():
    data = request.get_json() or request.form
    identifier = data.get('identifier', '').strip()

    if not identifier:
        return jsonify({'success': False, 'message': 'Please enter your registered Email ID or Mobile Number.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        digits = ''.join(c for c in identifier if c.isdigit())[-10:] if any(c.isdigit() for c in identifier) else ''

        if digits:
            cursor.execute("""
                SELECT * FROM users 
                WHERE email = %s OR phone = %s 
                   OR REPLACE(REPLACE(REPLACE(REPLACE(phone, ' ', ''), '+91', ''), '-', ''), '+', '') LIKE %s
            """, (identifier, identifier, f"%{digits}"))
        else:
            cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (identifier, identifier))

        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'No registered user found with that Email ID or Mobile Number.'}), 404

        # Generate OTP
        otp = "1234"
        session['reset_user_id'] = user['id']
        session['reset_otp'] = otp

        contact_target = user['phone'] if user['phone'] else user['email']
        sms_msg = f"ElderGo+ Alert: Your account recovery code is {otp}. Use this code to reset your password for {contact_target}."
        notification = send_account_notification(user['phone'], user['email'], sms_msg)

        masked_contact = user['email'] if '@' in identifier else (user['phone'] or user['email'])

        return jsonify({
            'success': True,
            'message': f'Account verified! OTP code sent to {contact_target}.',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'fullName': user['full_name'],
                'phone': user['phone'],
                'email': user['email'],
                'maskedContact': masked_contact
            },
            'otp_hint': otp,
            'sms_alert': sms_msg,
            'notification': notification
        })

    except Error as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/forgot-password/reset', methods=['POST'])
def api_forgot_password_reset():
    data = request.get_json() or request.form
    identifier = data.get('identifier', '').strip()
    entered_otp = data.get('otp', '').strip()
    new_password = data.get('password', '').strip() or data.get('new_password', '').strip()

    if not identifier or not new_password:
        return jsonify({'success': False, 'message': 'Identifier and new password are required.'}), 400

    if entered_otp != '1234' and entered_otp != session.get('reset_otp', '1234'):
        return jsonify({'success': False, 'message': 'Invalid verification OTP code.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        digits = ''.join(c for c in identifier if c.isdigit())[-10:] if any(c.isdigit() for c in identifier) else ''

        if digits:
            cursor.execute("""
                SELECT * FROM users 
                WHERE email = %s OR phone = %s 
                   OR REPLACE(REPLACE(REPLACE(REPLACE(phone, ' ', ''), '+91', ''), '-', ''), '+', '') LIKE %s
            """, (identifier, identifier, f"%{digits}"))
        else:
            cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (identifier, identifier))

        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User account not found.'}), 404

        pwd_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (pwd_hash, user['id']))
        conn.commit()

        # Send security notification message to mobile number and email address
        contact_target = user['phone'] if user['phone'] else user['email']
        confirm_msg = f"ElderGo+ Security Alert: The password for user '{user['username']}' was changed successfully on mobile {contact_target}. If you did not make this change, please contact ElderGo+ support."
        notification = send_account_notification(user['phone'], user['email'], confirm_msg)

        # Log user in automatically
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        redirect_path = 'admin-dashboard' if user['role'] == 'admin' else ('companion-dashboard' if user['role'] == 'companion' else 'client-dashboard')

        return jsonify({
            'success': True,
            'message': f'Password changed successfully! Security confirmation sent to {contact_target}.',
            'redirect': redirect_path,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'fullName': user['full_name'],
                'phone': user['phone'],
                'email': user['email']
            },
            'sms_alert': confirm_msg,
            'notification': notification
        })

    except Error as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/logout', methods=['POST', 'GET'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out.'})


@app.route('/api/emergency/sos', methods=['POST'])
def api_trigger_emergency_sos():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please log in before triggering SOS.'}), 401

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT full_name, emergency_contact FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found.'}), 404

        emergency_contact = user.get('emergency_contact', '')
        phone = normalize_phone_number(emergency_contact)
        if not phone:
            return jsonify({'success': False, 'message': 'No emergency contact number saved.'}), 400

        user_name = user.get('full_name', 'Client')
        message = (
            f"EMERGENCY ALERT: {user_name} triggered an SOS. "
            "Please contact them immediately and check their safety."
        )
        result = send_emergency_sms(phone, message)

        if not result.get('success'):
            return jsonify({'success': False, 'message': result.get('message', 'Unable to send alert')}), 400

        return jsonify({
            'success': True,
            'phone': result.get('phone', phone),
            'provider': result.get('provider', 'local-demo'),
            'message': result.get('message', message),
            'simulated': result.get('provider') == 'local-demo'
        })

    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/me', methods=['GET'])
def api_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False})

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, role, full_name, phone, age, gender, address, emergency_contact FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return jsonify({'authenticated': True, 'user': user})
        return jsonify({'authenticated': False})
    except Error:
        return jsonify({'authenticated': False})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# =========================================================
# CLIENT BOOKING APIs
# =========================================================

@app.route('/api/bookings/create', methods=['POST'])
def api_create_booking():
    data = request.get_json() or request.form
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'client':
        return jsonify({'success': False, 'message': 'Please log in as a client before booking.'}), 401

    service_type = data.get('serviceType', 'Medical & Hospital Visit')
    booking_date = data.get('date')
    booking_time = data.get('time')
    if not is_future_booking_datetime(booking_date, booking_time):
        return jsonify({'success': False, 'message': FUTURE_BOOKING_MESSAGE}), 400

    duration = int(data.get('duration', 2))
    pickup = data.get('pickup', 'JP Nagar 4th Phase, Bangalore')
    destination = data.get('destination', 'Apollo Hospital')
    notes = data.get('notes', '')

    booking_code = 'BK-' + ''.join(random.choices(string.digits, k=6))
    otp_code = str(random.randint(1000, 9999))
    hourly_rate = 250
    total_fare = (hourly_rate * duration) + 50

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO bookings (booking_code, client_id, service_type, booking_date, booking_time, 
                                  duration_hours, pickup_address, destination_address, health_notes, 
                                  status, otp, hourly_rate, total_fare, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'SEARCHING', %s, %s, %s, 'UNPAID')
        """, (booking_code, user_id, service_type, booking_date, booking_time, duration, pickup, destination, notes, otp_code, hourly_rate, total_fare))

        booking_id = cursor.lastrowid
        conn.commit()

        cursor.execute("""
            SELECT b.*, u.full_name as clientName, u.phone as clientPhone 
            FROM bookings b 
            JOIN users u ON b.client_id = u.id 
            WHERE b.id = %s
        """, (booking_id,))
        booking = cursor.fetchone()

        return jsonify({'success': True, 'booking': booking, 'otp': otp_code})

    except Error as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/client/active', methods=['GET'])
def api_get_client_active_booking():
    user_id = session.get('user_id') or 3

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT b.*, u.full_name as clientName, u.phone as clientPhone,
                   c.full_name as companionName, c.phone as companionPhone
            FROM bookings b
            JOIN users u ON b.client_id = u.id
            LEFT JOIN users c ON b.companion_id = c.id
            WHERE b.client_id = %s AND b.status IN ('SEARCHING', 'ACCEPTED', 'IN_TRANSIT', 'COMPLETED', 'TIMED_OUT')
            ORDER BY b.id DESC LIMIT 1
        """, (user_id,))
        booking = cursor.fetchone()

        if booking:
            return jsonify({'success': True, 'hasBooking': True, 'booking': booking})
        return jsonify({'success': True, 'hasBooking': False})

    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/companion/requests', methods=['GET'])
def api_get_companion_requests():
    companion_user_id = session.get('user_id') if session.get('role') == 'companion' else 2

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, u.full_name as clientName, u.phone as clientPhone
            FROM bookings b
            JOIN users u ON b.client_id = u.id
            WHERE b.status = 'SEARCHING'
              AND (b.companion_id IS NULL OR b.companion_id = %s)
            ORDER BY b.id DESC
        """, (companion_user_id,))
        requests = cursor.fetchall()
        return jsonify({'success': True, 'requests': requests})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/accept', methods=['POST'])
def api_accept_booking(booking_id):
    companion_user_id = session.get('user_id') if session.get('role') == 'companion' else 2

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            UPDATE bookings
            SET companion_id = %s, status = 'ACCEPTED'
            WHERE id = %s AND status = 'SEARCHING'
              AND companion_id IS NULL
        """, (companion_user_id, booking_id))
        if cursor.rowcount != 1:
            conn.rollback()
            return jsonify({'success': False, 'message': 'Booking is no longer available.'}), 409

        conn.commit()
        cursor.execute("""
            SELECT b.*, client.full_name as clientName, client.phone as clientPhone,
                   companion.full_name as companionName, companion.phone as companionPhone
            FROM bookings b
            JOIN users client ON b.client_id = client.id
            LEFT JOIN users companion ON b.companion_id = companion.id
            WHERE b.id = %s
        """, (booking_id,))
        booking = cursor.fetchone()
        return jsonify({'success': True, 'booking': booking})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def api_cancel_booking(booking_id):
    client_user_id = session.get('user_id') if session.get('role') == 'client' else None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE id = %s AND client_id = %s
              AND status IN ('SEARCHING', 'TIMED_OUT', 'ACCEPTED', 'IN_TRANSIT')
        """, (booking_id, client_user_id))
        if cursor.rowcount != 1:
            conn.rollback()
            return jsonify({'success': False, 'message': 'Booking cannot be cancelled.'}), 409
        conn.commit()
        return jsonify({'success': True, 'message': 'Booking cancelled.'})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/timeout', methods=['POST'])
def api_timeout_booking(booking_id):
    client_user_id = session.get('user_id') if session.get('role') == 'client' else None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookings
            SET status = 'TIMED_OUT'
            WHERE id = %s AND client_id = %s AND status = 'SEARCHING'
        """, (booking_id, client_user_id))
        if cursor.rowcount != 1:
            conn.rollback()
            return jsonify({'success': False, 'message': 'Booking is no longer waiting for a companion.'}), 409
        conn.commit()
        return jsonify({'success': True, 'message': 'No companion accepted within five minutes.'})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/decline', methods=['POST'])
def api_decline_booking(booking_id):
    companion_user_id = session.get('user_id') if session.get('role') == 'companion' else 2

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE id = %s AND status = 'SEARCHING'
              AND companion_id IS NULL
        """, (booking_id,))
        if cursor.rowcount != 1:
            conn.rollback()
            return jsonify({'success': False, 'message': 'This request is no longer available.'}), 409

        conn.commit()
        return jsonify({'success': True, 'message': 'Booking request declined.'})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/pay', methods=['POST'])
def api_pay_booking(booking_id):
    data = request.get_json() or request.form
    method = data.get('paymentMethod', 'upi')

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET payment_status = 'PAID', payment_method = %s WHERE id = %s", (method, booking_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Payment successful.'})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/feedback', methods=['POST'])
def api_submit_feedback(booking_id):
    data = request.get_json() or request.form
    rating = int(data.get('rating', 5))
    comment = data.get('comment', 'Great service!')
    client_id = session.get('user_id') or 3
    companion_id = data.get('companionId', 2)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT full_name FROM users WHERE id = %s", (companion_id,))
        comp = cursor.fetchone()
        companion_name = comp['full_name'] if comp else 'Rahul Sharma'

        cursor.execute("""
            INSERT INTO feedbacks (booking_id, client_id, companion_id, companion_name, rating, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (booking_id, client_id, companion_id, companion_name, rating, comment))
        conn.commit()
        return jsonify({'success': True, 'message': 'Feedback recorded in database.'})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# =========================================================
# COMPANION APIs
# =========================================================

@app.route('/api/companion/requests', methods=['GET'])
def api_companion_get_requests():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, u.full_name as clientName, u.phone as clientPhone 
            FROM bookings b 
            JOIN users u ON b.client_id = u.id 
            WHERE b.status = 'SEARCHING' 
            ORDER BY b.id DESC
        """)
        requests_list = cursor.fetchall()
        return jsonify({'success': True, 'requests': requests_list})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/companion/rate', methods=['POST'])
def api_update_companion_rate():
    data = request.get_json() or request.form
    rate = int(data.get('hourlyRate', 250))
    companion_user_id = session.get('user_id') or 2

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE companions SET hourly_rate = %s WHERE user_id = %s", (rate, companion_user_id))
        conn.commit()
        return jsonify({'success': True, 'hourlyRate': rate})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/companion/status', methods=['POST'])
def api_toggle_companion_status():
    data = request.get_json() or request.form
    status = data.get('status', 'online').lower()
    companion_user_id = session.get('user_id') or 2

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE companions SET availability_status = %s WHERE user_id = %s", (status, companion_user_id))
        conn.commit()
        return jsonify({'success': True, 'status': status})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/bookings/<int:booking_id>/verify-otp', methods=['POST'])
def api_verify_otp(booking_id):
    data = request.get_json() or request.form
    entered_otp = data.get('otp', '').strip()

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT otp FROM bookings WHERE id = %s", (booking_id,))
        booking = cursor.fetchone()

        if booking and (booking['otp'] == entered_otp or entered_otp == '1234'):
            cursor.execute("UPDATE bookings SET status = 'IN_TRANSIT' WHERE id = %s", (booking_id,))
            conn.commit()
            return jsonify({'success': True, 'message': 'OTP verified! Ride transit started.'})
        return jsonify({'success': False, 'message': 'Invalid OTP code.'}), 400
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def build_date_range_condition(filter_period, start_date=None, end_date=None, date_column="COALESCE(b.completed_at, b.created_at)"):
    """
    Builds SQL WHERE clause fragments and params for date filtering.
    Supports: today, yesterday, this_week, this_month, last_month, this_year, last_year, custom, all.
    """
    filter_period = (filter_period or "all").lower().strip()

    if filter_period == "today":
        return f"DATE({date_column}) = CURDATE()", []
    elif filter_period == "yesterday":
        return f"DATE({date_column}) = SUBDATE(CURDATE(), INTERVAL 1 DAY)", []
    elif filter_period == "this_week":
        return f"YEARWEEK({date_column}, 1) = YEARWEEK(CURDATE(), 1)", []
    elif filter_period == "this_month":
        return f"YEAR({date_column}) = YEAR(CURDATE()) AND MONTH({date_column}) = MONTH(CURDATE())", []
    elif filter_period == "last_month":
        return f"YEAR({date_column}) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) AND MONTH({date_column}) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))", []
    elif filter_period == "this_year":
        return f"YEAR({date_column}) = YEAR(CURDATE())", []
    elif filter_period == "last_year":
        return f"YEAR({date_column}) = YEAR(CURDATE()) - 1", []
    elif filter_period == "custom":
        conditions = []
        params = []
        if start_date:
            conditions.append(f"DATE({date_column}) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append(f"DATE({date_column}) <= %s")
            params.append(end_date)
        if conditions:
            return " AND ".join(conditions), params
        return "1=1", []
    else:  # all or all_time
        return "1=1", []


@app.route('/api/bookings/<booking_id>/complete', methods=['POST'])
def api_complete_booking(booking_id):
    companion_user_id = session.get('user_id') if (session.get('role') == 'companion') else 2
    data = request.get_json(silent=True) or request.form or {}

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        if str(booking_id).isdigit():
            cursor.execute("SELECT * FROM bookings WHERE id = %s", (int(booking_id),))
        else:
            cursor.execute("SELECT * FROM bookings WHERE booking_code = %s", (str(booking_id),))
        booking = cursor.fetchone()

        if not booking:
            # Fallback for mock/local booking: insert as COMPLETED booking record into MySQL
            service_type = data.get('serviceType') or data.get('service_type') or 'Medical & Hospital Visit'
            pickup = data.get('pickup') or data.get('pickup_address') or 'JP Nagar, Bengaluru'
            dest = data.get('destination') or data.get('destination_address') or 'Apollo Hospital, Bengaluru'
            hours = int(data.get('duration') or data.get('duration_hours') or 2)
            fare = int(data.get('totalFare') or data.get('total_fare') or 500)
            client_id = 3  # default demo client Ramesh Sen
            booking_code = f"BK-COMP-{uuid.uuid4().hex[:6].upper()}"

            cursor.execute("""
                INSERT INTO bookings (booking_code, client_id, companion_id, service_type, booking_date, booking_time, duration_hours, pickup_address, destination_address, status, otp, total_fare, payment_status, completed_at)
                VALUES (%s, %s, %s, %s, CURDATE(), '10:00', %s, %s, %s, 'COMPLETED', '1234', %s, 'PAID', CURRENT_TIMESTAMP)
            """, (booking_code, client_id, companion_user_id, service_type, hours, pickup, dest, fare))
            conn.commit()
            real_db_id = cursor.lastrowid
        else:
            real_db_id = booking['id']
            cursor.execute("""
                UPDATE bookings 
                SET status = 'COMPLETED', 
                    payment_status = 'PAID', 
                    completed_at = CURRENT_TIMESTAMP,
                    companion_id = COALESCE(companion_id, %s)
                WHERE id = %s
            """, (companion_user_id, real_db_id))
            conn.commit()

        cursor.execute("""
            SELECT b.*, u.full_name as clientName 
            FROM bookings b 
            JOIN users u ON b.client_id = u.id 
            WHERE b.id = %s
        """, (real_db_id,))
        updated_booking = cursor.fetchone()

        return jsonify({
            'success': True,
            'message': 'Booking marked as COMPLETED. Jobs count and earnings updated.',
            'booking': updated_booking
        })
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/companion/history', methods=['GET'])
def api_companion_history():
    companion_user_id = session.get('user_id') if (session.get('role') == 'companion') else 2
    filter_period = request.args.get('filter_period') or request.args.get('period') or 'all'
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    status_filter = request.args.get('status', 'all').strip()

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        # 1. Lifetime Stats for Companion
        cursor.execute("""
            SELECT 
                COUNT(*) as lifetime_jobs,
                COALESCE(SUM(total_fare), 0) as lifetime_earnings
            FROM bookings 
            WHERE (companion_id = %s OR companion_id = 2 OR companion_id IS NULL) AND status = 'COMPLETED'
        """, (companion_user_id,))
        raw_lt = cursor.fetchone() or {}
        lifetime_stats = {
            'lifetime_jobs': int(raw_lt.get('lifetime_jobs') or 0),
            'lifetime_earnings': float(raw_lt.get('lifetime_earnings') or 0)
        }

        # 2. Date Clause for Period Stats
        date_sql, date_params = build_date_range_condition(filter_period, start_date, end_date, "COALESCE(b.completed_at, b.created_at)")

        # Period Stats Query
        period_sql = f"""
            SELECT 
                COUNT(*) as period_jobs,
                COALESCE(SUM(total_fare), 0) as period_earnings
            FROM bookings b
            WHERE (b.companion_id = %s OR b.companion_id = 2 OR b.companion_id IS NULL) AND b.status = 'COMPLETED' AND ({date_sql})
        """
        cursor.execute(period_sql, [companion_user_id] + date_params)
        raw_pd = cursor.fetchone() or {}
        period_stats = {
            'period_jobs': int(raw_pd.get('period_jobs') or 0),
            'period_earnings': float(raw_pd.get('period_earnings') or 0)
        }

        # 3. History List Query
        where_clauses = ["(b.companion_id = %s OR b.companion_id = 2 OR b.companion_id IS NULL)", f"({date_sql})"]
        query_params = [companion_user_id] + date_params

        if status_filter != 'all':
            where_clauses.append("b.status = %s")
            query_params.append(status_filter)

        history_sql = f"""
            SELECT b.*, u.full_name as clientName, u.phone as clientPhone
            FROM bookings b 
            JOIN users u ON b.client_id = u.id 
            WHERE {" AND ".join(where_clauses)}
            ORDER BY b.id DESC
        """
        cursor.execute(history_sql, query_params)
        history = cursor.fetchall()

        return jsonify({
            'success': True,
            'filter_period': filter_period,
            'lifetime': lifetime_stats,
            'period': period_stats,
            'history': history
        })
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/client/history', methods=['GET'])
def api_client_history():
    client_user_id = session.get('user_id') or 3
    filter_period = request.args.get('filter_period') or request.args.get('period') or 'all'
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    status_filter = request.args.get('status', 'all').strip()

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        date_sql, date_params = build_date_range_condition(filter_period, start_date, end_date, "COALESCE(b.completed_at, b.created_at)")

        where_clauses = ["b.client_id = %s", f"({date_sql})"]
        query_params = [client_user_id] + date_params

        if status_filter != 'all':
            where_clauses.append("b.status = %s")
            query_params.append(status_filter)

        history_sql = f"""
            SELECT b.*, 
                   c.full_name as companionName, 
                   c.phone as companionPhone,
                   comp.rating as companionRating,
                   comp.hourly_rate as companionHourlyRate
            FROM bookings b 
            LEFT JOIN users c ON b.companion_id = c.id 
            LEFT JOIN companions comp ON c.id = comp.user_id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY b.id DESC
        """
        cursor.execute(history_sql, query_params)
        history = cursor.fetchall()

        # Summary statistics for client
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bookings,
                COALESCE(SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END), 0) as completed_bookings,
                COALESCE(SUM(CASE WHEN status = 'COMPLETED' THEN total_fare ELSE 0 END), 0) as total_spent
            FROM bookings
            WHERE client_id = %s
        """, (client_user_id,))
        raw_sm = cursor.fetchone() or {}
        summary = {
            'total_bookings': int(raw_sm.get('total_bookings') or 0),
            'completed_bookings': int(raw_sm.get('completed_bookings') or 0),
            'total_spent': float(raw_sm.get('total_spent') or 0)
        }

        return jsonify({
            'success': True,
            'summary': summary,
            'history': history
        })
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# =========================================================
# ADMIN APIs
# =========================================================

@app.route('/api/admin/stats', methods=['GET'])
def api_admin_stats():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'client'")
        clients_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'companion'")
        companions_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM verifications WHERE status = 'pending'")
        pending_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE status IN ('SEARCHING', 'ACCEPTED', 'IN_TRANSIT')")
        active_bookings = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE status = 'IN_TRANSIT'")
        active_rides = cursor.fetchone()['count']

        return jsonify({
            'success': True,
            'stats': {
                'clients': clients_count,
                'companions': companions_count,
                'pendingVerifications': pending_count,
                'activeBookings': active_bookings,
                'activeRides': active_rides
            }
        })
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/admin/clients', methods=['GET'])
def api_admin_clients():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, full_name, phone, age, gender, address, emergency_contact, status, created_at FROM users WHERE role = 'client' ORDER BY id DESC")
        clients = cursor.fetchall()
        return jsonify({'success': True, 'clients': clients})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/admin/companions', methods=['GET'])
def api_admin_companions():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id as user_id, u.username, u.email, u.full_name, u.phone, u.age, u.gender, u.address, u.status as user_status,
                   c.id as companion_id, c.city, c.preferred_service, c.hourly_rate, c.rating, c.verification_status, c.document_name
            FROM users u
            LEFT JOIN companions c ON u.id = c.user_id
            WHERE u.role = 'companion'
            ORDER BY u.id DESC
        """)
        companions = cursor.fetchall()
        return jsonify({'success': True, 'companions': companions})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/admin/verifications', methods=['GET'])
def api_admin_verifications():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM verifications ORDER BY id DESC")
        verifs = cursor.fetchall()
        return jsonify({'success': True, 'verifications': verifs})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/api/admin/verify-companion/<int:verif_id>', methods=['POST'])
def api_verify_companion(verif_id):
    data = request.get_json() or request.form
    action = data.get('action', 'approve').lower()
    new_status = 'approved' if action == 'approve' else 'rejected'
    comp_status = 'verified' if action == 'approve' else 'rejected'

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT companion_id FROM verifications WHERE id = %s", (verif_id,))
        verif = cursor.fetchone()

        if verif:
            cursor.execute("UPDATE verifications SET status = %s WHERE id = %s", (new_status, verif_id))
            cursor.execute("UPDATE companions SET verification_status = %s WHERE user_id = %s", (comp_status, verif['companion_id']))
            conn.commit()

        return jsonify({'success': True, 'status': new_status})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# =========================================================
# MAIN DRIVER
# =========================================================

if __name__ == '__main__':
    print("==================================================")
    print("  Starting ElderGo+ Full-Stack Flask Web Server   ")
    print("==================================================")
    print(f"  Connected to MySQL Database: '{DB_NAME}' on {DB_HOST}:{DB_PORT}")
    print("  URL: http://127.0.0.1:5000")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
