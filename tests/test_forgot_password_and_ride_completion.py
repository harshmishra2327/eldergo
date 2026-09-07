import unittest
import uuid
import datetime
from app import app, get_db_connection

class TestForgotPasswordAndRideCompletion(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.random_id = str(uuid.uuid4())[:8]
        self.email = f"user_{self.random_id}@test.com"
        self.phone = f"987{self.random_id[:7]}"
        self.username = f"uname_{self.random_id}"
        self.password = "original_pass123"
        self.new_password = "new_secret_pass456"

    def test_forgot_password_via_email_and_mobile(self):
        # 1. Register user with email and phone
        res_reg = self.client.post("/api/register", json={
            "role": "client",
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "fullName": "Test Forgot User",
            "phone": self.phone
        })
        self.assertEqual(res_reg.status_code, 200)
        self.assertTrue(res_reg.get_json().get("success"))

        # 2. Verify account by Email
        res_v_email = self.client.post("/api/forgot-password/verify", json={
            "identifier": self.email
        })
        self.assertEqual(res_v_email.status_code, 200)
        json_v_email = res_v_email.get_json()
        self.assertTrue(json_v_email.get("success"))
        self.assertIn("sms_alert", json_v_email)
        self.assertIn("1234", json_v_email["sms_alert"])

        # 3. Verify account by Mobile Number
        res_v_phone = self.client.post("/api/forgot-password/verify", json={
            "identifier": self.phone
        })
        self.assertEqual(res_v_phone.status_code, 200)
        json_v_phone = res_v_phone.get_json()
        self.assertTrue(json_v_phone.get("success"))
        self.assertIn("sms_alert", json_v_phone)

        # 4. Reset password using mobile number & OTP
        res_reset = self.client.post("/api/forgot-password/reset", json={
            "identifier": self.phone,
            "otp": "1234",
            "password": self.new_password
        })
        self.assertEqual(res_reset.status_code, 200)
        json_reset = res_reset.get_json()
        self.assertTrue(json_reset.get("success"))
        self.assertIn("sms_alert", json_reset)
        self.assertIn("changed successfully", json_reset["sms_alert"])

        # 5. Log in with new password using Username, Email, AND Phone number
        res_login_uname = self.client.post("/api/login", json={
            "username": self.username,
            "password": self.new_password
        })
        self.assertTrue(res_login_uname.get_json().get("success"))

        res_login_email = self.client.post("/api/login", json={
            "username": self.email,
            "password": self.new_password
        })
        self.assertTrue(res_login_email.get_json().get("success"))

        res_login_phone = self.client.post("/api/login", json={
            "username": self.phone,
            "password": self.new_password
        })
        self.assertTrue(res_login_phone.get_json().get("success"))

    def test_companion_ride_completion_updates_jobs_income_and_history(self):
        # 1. Register companion user
        comp_uname = f"comp_{self.random_id}"
        res_cp = self.client.post("/api/register", json={
            "role": "companion",
            "username": comp_uname,
            "email": f"{comp_uname}@test.com",
            "password": "pass",
            "fullName": "Duty Companion",
            "phone": "9988776655"
        })
        comp_user_id = res_cp.get_json()["user"]["id"]

        # 2. Set companion session
        with self.client.session_transaction() as sess:
            sess["user_id"] = comp_user_id
            sess["username"] = comp_uname
            sess["role"] = "companion"

        # 3. Complete a ride via API
        res_comp = self.client.post("/api/bookings/99999/complete", json={
            "serviceType": "Medical & Hospital Visit",
            "pickup": "Koramangala, Bengaluru",
            "destination": "Manipal Hospital",
            "duration": 3,
            "totalFare": 750
        })
        self.assertEqual(res_comp.status_code, 200)
        data_comp = res_comp.get_json()
        self.assertTrue(data_comp.get("success"))
        self.assertEqual(data_comp["booking"]["status"], "COMPLETED")

        # 4. Check companion history API returns updated job count and income
        res_hist = self.client.get("/api/companion/history?period=all")
        self.assertEqual(res_hist.status_code, 200)
        hist_data = res_hist.get_json()
        self.assertTrue(hist_data.get("success"))
        self.assertGreaterEqual(hist_data["lifetime"]["lifetime_jobs"], 1)
        self.assertGreaterEqual(hist_data["lifetime"]["lifetime_earnings"], 750)
        self.assertGreaterEqual(len(hist_data["history"]), 1)

if __name__ == "__main__":
    unittest.main()
