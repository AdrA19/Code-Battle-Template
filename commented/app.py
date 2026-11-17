# ═══════════════════════════════════════════════════════════════════
# 1. IMPORTS
# ═══════════════════════════════════════════════════════════════════
# "from flask import X" pulls each name out of the flask package.
# Without this, you'd write flask.Flask, flask.request, etc.
from flask import Flask, render_template, request, redirect, url_for, session

#   Flask           – the class we instantiate to build the app
#   render_template – loads templates/<name>.html, runs Jinja, returns HTML
#   request         – per-request object: .method, .form, .path, .args
#   redirect        – returns a 302 response pointing at a new URL
#   url_for         – reverse routing: function name → URL
#   session         – dict-like, persisted across requests via signed cookie


# ═══════════════════════════════════════════════════════════════════
# 2. CONFIGURATION CONSTANTS
# ═══════════════════════════════════════════════════════════════════
# UPPER_CASE = Python convention for "constant, don't change at runtime".

ADMIN_USER = "admin"
# Used to seed USERS below and shown on the admin panel.

ADMIN_PASS = "admin123"
# ⚠️ Plaintext — demo only. Real apps store bcrypt hashes.

USERS = {ADMIN_USER: [ADMIN_PASS, True]}
# A dict: { username: [password, is_admin] }.
#   USERS["admin"]     → ["admin123", True]
#   USERS["admin"][0]  → "admin123"   (password)
#   USERS["admin"][1]  → True         (admin flag)
# We use a list (not a dict) for the value so [0]/[1] indexing works.
# ⚠️ In-memory only — restart wipes all signups back to just admin.


# ═══════════════════════════════════════════════════════════════════
# 3. APP OBJECT + SECRET KEY
# ═══════════════════════════════════════════════════════════════════
app = Flask(__name__)
# __name__ tells Flask where to find templates/ and static/.

app.secret_key = "a-simple-secret-key"
# Flask's session works by writing a SIGNED cookie to the browser.
# The signature is computed with this key. If someone tampers with
# the cookie (e.g. flips is_admin to True), the signature breaks and
# Flask discards the cookie.
# ⚠️ "a-simple-secret-key" is guessable — anyone who knows it can
# forge an admin session. Generate real ones with:
#     python -c "import secrets; print(secrets.token_hex())"


# ═══════════════════════════════════════════════════════════════════
# 4. LOGIN + SIGNUP (one function, two URLs)
# ═══════════════════════════════════════════════════════════════════
@app.route("/", methods=["GET", "POST"])
@app.route("/signup", methods=["GET", "POST"], endpoint="signup")
def login():
    # Two decorators stacked → one function serves both URLs.
    # GET  = user opened the page, show form
    # POST = user submitted the form, process it
    # (Without "POST" in methods, submitting would give 405.)
    #
    # endpoint="signup" lets url_for('signup') work even though the
    # Python function is named `login`. Without it, Flask would name
    # the endpoint after the function ("login") and clash with "/" .

    mode = "signup" if request.path == "/signup" else "login"
    # request.path is the URL path. Ternary picks the mode string.
    # This one variable is what makes the two routes differ.

    error = None
    # Set to a string on failure. None → falsy → template shows no error.

    if request.method == "POST":
        # Only runs on form submit. GET skips to the render at the bottom.

        u = request.form["username"].strip()
        # request.form is the submitted form dict.
        # Key "username" matches name="username" in the HTML.
        # .strip() trims whitespace so " bob " → "bob".

        p = request.form["password"]
        # No .strip() on passwords — spaces may be intentional.

        if mode == "login":
            # ─── LOGIN ───
            if u in USERS and USERS[u][0] == p:
                # Two checks:
                #   "u in USERS"     → does the username exist?
                #   USERS[u][0] == p → does the password match?
                # Short-circuit: if the first is False, the second is
                # never evaluated, so no KeyError on missing user.

                session.update(user=u, is_admin=USERS[u][1])
                # Shorthand for:
                #   session["user"]     = u
                #   session["is_admin"] = USERS[u][1]   (the flag)
                return redirect(url_for("welcome"))
                # 302 to /welcome. Returning ends the function.

            error = "Wrong username or password"
            # Same message whether username or password is wrong —
            # prevents username enumeration.

        else:
            # ─── SIGNUP ───
            if not u or not p:
                # `not ""` is True → catches blank submissions that
                # somehow skip the HTML `required` attribute (curl, etc).
                error = "Username and password required"
            elif u in USERS:
                # elif = else-if, only checked when the first `if` failed.
                error = "Username already taken"
            else:
                USERS[u] = [p, False]
                # New entry. Signups are never admin.
                # Mutates the module-level USERS dict in place.

                session.update(user=u, is_admin=False)
                # Log the new user in immediately.
                return redirect(url_for("welcome"))

    # Reached on GET, or POST with validation error.
    return render_template("login.html", error=error, mode=mode)
    # Jinja gets two variables: error (None or str) and mode ("login"/"signup").


# ═══════════════════════════════════════════════════════════════════
# 5. WELCOME
# ═══════════════════════════════════════════════════════════════════
@app.route("/welcome")
def welcome():
    # No methods= → GET only.

    if "user" not in session:
        # Not logged in → back to the form.
        return redirect(url_for("login"))

    return render_template("welcome.html",
                           user=session["user"],
                           is_admin=session.get("is_admin", False))
    # session["user"] — safe because we just checked it exists.
    # session.get("is_admin", False) — safe even if key missing;
    # returns False by default. Handles stale cookies.
    # Both names become Jinja variables.


# ═══════════════════════════════════════════════════════════════════
# 6. ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════
@app.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        # get() returns None if key missing → `not None` → True → block.
        # Returns False if is_admin was explicitly False → also blocked.
        # Only True passes.
        return "Access Denied. You are not an admin.", 403
        # (body, status) tuple → Flask uses 403 as the status code.

    user_list = []
    # Plain Python list of display strings.

    for name, data in USERS.items():
        # .items() → (username, [password, is_admin]) pairs.
        # name = "admin" / signup username
        # data = ["password", admin_flag]
        icon = "🛡️" if data[1] else "👤"
        # data[1] is the admin flag. Ternary picks an icon.
        user_list.append(f"{name} {icon}")
        # f-string: {name} interpolates the variable.
        # Result e.g. "admin 🛡️" or "bob 👤".

    return render_template("admin.html",
                           user=session["user"],
                           admin_user=ADMIN_USER,
                           user_list=user_list)
    # Three template variables:
    #   user       – current admin's username
    #   admin_user – the ADMIN_USER constant for the settings display
    #   user_list  – the formatted list we just built


# ═══════════════════════════════════════════════════════════════════
# 7. WEBCAM PAGE
# ═══════════════════════════════════════════════════════════════════
@app.route("/webcam")
def webcam():
    if "user" not in session:
        return redirect(url_for("login"))
    # Same login check as /welcome.
    return render_template("webcam.html")
    # No variables needed — everything happens in the browser JS.


# ═══════════════════════════════════════════════════════════════════
# 8. LOGOUT
# ═══════════════════════════════════════════════════════════════════
@app.route("/logout")
def logout():
    session.clear()
    # Empties the session dict. Flask writes a fresh empty cookie,
    # effectively logging the user out.
    return redirect(url_for("login"))


# ═══════════════════════════════════════════════════════════════════
# 9. DEV SERVER
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Only runs when you execute `python app.py` directly.
    # If app.py is imported (e.g. by gunicorn), __name__ is "app",
    # so this block is skipped.
    app.run(host="localhost", port=8000, debug=True)
    # host="localhost" → only reachable from this machine
    # port=8000       → http://localhost:8000
    # debug=True      → auto-reload on save + traceback debugger
    # ⚠️ Never use debug=True in production — the debugger lets
    # anyone on the network run arbitrary Python.