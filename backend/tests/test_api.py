from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_register_login():
    r = client.post(
        "/api/auth/register",
        json={"email": "tester@hillguard.local", "password": "testersPass1", "display_name": "Tester"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    login = client.post("/api/auth/login", json={"email": "tester@hillguard.local", "password": "testersPass1"})
    assert login.status_code == 200


def test_login_seed_admin():
    r = client.post("/api/auth/login", json={"email": "admin@hillguard.local", "password": "HillGuardAdmin123!"})
    assert r.status_code == 200
    assert r.json()["role"] == "ADMIN"


def test_incidents_list_and_filter():
    r = client.get("/api/incidents")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    f = client.get("/api/incidents", params={"category": "landslide"})
    assert f.status_code == 200
    for item in f.json()["items"]:
        assert item["category"] == "landslide"


def test_incident_create():
    r = client.post(
        "/api/incidents",
        data={
            "category": "landslide",
            "description": "Test debris near a road for automated tests.",
            "latitude": "31.71",
            "longitude": "76.93",
            "observed_at": "2026-10-03T12:00:00+00:00",
            "location_label": "Mandi, Himachal Pradesh",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "unverified"
    assert body["report_id"]
    got = client.get(f"/api/incidents/{body['report_id']}")
    assert got.status_code == 200


def test_nearby():
    r = client.get("/api/incidents/nearby", params={"lat": 31.7084, "lng": 76.932, "km": 20})
    assert r.status_code == 200
    assert "items" in r.json()


def test_admin_verify():
    created = client.post(
        "/api/incidents",
        data={
            "category": "flood",
            "description": "Test water on roadway.",
            "latitude": "32.22",
            "longitude": "76.32",
            "observed_at": "2026-10-03T10:00:00+00:00",
        },
    )
    rid = created.json()["report_id"]
    login = client.post("/api/auth/login", json={"email": "admin@hillguard.local", "password": "HillGuardAdmin123!"})
    token = login.json()["access_token"]
    patched = client.patch(
        f"/api/admin/reports/{rid}/status",
        json={"verification_status": "verified", "reviewer_notes": "Looks consistent with other reports."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patched.status_code == 200
    assert patched.json()["verification_status"] == "verified"
    pub = client.get(f"/api/incidents/{rid}")
    assert pub.json()["verification_status"] == "verified"


def test_user_cannot_admin():
    login = client.post("/api/auth/login", json={"email": "user@hillguard.local", "password": "HillGuardUser123!"})
    token = login.json()["access_token"]
    r = client.get("/api/admin/reports", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_risk_and_clusters_and_analytics():
    r = client.post("/api/ai/risk", json={"latitude": 31.7084, "longitude": 76.932})
    assert r.status_code == 200
    assert r.json()["risk_category"] in {"Lower", "Moderate", "Elevated", "Higher"}
    c = client.get("/api/clusters")
    assert c.status_code == 200
    a = client.get("/api/analytics")
    assert a.status_code == 200
    assert "kpis" in a.json()


def test_route_analyze():
    r = client.post("/api/routes/analyze", json={"start": "Shimla", "destination": "Manali"})
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body
    assert "does not guarantee" in body["summary"]["disclaimer"].lower()


def test_invalid_upload_rejected():
    r = client.post(
        "/api/incidents",
        data={
            "category": "other",
            "description": "bad file",
            "latitude": "31.1",
            "longitude": "77.1",
            "observed_at": "2026-10-03T10:00:00+00:00",
        },
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
