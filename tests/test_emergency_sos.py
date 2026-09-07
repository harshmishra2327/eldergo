from app import app


def test_normalize_emergency_phone_number():
    from app import normalize_phone_number

    assert normalize_phone_number("Ramesh (Son) - 9876543210") == "9876543210"
    assert normalize_phone_number("+91 98765 43210") == "919876543210"


def test_emergency_endpoint_uses_user_contact(monkeypatch):
    client = app.test_client()

    class FakeCursor:
        def __init__(self):
            self.last_query = None

        def execute(self, query, params=None):
            self.last_query = query

        def fetchone(self):
            return {"emergency_contact": "Ramesh (Son) - 9876543210"}

        def close(self):
            pass

    class FakeConn:
        def cursor(self, dictionary=True):
            return FakeCursor()

        def commit(self):
            pass

        def close(self):
            pass

        @property
        def is_connected(self):
            return True

    monkeypatch.setattr("app.get_db_connection", lambda: FakeConn())
    monkeypatch.setattr("app.send_emergency_sms", lambda phone, message: {"success": True, "phone": phone, "message": message})

    with client.session_transaction() as session:
        session["user_id"] = 3

    response = client.post("/api/emergency/sos", json={})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["phone"] == "9876543210"
