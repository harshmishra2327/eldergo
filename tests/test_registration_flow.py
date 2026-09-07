import sys
import unittest
import uuid
from app import app, get_db_connection

class TestRegistrationFlow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.random_id = str(uuid.uuid4())[:8]

    def test_client_registration_stores_in_db(self):
        username = f"testclient_{self.random_id}"
        email = f"{username}@example.com"
        payload = {
            "role": "client",
            "username": username,
            "email": email,
            "password": "Password123!",
            "fullName": "Test Client User",
            "phone": "9876543210",
            "age": 75,
            "gender": "Female",
            "address": "123 Main St, Bengaluru",
            "emergencyContact": "Son - 9988776655"
        }

        response = self.client.post("/api/register", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], username)

        # Verify DB storage
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(user_row)
        self.assertEqual(user_row["email"], email)
        self.assertEqual(user_row["role"], "client")
        self.assertEqual(user_row["full_name"], "Test Client User")
        self.assertEqual(user_row["age"], 75)
        self.assertEqual(user_row["gender"], "Female")
        self.assertEqual(user_row["emergency_contact"], "Son - 9988776655")

    def test_companion_registration_stores_in_db(self):
        username = f"testcomp_{self.random_id}"
        email = f"{username}@example.com"
        payload = {
            "role": "companion",
            "username": username,
            "email": email,
            "password": "Password123!",
            "fullName": "Test Companion User",
            "phone": "9123456789",
            "age": 30,
            "gender": "Male",
            "address": "456 Side St, Bengaluru",
            "city": "Bengaluru",
            "preferredService": "Hospital Visit",
            "hourlyRate": "300"
        }

        response = self.client.post("/api/register", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))

        # Verify DB storage
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()

        cursor.execute("SELECT * FROM companions WHERE user_id = %s", (user_row["id"],))
        comp_row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(user_row)
        self.assertEqual(user_row["age"], 30)
        self.assertIsNotNone(comp_row)
        self.assertEqual(comp_row["hourly_rate"], 300)

    def test_admin_clients_and_companions_api(self):
        res_clients = self.client.get("/api/admin/clients")
        self.assertEqual(res_clients.status_code, 200)
        data_c = res_clients.get_json()
        self.assertTrue(data_c.get("success"))
        self.assertIsInstance(data_c.get("clients"), list)

        res_comps = self.client.get("/api/admin/companions")
        self.assertEqual(res_comps.status_code, 200)
        data_comp = res_comps.get_json()
        self.assertTrue(data_comp.get("success"))
        self.assertIsInstance(data_comp.get("companions"), list)

    def test_duplicate_registration_prevented(self):
        # Register user once
        username = f"dup_{self.random_id}"
        email = f"{username}@example.com"
        payload = {
            "role": "client",
            "username": username,
            "email": email,
            "password": "Password123!",
            "fullName": "Duplicate User",
            "phone": "9876543210",
            "address": "123 Main St"
        }
        res1 = self.client.post("/api/register", json=payload)
        self.assertEqual(res1.status_code, 200)

        # Register again with same username/email
        res2 = self.client.post("/api/register", json=payload)
        self.assertEqual(res2.status_code, 400)
        data2 = res2.get_json()
        self.assertFalse(data2.get("success"))
        self.assertIn("already registered", data2.get("message"))

if __name__ == "__main__":
    unittest.main()
