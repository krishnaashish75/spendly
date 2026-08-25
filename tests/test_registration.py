import pytest
from werkzeug.security import check_password_hash

from database import db


@pytest.fixture
def client(monkeypatch, tmp_path):
    database_path = tmp_path / "expense_tracker.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db()

    from app import app

    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def get_user(email):
    connection = db.get_db()

    try:
        return connection.execute(
            "SELECT name, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        connection.close()


def user_count():
    connection = db.get_db()

    try:
        return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        connection.close()


def test_register_page_loads(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b'action="/register"' in response.data
    assert b'href="/login"' in response.data
    assert b'minlength="8"' in response.data


def test_registration_creates_user_with_hashed_password(client):
    response = client.post(
        "/register",
        data={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    user = get_user("ada@example.com")
    assert user["name"] == "Ada Lovelace"
    assert user["email"] == "ada@example.com"
    assert user["password_hash"] != "password123"
    assert check_password_hash(user["password_hash"], "password123")


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (
            {"name": "", "email": "ada@example.com", "password": "password123"},
            "Please enter your full name.",
        ),
        (
            {"name": "Ada Lovelace", "email": "", "password": "password123"},
            "Please enter your email address.",
        ),
        (
            {"name": "Ada Lovelace", "email": "ada@example.com", "password": ""},
            "Please enter a password.",
        ),
        (
            {"name": "Ada Lovelace", "email": "ada@example.com", "password": "short"},
            "Password must be at least 8 characters.",
        ),
    ],
)
def test_registration_rejects_invalid_input(client, data, error):
    initial_user_count = user_count()

    response = client.post("/register", data=data)

    assert response.status_code == 200
    assert error.encode() in response.data
    assert user_count() == initial_user_count


def test_registration_rejects_duplicate_email(client):
    registration_data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "password123",
    }
    client.post("/register", data=registration_data)

    response = client.post("/register", data=registration_data)

    assert response.status_code == 200
    assert b"An account with that email address already exists." in response.data

    connection = db.get_db()
    try:
        matching_users = connection.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?",
            ("ada@example.com",),
        ).fetchone()[0]
    finally:
        connection.close()

    assert matching_users == 1


def test_failed_registration_preserves_name_and_email_not_password(client):
    response = client.post(
        "/register",
        data={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "short",
        },
    )

    assert b'value="Ada Lovelace"' in response.data
    assert b'value="ada@example.com"' in response.data
    assert b'value="short"' not in response.data
