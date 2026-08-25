from flask import Flask, redirect, render_template, request, url_for

from database.db import create_user, get_db, init_db, seed_db


app = Flask(__name__)

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


def render_register(error=None, name="", email=""):
    return render_template(
        "register.html",
        error=error,
        name=name,
        email=email,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_register()

    name = request.form.get("name", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    trimmed_name = name.strip()
    trimmed_email = email.strip()

    if not trimmed_name:
        return render_register("Please enter your full name.", name, email)

    if not trimmed_email:
        return render_register("Please enter your email address.", name, email)

    if not password:
        return render_register("Please enter a password.", name, email)

    if len(password) < 8:
        return render_register(
            "Password must be at least 8 characters.",
            name,
            email,
        )

    if not create_user(trimmed_name, trimmed_email, password):
        return render_register(
            "An account with that email address already exists.",
            name,
            email,
        )

    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
