import pytest

from database import db


@pytest.fixture
def client(monkeypatch, tmp_path):
    database_path = tmp_path / "expense_tracker.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db()
    db.seed_db()

    from app import app

    app.config.update(TESTING=True, SECRET_KEY="testing-secret-key")
    with app.test_client() as test_client:
        yield test_client


def create_test_user():
    db.create_user("Ada Lovelace", "ada@example.com", "password123")


def get_user_id(email):
    connection = db.get_db()

    try:
        return connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()["id"]
    finally:
        connection.close()


def get_user_count():
    connection = db.get_db()

    try:
        return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        connection.close()


def test_login_page_loads(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b'value=""' in response.data


def test_authenticate_user_verifies_credentials(client):
    create_test_user()

    user = db.authenticate_user("ada@example.com", "password123")

    assert user["id"] == get_user_id("ada@example.com")
    assert db.authenticate_user("ada@example.com", "wrong-password") is None
    assert db.authenticate_user("unknown@example.com", "password123") is None


def test_login_creates_session_and_redirects_to_profile(client):
    create_test_user()
    user_id = get_user_id("ada@example.com")

    with client.session_transaction() as current_session:
        current_session["unrelated_key"] = "remove me"

    response = client.post(
        "/login",
        data={"email": "ada@example.com", "password": "password123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"
    with client.session_transaction() as current_session:
        assert dict(current_session) == {"user_id": user_id}


def test_login_accepts_seeded_demo_credentials(client):
    response = client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"


def test_login_trims_email_but_not_password(client):
    create_test_user()

    response = client.post(
        "/login",
        data={"email": "  ada@example.com  ", "password": "password123"},
    )

    assert response.status_code == 302

    client.get("/logout")
    response = client.post(
        "/login",
        data={"email": "ada@example.com", "password": " password123 "},
    )

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


@pytest.mark.parametrize(
    ("data", "error"),
    [
        ({"email": "", "password": "password123"}, "Please enter your email address."),
        ({"email": "ada@example.com", "password": ""}, "Please enter your password."),
    ],
)
def test_login_rejects_missing_fields(client, data, error):
    response = client.post("/login", data=data)

    assert response.status_code == 200
    assert error.encode() in response.data
    with client.session_transaction() as current_session:
        assert "user_id" not in current_session


def test_invalid_credentials_share_error_and_never_render_password(client):
    create_test_user()
    submitted_email = "ada@example.com"
    submitted_password = "not-the-password"

    wrong_password = client.post(
        "/login",
        data={"email": submitted_email, "password": submitted_password},
    )
    unknown_email = client.post(
        "/login",
        data={"email": "unknown@example.com", "password": submitted_password},
    )

    assert b"Invalid email or password." in wrong_password.data
    assert b"Invalid email or password." in unknown_email.data
    assert b'value="ada@example.com"' in wrong_password.data
    assert submitted_password.encode() not in wrong_password.data
    with client.session_transaction() as current_session:
        assert "user_id" not in current_session


def test_authenticated_session_persists_and_updates_navigation(client):
    create_test_user()
    client.post(
        "/login",
        data={"email": "ada@example.com", "password": "password123"},
    )

    response = client.get("/")

    assert b'href="/profile">Profile</a>' in response.data
    assert b'href="/logout" class="nav-cta">Sign out</a>' in response.data
    assert b">Sign in</a>" not in response.data
    assert b">Get started</a>" not in response.data


def test_anonymous_navigation_shows_auth_links(client):
    response = client.get("/")

    assert b'href="/login">Sign in</a>' in response.data
    assert b'href="/register" class="nav-cta">Get started</a>' in response.data
    assert b">Profile</a>" not in response.data
    assert b">Sign out</a>" not in response.data


def test_logout_clears_session_and_redirects_to_landing(client):
    with client.session_transaction() as current_session:
        current_session["user_id"] = 1
        current_session["unrelated_key"] = "remove me"

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with client.session_transaction() as current_session:
        assert not current_session


def test_anonymous_logout_is_harmless(client):
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


@pytest.mark.parametrize(
    ("path", "method", "data"),
    [
        ("/login", "GET", None),
        (
            "/login",
            "POST",
            {"email": "demo@spendly.com", "password": "demo123"},
        ),
        ("/register", "GET", None),
        (
            "/register",
            "POST",
            {
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "password": "password123",
            },
        ),
    ],
)
def test_authenticated_user_is_redirected_from_auth_routes(
    client,
    path,
    method,
    data,
):
    with client.session_transaction() as current_session:
        current_session["user_id"] = 1
        current_session["unrelated_key"] = "preserve me"

    initial_user_count = get_user_count()
    response = client.open(path, method=method, data=data)

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"
    assert get_user_count() == initial_user_count
    with client.session_transaction() as current_session:
        assert dict(current_session) == {
            "user_id": 1,
            "unrelated_key": "preserve me",
        }


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/expenses/add", b"Add expense \xe2\x80\x94 coming in Step 7"),
        ("/expenses/1/edit", b"Edit expense \xe2\x80\x94 coming in Step 8"),
        ("/expenses/1/delete", b"Delete expense \xe2\x80\x94 coming in Step 9"),
    ],
)
def test_expense_routes_remain_unchanged_stubs(client, path, body):
    response = client.get(path)

    assert response.status_code == 200
    assert response.data == body
