from flask import Flask, render_template, request, redirect, url_for, session, Response
import cv2
import webcam_classifier

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# { username: [password, is_admin] }
USERS = {"admin": ["admin123", True]}

app = Flask(__name__)
app.secret_key = "a-simple-secret-key"


@app.route("/", methods=["GET", "POST"])
@app.route("/signup", methods=["GET", "POST"])
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
                           is_admin=session["is_admin"])


@app.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        return "Access Denied. You are not an admin.", 403
    status = "Loaded ✅" if webcam_classifier.model is not None else "Not Loaded ❌"
    return render_template("admin.html", user=session["user"],
                           model_status=status, admin_user=ADMIN_USER, users=USERS)


@app.route("/webcam")
def webcam():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("webcam.html")


@app.route("/video")
def video():
    if "user" not in session:
        return "Please log in first", 401
    return Response(stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


def stream():
    webcam_classifier.load_labels()
    webcam_classifier.load_model()
    cam = cv2.VideoCapture(0)
    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                break
            r = webcam_classifier.classify_image(frame)
            if r:
                cv2.putText(frame, f"{r['class_name']} ({r['confidence']:.0%})",
                            (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            ok, jpg = cv2.imencode(".jpg", frame)
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
    finally:
        cam.release()


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
