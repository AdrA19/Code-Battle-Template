# ============================================================
# IMPORTS
# ============================================================
# `flask` is a lightweight web framework for Python.
# We import specific names from it:
#   - Flask        : the main application class
#   - render_template : renders an HTML template file from the `templates/` folder
#   - request      : holds incoming request data (form fields, path, etc.)
#   - redirect     : returns a redirect response to another URL
#   - url_for      : builds a URL for a given view function name
#   - session      : a per-user dictionary stored in a signed cookie
from flask import Flask, render_template, request, redirect, url_for, session

# ============================================================
# CONSTANTS / INITIAL DATA
# ============================================================
# The built-in administrator username (a plain string).
ADMIN_USER = "admin"

# The built-in administrator password (a plain string — insecure in real apps).
ADMIN_PASS = "admin123"

# USERS is a dictionary mapping:
#     username (str) -> [password (str), is_admin (bool)]
# The admin account is pre-seeded here.
# `USERS[ADMIN_USER]` evaluates to the list `[ADMIN_PASS, True]`.
USERS = {ADMIN_USER: [ADMIN_PASS, True]}

# ============================================================
# APP SETUP
# ============================================================
# Create the Flask application object. `__name__` tells Flask where
# to look for templates/static files (relative to this module).
app = Flask(__name__)

# `secret_key` is required for sessions (Flask signs the cookie with it).
# In production this should be a long random value, NOT a hard-coded string.
app.secret_key = "a-simple-secret-key"

# ============================================================
# LOGIN / SIGNUP VIEW
# ============================================================
# Two decorators are stacked on the same function:
#   @app.route("/", ...)          -> root URL  (login page)
#   @app.route("/signup", ...)    -> /signup URL (signup page)
# `endpoint="signup"` gives the second route a distinct name so
# `url_for("signup")` works. Otherwise both would be named "login".
#
# `methods=["GET", "POST"]` means this view accepts both:
#   GET  -> show the form
#   POST -> process submitted form data
@app.route("/", methods=["GET", "POST"])
@app.route("/signup", methods=["GET", "POST"], endpoint="signup")
def login():
    # `request.path` is the URL path that was requested ("/" or "/signup").
    # We use it to decide whether we're in "login" or "signup" mode.
    # This is a ternary expression: value_if_true if condition else value_if_false
    mode = "signup" if request.path == "/signup" else "login"

    # `error` starts as None; it will be set to a string if something fails.
    error = None

    # Only process form data when the request method is POST.
    if request.method == "POST":
        # `request.form` is a dict-like object of submitted form fields.
        # `["username"]` raises KeyError if missing; `.strip()` removes
        # leading/trailing whitespace from the username.
        u = request.form["username"].strip()
        # Passwords are NOT stripped — whitespace may be intentional.
        p = request.form["password"]

        # ---- LOGIN MODE ----
        if mode == "login":
            # Check: username exists in USERS AND the stored password matches.
            # USERS[u][0] is the password (index 0 of the list).
            if u in USERS and USERS[u][0] == p:
                # `session.update(...)` sets multiple session keys at once.
                # `is_admin` is True only for the admin account.
                session.update(user=u, is_admin=USERS[u][1])
                # Redirect the browser to the "welcome" view's URL.
                return redirect(url_for("welcome"))
            # If credentials are wrong, set an error message.
            error = "Wrong username or password"

        # ---- SIGNUP MODE ----
        else:
            # Reject empty username or password.
            if not u or not p:
                error = "Username and password required"
            # Reject duplicate usernames.
            elif u in USERS:
                error = "Username already taken"
            else:
                # Register the new user as a non-admin ([password, False]).
                USERS[u] = [p, False]
                # Automatically log them in.
                session.update(user=u, is_admin=False)
                return redirect(url_for("welcome"))

    # If we reach here (GET, or POST with an error), render the template.
    # `render_template` looks for `login.html` inside `templates/`.
    # Keyword args become variables accessible inside the template.
    return render_template("login.html", error=error, mode=mode)

# ============================================================
# WELCOME VIEW (protected)
# ============================================================
@app.route("/welcome")
def welcome():
    # "Authentication guard": if the session has no "user" key,
    # the visitor is not logged in -> send them to the login page.
    if "user" not in session:
        return redirect(url_for("login"))
    # Otherwise render the welcome page. `session["user"]` is the username.
    # `session.get("is_admin", False)` returns False if the key is missing.
    return render_template("welcome.html", user=session["user"],
                           is_admin=session.get("is_admin", False))

# ============================================================
# ADMIN PANEL VIEW (admin-only)
# ============================================================
@app.route("/admin")
def admin_panel():
    # Guard: only users with is_admin True may proceed.
    # `not session.get("is_admin")` is True when the value is missing/False.
    # We return a tuple `(body, status_code)` -> HTTP 403 Forbidden.
    if not session.get("is_admin"):
        return "Access Denied. You are not an admin.", 403

    # Build a human-readable list of users with an emoji icon.
    user_list = []
    # `.items()` yields (key, value) pairs from the dict.
    for name, data in USERS.items():
        # `data[1]` is the is_admin boolean.
        # Ternary chooses the shield emoji for admins, person for regular users.
        icon = "🛡️" if data[1] else "👤"
        # f-strings interpolate variables into the string.
        user_list.append(f"{name} {icon}")

    # Render the admin template with the prepared data.
    # `admin_user` passes the constant so the template can display it.
    return render_template("admin.html", user=session["user"],
        admin_user=ADMIN_USER, user_list=user_list)

# ============================================================
# WEBCAM VIEW (protected)
# ============================================================
@app.route("/webcam")
def webcam():
    # Same login guard as /welcome.
    if "user" not in session:
        return redirect(url_for("login"))
    # Just render the page; the JS inside handles the camera.
    return render_template("webcam.html")

# ============================================================
# LOGOUT VIEW
# ============================================================
@app.route("/logout")
def logout():
    # `session.clear()` removes ALL keys from the session,
    # effectively logging the user out.
    session.clear()
    return redirect(url_for("login"))

# ============================================================
# ENTRY POINT
# ============================================================
# This block runs only when the script is executed directly
# (`python app.py`), not when imported as a module.
if __name__ == "__main__":
    # host="localhost" -> only reachable from this machine.
    # port=8000        -> listen on TCP port 8000.
    # debug=True       -> auto-reload on changes + detailed error pages.
    #                     NEVER enable debug in production.
    app.run(host="localhost", port=8000, debug=True)