def _auth_headers(client, email="test@example.com"):
    response = client.post(
        "/auth/register",
        json={
            "name": "Tester",
            "email": email,
            "password": "password123",
        },
    )
    if response.status_code == 409:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_settings(client):
    auth_headers = _auth_headers(client)
    # Setup test user preference
    # (By default test user might have send_reminder_email=True)
    res = client.get("/auth/settings", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "send_reminder_email" in data
    assert data["send_reminder_email"] is True

def test_put_settings(client):
    auth_headers = _auth_headers(client)
    res = client.put(
        "/auth/settings", 
        json={"send_reminder_email": False}, 
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["send_reminder_email"] is False

    # Verify GET reflects the change
    res2 = client.get("/auth/settings", headers=auth_headers)
    assert res2.get_json()["send_reminder_email"] is False
