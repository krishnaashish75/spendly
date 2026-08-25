# Spec: Login and Logout

## Overview

This feature completes Step 3 of the Spendly roadmap by allowing registered users to authenticate with their email address and password, persist their authenticated state in a secure Flask session, and sign out. It builds on registration so users can enter the application securely without implementing the Step 4 profile page or any later expense-management work.

## Depends on

- Step 01 — Database Setup
- Step 02 — Registration

## Routes

- `GET /login` — Render the login form — public
- `POST /login` — Validate credentials, create an authenticated session, and redirect to the profile route — public
- `GET /logout` — Clear the current session and redirect to the landing page — logged-in (safe and idempotent for anonymous visitors)

## Database changes

No schema changes.

Add a database-layer `authenticate_user(email, password)` helper that queries the user by email with a parameterised query, verifies the stored password hash with Werkzeug, closes its connection, and returns the matching user or `None`. It must return the same result for an unknown email and an incorrect password, and must never log or return plaintext credentials.

## Templates

**Create:** No new templates.

**Modify:**

- `templates/login.html` — Use `url_for('login')` for the form action, retain the submitted email after a failed attempt, and keep the password field blank.
- `templates/base.html` — Show `Sign in` and `Get started` to anonymous visitors; show `Profile` and `Sign out` to authenticated visitors. All links must use `url_for()`.

## Files to change

- `app.py`
- `database/db.py`
- `templates/login.html`
- `templates/base.html`

## Files to create

- `tests/test_authentication.py`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug.
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- Configure Flask's `SECRET_KEY` from `SPENDLY_SECRET_KEY`, with an explicitly development-only fallback so the app remains runnable locally.
- Trim the email address but do not trim, persist, or apply registration password-length validation to the login password; the seeded `demo@spendly.com` / `demo123` account must be able to log in.
- Validate missing email and password fields.
- Use a single generic invalid-credentials message for an unknown email and an incorrect password.
- On a successful login, call `session.clear()` before setting only `session['user_id']`; never store a password or password hash in the session.
- On successful login, redirect with `url_for('profile')`; do not implement or alter the Step 4 profile stub.
- Logout must call `session.clear()` and redirect with `url_for('landing')`.
- Do not add authentication decorators or implement any profile or expense stub routes in this step.

## Definition of done

- [ ] Visiting `GET /login` renders the login form with a `url_for()`-generated form action.
- [ ] Submitting valid registered credentials creates a signed session containing the correct user ID and redirects to `/profile`.
- [ ] The seeded `demo@spendly.com` / `demo123` account can log in.
- [ ] An unknown email and an incorrect password show the same generic error, create no authenticated session, retain the entered email, and never redisplay the password.
- [ ] Submitting either required field empty displays a clear validation error.
- [ ] A successful login remains authenticated on a subsequent request through Flask's session cookie.
- [ ] Anonymous navigation shows `Sign in` and `Get started`; authenticated navigation shows `Profile` and `Sign out`.
- [ ] Visiting `/logout` clears all session state and redirects to `/`; visiting it anonymously is harmless.
- [ ] The profile and expense routes remain unimplemented stubs.
- [ ] `pytest` passes, including the new authentication tests and existing registration tests.
- [ ] Running `python app.py` starts the application on port 5001.
