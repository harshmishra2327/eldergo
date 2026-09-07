import unittest
import uuid
import datetime
from app import app, get_db_connection

class TestBookingCompletionAndHistory(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.random_id = str(uuid.uuid4())[:8]

    def test_complete_booking_updates_db_and_returns_history_stats(self):
        # 1. Create client & companion
        client_name = f"Client_{self.random_id}"
        comp_name = f"Comp_{self.random_id}"

        res_c = self.client.post("/api/register", json={
            "role": "client", "username": client_name, "email": f"{client_name}@ex.com",
            "password": "pass", "fullName": "Client User", "phone": "9876543210"
        })
        client_user_id = res_c.get_json()["user"]["id"]

        res_cp = self.client.post("/api/register", json={
            "role": "companion", "username": comp_name, "email": f"{comp_name}@ex.com",
            "password": "pass", "fullName": "Companion User", "phone": "9123456789"
        })
        comp_user_id = res_cp.get_json()["user"]["id"]

        # 2. Create booking in DB for this client
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        code = "BK-TEST-" + self.random_id
        cursor.execute("""
            INSERT INTO bookings (booking_code, client_id, companion_id, service_type, booking_date, booking_time, duration_hours, pickup_address, destination_address, status, otp, hourly_rate, total_fare, payment_status)
            VALUES (%s, %s, NULL, 'Medical & Hospital Visit', '2026-09-02', '10:30', 2, 'Pickup Point', 'Dest Hospital', 'SEARCHING', '1234', 300, 650, 'UNPAID')
            """, (code, client_user_id))
        booking_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        with self.client.session_transaction() as sess:
            sess["user_id"] = comp_user_id
            sess["role"] = "companion"

        res_requests = self.client.get("/api/bookings/companion/requests")
        self.assertEqual(res_requests.status_code, 200)
        request_data = res_requests.get_json()
        self.assertTrue(request_data.get("success"))
        matching_request = next(item for item in request_data["requests"] if item["booking_code"] == code)
        self.assertEqual(matching_request["clientName"], "Client User")

        res_decline = self.client.post(f"/api/bookings/{booking_id}/decline")
        self.assertEqual(res_decline.status_code, 200)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM bookings WHERE id = %s", (booking_id,))
        self.assertEqual(cursor.fetchone()["status"], "CANCELLED")
        cursor.close()
        conn.close()

        cursor = None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookings SET status = 'SEARCHING', companion_id = NULL WHERE id = %s
        """, (booking_id,))
        conn.commit()
        cursor.close()
        conn.close()

        res_accept = self.client.post(f"/api/bookings/{booking_id}/accept")
        self.assertEqual(res_accept.status_code, 200)
        self.assertEqual(res_accept.get_json()["booking"]["clientName"], "Client User")

        # 3. Complete booking via API
        res_comp = self.client.post(f"/api/bookings/{booking_id}/complete")
        self.assertEqual(res_comp.status_code, 200)
        data_comp = res_comp.get_json()
        self.assertTrue(data_comp.get("success"))
        self.assertIsNotNone(data_comp["booking"]["completed_at"])

        # 4. Test Companion History API with session
        with self.client.session_transaction() as sess:
            sess["user_id"] = comp_user_id

        res_hist = self.client.get("/api/companion/history?period=today")
        self.assertEqual(res_hist.status_code, 200)
        hist_data = res_hist.get_json()
        self.assertTrue(hist_data.get("success"))
        self.assertGreaterEqual(hist_data["lifetime"]["lifetime_jobs"], 1)
        self.assertGreaterEqual(hist_data["lifetime"]["lifetime_earnings"], 650)
        self.assertGreaterEqual(hist_data["period"]["period_jobs"], 1)
        self.assertGreaterEqual(hist_data["period"]["period_earnings"], 650)
        self.assertGreaterEqual(len(hist_data["history"]), 1)
        self.assertEqual(hist_data["history"][0]["booking_code"], code)
        self.assertEqual(hist_data["history"][0]["clientName"], "Client User")

        # Test date range filters (this_month, this_year, custom, all)
        res_month = self.client.get("/api/companion/history?period=this_month")
        self.assertGreaterEqual(res_month.get_json()["period"]["period_jobs"], 1)

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        res_custom = self.client.get(f"/api/companion/history?period=custom&start_date={today_str}&end_date={today_str}")
        self.assertGreaterEqual(res_custom.get_json()["period"]["period_jobs"], 1)

        # 5. Test Client History API with session
        with self.client.session_transaction() as sess:
            sess["user_id"] = client_user_id

        res_c_hist = self.client.get("/api/client/history?period=today")
        self.assertEqual(res_c_hist.status_code, 200)
        c_hist_data = res_c_hist.get_json()
        self.assertTrue(c_hist_data.get("success"))
        self.assertEqual(c_hist_data["summary"]["total_bookings"], 1)
        self.assertEqual(c_hist_data["summary"]["completed_bookings"], 1)
        self.assertEqual(c_hist_data["summary"]["total_spent"], 650)
        self.assertEqual(len(c_hist_data["history"]), 1)
        self.assertEqual(c_hist_data["history"][0]["companionName"], "Companion User")

if __name__ == "__main__":
    unittest.main()
