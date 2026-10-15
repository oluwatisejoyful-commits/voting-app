from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-me-later"

users = {}  # temporary storage: {username: hashed_password}
votes = {}  # temporary storage: {username: "cats" or "dogs"}

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
    if "user" not in session:
        return "Hello, voting app! <a href='/register'>Register</a> | <a href='/login'>Login</a>"
    user = session["user"]
    if user in votes:
        return f"Hello, {user}! You voted for {votes[user]}. <a href='/results'>See results</a> | <a href='/logout'>Log out</a>"
    return f"""
    <h2>Hello, {user}! Cast your vote</h2>
    <form method="post" action="/vote">
      <button name="option" value="cats">Cats</button>
      <button name="option" value="dogs">Dogs</button>
    </form>
    <p><a href="/results">See results</a> | <a href="/logout">Log out</a></p>
    """

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

@app.route("/vote", methods=["POST"])
def vote():
    if "user" not in session:
        return redirect("/login")
    user = session["user"]
    option = request.form.get("option")
    if option not in ("cats", "dogs"):
        return "Invalid option", 400
    if user in votes:
        return "You already voted.", 409
    votes[user] = option
    return redirect("/")

@app.route("/results")
def results():
    cats = sum(1 for v in votes.values() if v == "cats")
    dogs = sum(1 for v in votes.values() if v == "dogs")
    return f"<h2>Results</h2><p>Cats: {cats}</p><p>Dogs: {dogs}</p><a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(debug=True)