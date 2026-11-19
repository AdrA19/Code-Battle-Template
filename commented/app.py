# ============================================================================
# IMPORTS
# ============================================================================
# "from flask import ..." means: go into the Flask library (a package installed
# via pip) and bring specific names into this file so we can use them directly.
# Flask          -> the main class that creates our web application object.
# render_template-> a function that finds an HTML file inside the "templates"
#                   folder, optionally fills in placeholders, and returns the
#                   resulting HTML string as the response.
# request        -> an object that holds everything about the incoming HTTP
#                   request (form data, URL path, headers, etc.). It is created
#                   fresh for every request Flask handles.
# redirect       -> a function that returns a special response telling the
#                   browser "go to this other URL instead" (HTTP 302).
# url_for        -> a function that builds a URL from the *name* of a route
#                   function (e.g. url_for("welcome") -> "/welcome"). This is
#                   better than hardcoding paths because if you change the
#                   route, all links update automatically.
# session        -> a dict-like object that stores data on the *client* side
#                   (inside a signed cookie) so it persists between requests.
from flask import Flask, render_template, request, redirect, url_for, session

# ============================================================================
# CONSTANTS / "DATABASE"
# ============================================================================
# ADMIN_USER is a plain string constant holding the admin's login name.
# ALL_CAPS is a Python convention meaning "this is a constant, don't change it".
ADMIN_USER = "admin"

# ADMIN_PASS is the admin's password stored as a plain string.
# (In a real app you would NEVER store passwords in plain text — you would
#  hash them — but this is a learning example.)
ADMIN_PASS = "admin123"

# USERS is a dictionary (a key -> value mapping).
# Each KEY is a username (string).
# Each VALUE is a LIST with exactly two items:
#   index 0 -> the password (string)
#   index 1 -> a boolean: True if the user is an admin, False otherwise.
# So USERS = { "admin": ["admin123", True] } means the admin account exists
# from the start. New sign-ups are added to this dict at runtime.
# NOTE: this is in-memory only — restarting the server wipes all sign-ups.
USERS = {ADMIN_USER: [ADMIN_PASS, True]}

# ============================================================================
# APP CREATION
# ============================================================================
# Flask(__name__) creates the application object.
# __name__ is a built-in Python variable that equals the name of the current
# module ("app" when run as app.py). Flask uses it to figure out where to
# look for the "templates" and "static" folders (they must be next to this file).
app = Flask(__name__)

# app.secret_key is REQUIRED for sessions to work. Flask uses this string to
# cryptographically sign the session cookie so the client cannot tamper with it.
# If you change this key, all existing sessions become invalid.
# (Again: in production this should be a long random value, not a hardcoded one.)
app.secret_key = "a-simple-secret-key"


# ============================================================================
# ROUTE: LOGIN / SIGNUP
# ============================================================================
# @app.route(...) is a DECORATOR. A decorator is a function that wraps another
# function to add behaviour. Here it tells Flask: "when a request comes in for
# this URL, call the function below."
#
# Two decorators are stacked on the same function, so it handles TWO URLs:
#   "/"        -> the homepage, used for LOGIN
#   "/signup"  -> used for SIGNUP
# The second decorator has endpoint="signup". Normally Flask names a route
# after its function ("login"), but because two routes share one function we
# must give the second one a unique name so url_for('signup') works.
#
# methods=["GET", "POST"] means this route accepts both kinds of HTTP request:
#   GET  -> the browser is just asking to SEE the page (show the form)
#   POST -> the browser is SUBMITTING the form (send username/password)
@app.route("/", methods=["GET", "POST"])
@app.route("/signup", methods=["GET", "POST"], endpoint="signup")
def login():
    # request.path is the URL path the browser asked for, e.g. "/" or "/signup".
    # A ternary expression: if path is "/signup" then mode = "signup",
    # otherwise mode = "login". This one variable controls which form to show.
    mode = "signup" if request.path == "/signup" else "login"

    # error starts as None (meaning "no error"). If something goes wrong below
    # we set it to a message string, and the template will display it in red.
    error = None

    # request.method tells us the HTTP verb of the current request.
    # This block only runs when the user has SUBMITTED the form (POST).
    if request.method == "POST":
        # request.form is a dict-like object containing the submitted fields.
        # request.form["username"] gets the value of the input named "username".
        # .strip() removes leading/trailing whitespace (spaces, tabs, newlines)
        # so "  bob  " becomes "bob". We assign it to `u`.
        u = request.form["username"].strip()

        # Get the password exactly as typed (no strip, because spaces could be
        # intentional in a password). Assign to `p`.
        p = request.form["password"]

        # ---- LOGIN BRANCH ----
        if mode == "login":
            # `u in USERS` checks whether the username exists as a key in the
            # USERS dictionary. `USERS[u][0]` gets the password (index 0 of the
            # list stored under that key). Both must match to log in.
            if u in USERS and USERS[u][0] == p:
                # session.update(...) is like dict.update: it sets multiple
                # keys at once. Here we store:
                #   "user"     -> the username
                #   "is_admin" -> the boolean from USERS[u][1]
                # This data is saved in the signed cookie so subsequent requests
                # remember who is logged in.
                session.update(user=u, is_admin=USERS[u][1])
                # Redirect the browser to the welcome page. url_for("welcome")
                # builds the URL for the function named `welcome` ("/welcome").
                return redirect(url_for("welcome"))
            # If we reach here, credentials were wrong. Set the error message.
            error = "Wrong username or password"

        # ---- SIGNUP BRANCH ----
        else:
            # `not u or not p` is True if either string is empty ("" is falsy).
            # This handles the case where the browser somehow submitted blanks
            # (the `required` attribute in HTML normally prevents this, but a
            # user can bypass it, so we always validate on the server too).
            if not u or not p:
                error = "Username and password required"
            # If the username is already taken, refuse to create the account.
            elif u in USERS:
                error = "Username already taken"
            else:
                # Add the new user to the dict. The value is a list:
                # [password, False] -> not an admin.
                USERS[u] = [p, False]
                # Log them in immediately by writing to the session.
                session.update(user=u, is_admin=False)
                # Send them to the welcome page.
                return redirect(url_for("welcome"))

    # If we didn't return above, we render the login/signup page.
    # render_template loads "templates/login.html" and passes the variables
    # `error` and `mode` into it so Jinja2 can use them ({{ error }}, etc.).
    return render_template("login.html", error=error, mode=mode)


# ============================================================================
# ROUTE: WELCOME PAGE
# ============================================================================
# This route only accepts GET (the default), because it's just a page to view.
@app.route("/welcome")
def welcome():
    # "user" not in session -> True if the visitor has never logged in.
    # The session dict will be empty for an anonymous visitor.
    if "user" not in session:
        # Send them back to the login page instead of showing the welcome page.
        return redirect(url_for("login"))
    # If we get here, the user is logged in. Render the welcome template with:
    #   user     -> the username string stored in the session
    #   is_admin -> session.get("is_admin", False) returns the stored value,
    #               or False if the key somehow doesn't exist (defensive).
    return render_template("welcome.html", user=session["user"],
                           is_admin=session.get("is_admin", False))


# ============================================================================
# ROUTE: ADMIN PANEL
# ============================================================================
@app.route("/admin")
def admin_panel():
    # session.get("is_admin") returns None if the key is missing, False if it's
    # False, True if it's True. `not` turns all falsy values into True, so:
    #   - anonymous visitor        -> None -> `not None`  -> True -> denied
    #   - logged-in non-admin      -> False -> `not False` -> True -> denied
    #   - logged-in admin          -> True -> `not True`  -> False -> allowed
    if not session.get("is_admin"):
        # Returning a tuple (string, status_code) tells Flask to use that HTTP
        # status. 403 means "Forbidden" — the server understood but refuses.
        return "Access Denied. You are not an admin.", 403

    # Build a list of display strings, one per user.
    user_list = []
    # USERS.items() yields (key, value) pairs, so name is the username string
    # and data is the [password, is_admin] list.
    for name, data in USERS.items():
        # data[1] is the is_admin boolean. If True, use a shield emoji,
        # otherwise a person emoji. Ternary expression again.
        icon = "🛡️" if data[1] else "👤"
        # f-string formatting: insert the variables into the string.
        # Result looks like "alice 👤" or "admin 🛡️".
        user_list.append(f"{name} {icon}")

    # Render admin.html with the current user's name, the admin username
    # constant, and the list of formatted user strings.
    return render_template("admin.html", user=session["user"],
        admin_user=ADMIN_USER, user_list=user_list)


# ============================================================================
# ROUTE: WEBCAM PAGE
# ============================================================================
@app.route("/webcam")
def webcam():
    # Same login gate as the welcome page.
    if "user" not in session:
        return redirect(url_for("login"))
    # Render the webcam page (it needs no extra variables).
    return render_template("webcam.html")


# ============================================================================
# ROUTE: LOGOUT
# ============================================================================
@app.route("/logout")
def logout():
    # session.clear() wipes everything stored in the session cookie
    # (user and is_admin). The user is now effectively logged out.
    session.clear()
    # Send them back to the login page.
    return redirect(url_for("login"))


# ============================================================================
# ENTRY POINT
# ============================================================================
# This block runs ONLY when the file is executed directly (`python app.py`),
# NOT when it's imported by another module. __name__ is "__main__" in that case.
if __name__ == "__main__":
    # app.run starts Flask's built-in development web server.
    # host="localhost" -> only accept connections from this machine.
    # port=8000        -> serve on port 8000 (http://localhost:8000).
    # debug=True       -> auto-reload on code changes AND show detailed error
    #                     pages in the browser. Never use debug=True in prod!
    app.run(host="localhost", port=8000, debug=True)