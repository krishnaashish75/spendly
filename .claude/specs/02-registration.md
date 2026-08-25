# Spec: Registration

## Overview

Registration turns the existing public sign-up form into a working account-creation flow for Step 2 of the Spendly roadmap. It lets a new visitor create a unique account with a securely hashed password, on success visitor shown with a success message and then directs them to the existing login page; authentication and session management remain deferred to Step 3.

## Depends on

Step 1 — Database Setup. The `users` table, its unique `email` constraint, and SQLite connection helpers must be available.

## Routes

- POST /register — validate registration details, create a user account, and redirect on success or re-render the form with an error — public

The existing GET /register route continues to render the registration form.

## Database changes

No schema changes. Add database-layer helpers in `database/db.py` as needed to create a user and handle or expose duplicate-email conflicts without placing SQL in route functions.

## Templates

- Create: No new templates.
- Modify: `templates/register.html` — submit to `url_for('register')`, retain entered name and email after validation errors, add client-side minimum-length guidance for the password, and render server-provided validation errors safely.

## Files to change

- `app.py`
- `database/db.py`
- `templates/register.html`

## Files to create

No new implementation files.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with `werkzeug.security.generate_password_hash` before storage; never store or log plaintext passwords.
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- Keep all registration SQL and connection use in `database/db.py`; route functions only coordinate input, validation, and rendering or redirects.
- Keep `GET /register` public and add `POST` handling to the same route function.
- Validate required name, email, and password fields server-side even when browser validation is present.
- Require passwords to be at least eight characters server-side.
- Treat duplicate email registration as a friendly form error and do not create a second account.
- On successful registration, redirect with `url_for('login')`; do not add session handling or implement later roadmap routes.
- Use `url_for()` for every internal template URL, including the registration form action.

## Definition of done

- Opening `/register` as a logged-out visitor shows the existing registration form.
- Submitting a valid name, unused email, and password of at least eight characters creates one row in `users` with the submitted name and email.
- The stored `password_hash` is not the submitted plaintext password and verifies with `werkzeug.security.check_password_hash`.
- A successful submission redirects the browser to `/login`.
- Submitting an email already present in `users` keeps the visitor on the registration page, shows a clear error, and leaves the database with only one account for that email.
- Submitting a missing field or a password shorter than eight characters shows a clear error and creates no account.
- After a failed submission, the entered name and email remain populated while the password field is blank.
- The registration form action and login link are generated with `url_for()`.
- Starting the app with `python app.py` still serves the registration page on port 5001 without errors.
