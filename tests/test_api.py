def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_duplicate_username(client):
    body = {"username": "dup", "password": "secret123", "role": "viewer"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 400


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"username": "u1", "password": "rightpass", "role": "admin"},
    )
    r = client.post(
        "/auth/login",
        json={"username": "u1", "password": "wrong"},
    )
    assert r.status_code == 401


def test_transactions_list_pagination_shape(client, admin_token):
    h = {"Authorization": f"Bearer {admin_token}"}
    r = client.get("/transactions", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert data["skip"] == 0
    assert isinstance(data["items"], list)


def test_crud_with_jwt_admin(client, admin_token):
    h = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        "/transactions",
        headers=h,
        json={
            "amount": 100,
            "type": "expense",
            "category": "Food",
            "date": "2026-04-01",
            "note": "test",
        },
    )
    assert r.status_code == 201
    tid = r.json()["id"]

    r = client.get("/transactions", headers=h)
    assert r.json()["total"] >= 1

    r = client.patch(
        f"/transactions/{tid}",
        headers=h,
        json={"note": "updated"},
    )
    assert r.status_code == 200
    assert r.json()["note"] == "updated"

    r = client.delete(f"/transactions/{tid}", headers=h)
    assert r.status_code == 204


def test_viewer_cannot_filter(client, viewer_token, admin_token):
    ah = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/transactions",
        headers=ah,
        json={
            "amount": 50,
            "type": "expense",
            "category": "X",
            "date": "2026-04-01",
            "note": "",
        },
    )
    vh = {"Authorization": f"Bearer {viewer_token}"}
    r = client.get("/transactions", params={"category": "X"}, headers=vh)
    assert r.status_code == 403


def test_demo_admin_without_header(client):
    r = client.post(
        "/transactions",
        json={
            "amount": 10,
            "type": "income",
            "category": "Misc",
            "date": "2026-04-01",
            "note": "",
        },
    )
    assert r.status_code == 201


def test_negative_amount_422(client):
    r = client.post(
        "/transactions",
        json={
            "amount": -5,
            "type": "expense",
            "category": "x",
            "date": "2026-04-01",
        },
    )
    assert r.status_code == 422


def test_summary_analyst(client, admin_token):
    h = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/auth/register",
        json={"username": "analyst1", "password": "secret123", "role": "analyst"},
    )
    r = client.post(
        "/auth/login",
        json={"username": "analyst1", "password": "secret123"},
    )
    ah = {"Authorization": f"Bearer {r.json()['access_token']}"}
    out = client.get("/summary", headers=ah)
    assert out.status_code == 200
    j = out.json()
    assert "category_breakdown" in j and "monthly_summary" in j
