from flask import Flask, render_template, request, redirect, url_for, session

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# { username: [password, is_admin] }
USERS = {ADMIN_USER: [ADMIN_PASS, True]}

app = Flask(__name__)
app.secret_key = "a-simple-secret-key"


@app.route("/", methods=["GET", "POST"])
@app.route("/signup", methods=["GET", "POST"], endpoint="signup")
def login():
    mode = "signup" if request.path == "/signup" else "login"
    error = None

    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"]

        if mode == "login":
            if u in USERS and USERS[u][0] == p:
                session.update(user=u, is_admin=USERS[u][1])
                return redirect(url_for("welcome"))
            error = "Wrong username or password"
        else:
            if not u or not p:
                error = "Username and password required"
            elif u in USERS:
                error = "Username already taken"
            else:
                USERS[u] = [p, False]
                session.update(user=u, is_admin=False)
                return redirect(url_for("welcome"))

    return render_template("login.html", error=error, mode=mode)


@app.route("/welcome")
def welcome():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("welcome.html", user=session["user"],
                           is_admin=session.get("is_admin", False))


@app.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        return "Access Denied. You are not an admin.", 403

    user_list = []
    for name, data in USERS.items():
        icon = "🛡️" if data[1] else "👤"
        user_list.append(f"{name} {icon}")

    return render_template("admin.html", user=session["user"],
        admin_user=ADMIN_USER, user_list=user_list)


@app.route("/webcam")
def webcam():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("webcam.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)