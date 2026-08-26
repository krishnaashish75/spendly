import re
from pathlib import Path

import pytest

from database import db


@pytest.fixture
def client(monkeypatch, tmp_path):
    database_path = tmp_path / "expense_tracker.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db()

    from app import app

    app.config.update(TESTING=True, SECRET_KEY="testing-secret-key")
    with app.test_client() as test_client:
        yield test_client


def create_test_user(name, email, password="password123"):
    assert db.create_user(name, email, password)

    connection = db.get_db()
    try:
        return connection.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        connection.close()


def set_created_at(user_id, created_at):
    connection = db.get_db()
    try:
        connection.execute(
            "UPDATE users SET created_at = ? WHERE id = ?",
            (created_at, user_id),
        )
        connection.commit()
    finally:
        connection.close()


def test_get_user_profile_returns_only_safe_fields(client):
    user = create_test_user("Ada Lovelace", "ada@example.com")

    profile = db.get_user_profile(user["id"])

    assert set(profile.keys()) == {"id", "name", "email", "created_at"}
    assert profile["id"] == user["id"]
    assert profile["name"] == "Ada Lovelace"
    assert profile["email"] == "ada@example.com"
    assert "password_hash" not in profile.keys()
    assert db.get_user_profile(99999) is None


def test_anonymous_profile_redirects_to_login_without_account_data(client):
    create_test_user("Ada Lovelace", "ada@example.com")

    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert b"Ada Lovelace" not in response.data
    assert b"ada@example.com" not in response.data


def test_profile_shows_the_authenticated_users_safe_details(client):
    create_test_user("Ada Lovelace", "ada@example.com")
    grace = create_test_user("Grace Hopper", "grace@example.com")
    set_created_at(grace["id"], "2025-01-15 12:00:00")

    with client.session_transaction() as current_session:
        current_session["user_id"] = grace["id"]

    response = client.get("/profile")

    assert response.status_code == 200
    assert b"Hello, Grace Hopper" in response.data
    assert b">G</span>" in response.data
    assert b"grace@example.com" in response.data
    assert b"Ada Lovelace" not in response.data
    assert b"ada@example.com" not in response.data
    assert b"January 15, 2025" in response.data
    assert b'datetime="2025-01-15"' in response.data
    assert b'href="/static/css/profile.css"' in response.data
    assert b'action="/logout" method="GET"' in response.data
    assert b">Sign out</button>" in response.data


def test_profile_never_renders_password_data(client):
    password = "private-password"
    user = create_test_user("Ada Lovelace", "ada@example.com", password)

    with client.session_transaction() as current_session:
        current_session["user_id"] = user["id"]

    response = client.get("/profile")

    assert password.encode() not in response.data
    assert user["password_hash"].encode() not in response.data


def test_stale_profile_session_is_cleared_and_redirected_to_login(client):
    with client.session_transaction() as current_session:
        current_session["user_id"] = 99999
        current_session["unrelated_key"] = "remove me"

    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    with client.session_transaction() as current_session:
        assert not current_session


def test_profile_styles_are_scoped_and_include_a_narrow_layout():
    stylesheet_path = (
        Path(__file__).resolve().parents[1] / "static" / "css" / "profile.css"
    )
    stylesheet = stylesheet_path.read_text(encoding="utf-8")
    selectors = re.findall(r"(?<![\w\d-])\.([a-z][\w-]*)", stylesheet)

    assert selectors
    assert all(selector.startswith("profile-") for selector in selectors)
    assert "@media (max-width: 600px)" in stylesheet
    assert "grid-template-columns: 1fr;" in stylesheet
    assert "#" not in stylesheet
    assert "rgb(" not in stylesheet.lower()
