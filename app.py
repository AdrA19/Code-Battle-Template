from flask import Flask, render_template, request, redirect, url_for, session, Response
import cv2
import webcam_classifier

# Change your login here
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

app = Flask(__name__)
app.secret_key = "a-simple-secret-key"

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["user"] = ADMIN_USER
            session["is_admin"] = True # Remember that this user is an admin
            return redirect(url_for("welcome"))
        error = "Wrong username or password"
    return render_template("login.html", error=error)

@app.route("/welcome")
def welcome():
    if "user" not in session:
        return redirect(url_for("login"))
    # Pass is_admin to the welcome page
    return render_template("welcome.html", user=session["user"], is_admin=session.get("is_admin"))

@app.route("/admin")
def admin_panel():
    # Security check: Must be logged in AND be an admin
    if not session.get("is_admin"):
        return "Access Denied. You are not an admin.", 403
        
    # Check the status of the AI model
    model_status = "Loaded ✅" if webcam_classifier.model is not None else "Not Loaded ❌"
    
    return render_template("admin.html", 
                           user=session["user"], 
                           model_status=model_status,
                           admin_user=ADMIN_USER)

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
            if not ok: break
            
            result = webcam_classifier.classify_image(frame)
            if result:
                text = f"{result['class_name']} ({result['confidence']:.0%})"
                cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            ok, jpg = cv2.imencode(".jpg", frame)
            if ok:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")
    finally:
        cam.release()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)