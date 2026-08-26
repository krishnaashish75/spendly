# Spec: Frontend Page Design

## Overview

This Step 4 feature replaces Spendly’s placeholder profile screen with a polished, responsive account page for authenticated users. It gives a signed-in user a clear view of their account identity and membership details while establishing the card-based, fintech-style page pattern that later expense-management screens can reuse; expense summaries and editing remain deferred to their roadmap steps.

## Depends on

- Step 01 — Database Setup
- Step 02 — Registration
- Step 03 — Login and Logout

## Routes

- `GET /profile` — Replace the placeholder with the authenticated user’s profile page; redirect anonymous visitors to the login page — logged-in

## Database changes

No schema changes.

Add a database-layer helper in `database/db.py` to retrieve the current user’s safe profile fields (`id`, `name`, `email`, and `created_at`) by ID. The query must be parameterised and must not fetch or expose `password_hash`.

## Templates

**Create:** No new templates.

**Modify:**

- `templates/profile.html` — Replace the placeholder with an accessible profile layout: a personal greeting, an initial-based avatar, account-detail cards, a membership date, and a clearly labelled sign-out action. Load the profile-specific stylesheet through the existing `head` block using `url_for()`.

## Files to change

- `app.py`
- `database/db.py`
- `templates/profile.html`

## Files to create

- `static/css/profile.css`
- `tests/test_profile.py`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug.
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- Keep database access in `database/db.py`; the profile route may only check the session, obtain the current user through a database helper, and render or redirect.
- Require `session['user_id']` for `/profile`; redirect anonymous visitors with `url_for('login')` rather than showing profile content.
- If the session user no longer exists, clear the stale session and redirect to login.
- Pass only safe user fields to the template; never pass, render, log, or query a password hash for display.
- Keep the profile page focused on account information. Do not add expense lists, expense totals, expense forms, or later roadmap functionality.
- Use the existing design tokens, fonts, button styles, card treatment, and responsive conventions from `static/css/style.css`.
- Add all page-specific selectors to `static/css/profile.css` with a `profile-` prefix so styles do not leak into other pages.
- Ensure the layout is responsive: profile cards stack cleanly and retain usable spacing on narrow viewports.
- Use `url_for()` for every internal template URL, including the profile stylesheet and sign-out action.
- Do not alter the unimplemented expense routes.

## Definition of done

- [ ] Logging in with a valid account and visiting `/profile` shows that account’s name, email address, and formatted membership date.
- [ ] The profile page presents a polished, responsive card-based account layout that matches the existing Spendly visual language.
- [ ] The page includes an initial-based avatar and a clearly labelled sign-out action that logs the user out and returns them to `/`.
- [ ] Opening `/profile` without an authenticated session redirects to `/login` and shows no account information.
- [ ] A stale session whose user no longer exists is cleared and redirected to `/login`.
- [ ] The rendered page never contains the user’s password or password hash.
- [ ] The profile stylesheet loads through `url_for()` and all new profile CSS uses existing CSS variables rather than hardcoded hex colours.
- [ ] At narrow viewport widths, the profile information cards stack without horizontal overflow.
- [ ] The expense add, edit, and delete placeholder routes remain unchanged.
- [ ] `pytest` passes, including profile-access and profile-content tests.
- [ ] Running `python app.py` serves the profile page on port 5001 without errors.
