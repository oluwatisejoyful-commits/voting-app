import os
import json
import redis
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = "change-me-later"

cache = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)


def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


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
    if "user_id" not in session:
        return "Hello, voting app! <a href='/register'>Register</a> | <a href='/login'>Login</a>"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT choice FROM votes WHERE user_id = %s", (session["user_id"],))
    row = cur.fetchone()
    cur.close()
    conn.close()
    name = session["user"]
    if row:
        return f"Hello, {name}! You voted for {row[0]}. <a href='/results'>See results</a> | <a href='/logout'>Log out</a>"
    return f"""
    <h2>Hello, {name}! Cast your vote</h2>
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
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            message = "That username is taken."
        else:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect("/login")
        cur.close()
        conn.close()
    return render_template_string(PAGE, title="Register", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
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
    if "user_id" not in session:
        return redirect("/login")
    option = request.form.get("option")
    if option not in ("cats", "dogs"):
        return "Invalid option", 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO votes (user_id, choice) VALUES (%s, %s)",
            (session["user_id"], option),
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return "You already voted.", 409
    finally:
        cur.close()
        conn.close()
    return redirect("/")


@app.route("/results")
def results():
    cached = cache.get("results")
    if cached:
        counts = json.loads(cached)
        source = "cache"
    else:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT choice, COUNT(*) FROM votes GROUP BY choice")
        counts = dict(cur.fetchall())
        cur.close()
        conn.close()
        cache.set("results", json.dumps(counts), ex=10)
        source = "database"
    cats = counts.get("cats", 0)
    dogs = counts.get("dogs", 0)
    return (
        f"<h2>Results</h2><p>Cats: {cats}</p><p>Dogs: {dogs}</p>"
        f"<p><small>Served from: {source}</small></p><a href='/'>Back</a>"
    )


if __name__ == "__main__":
    app.run(debug=True)