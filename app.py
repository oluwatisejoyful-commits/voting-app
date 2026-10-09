from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-me-later"

users = {}  # temporary storage: {username: hashed_password}

PAGE = """
<h2>{{ title }}</h2>
<p style="color:red">{{ message }}</p>
<form method="post">
  <input name="username" placeholder="Username" required><br><br>
  <input name="password" type="password" placeholder="Password" required><br><br>
  <button type="submit">{{ title }}</button>
</form>
<p><a href="/register">Register</a> | <a href="/login">Login</a></p>
"""

@app.route("/")
def home():
    if "user" in session:
        return f"Hello, {session['user']}! <a href='/logout'>Log out</a>"
    return "Hello, voting app! <a href='/register'>Register</a> | <a href='/login'>Login</a>"

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            message = "That username is taken."
        else:
            users[username] = generate_password_hash(password)
            return redirect("/login")
    return render_template_string(PAGE, title="Register", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and check_password_hash(users[username], password):
            session["user"] = username
            return redirect("/")
        message = "Wrong username or password."
    return render_template_string(PAGE, title="Login", message=message)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)