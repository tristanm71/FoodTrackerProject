import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
from functools import wraps

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///food.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/home")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/home")
@login_required
def home():
    today = date.today()
    today = str(today)
    day = '%' + today + '%'
    list = db.execute("SELECT name, protein, carbs, fats, calories, portion, datetime FROM history WHERE user = ? AND datetime LIKE ? ORDER BY datetime", session["user_id"], day)

    protein, carbs, fats, calories = 0, 0, 0, 0
    for row in list:
        protein += row["protein"]
        carbs += row["carbs"]
        fats += row["fats"]
        calories += row["calories"]

    goal = db.execute("SELECT daily_calories FROM stats WHERE user_id = ?", int(session["user_id"]))
    goal = goal[0]["daily_calories"]
    return render_template("home.html", date=today, list=list, protein=protein, carbs=carbs, fats=fats, calories=calories, goal=goal)

@app.route("/logs")
@login_required
def logs():
    list = db.execute("SELECT name, protein, carbs, fats, calories, portion, datetime FROM history WHERE user = ? ORDER BY datetime DESC", session["user_id"])

    return render_template("logs.html", list=list)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if user imputs everything and passwords match
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords do not match", 400)
        # check if username is taken
        if db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username")):
            return apology("username taken", 400)

        hashpassword = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), hashpassword)
        rows = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))

        session["user_id"] = rows[0]["id"]
        return redirect("/stats")
    else:
        return render_template("register.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        if not request.form.get("food"):
            apology("please enter food", 400)

        word = "%" + request.form.get("food") + "%"
        foods = db.execute("SELECT name, fdc_id FROM food WHERE name LIKE ? ORDER BY name", word)

        nutrient = {}
        for row in foods:
            id = row["fdc_id"]
            nutrient[id] = db.execute("SELECT nutrient_id, amount FROM nutrients WHERE fdc_id = ? ORDER BY nutrient_id", id)

        if len(foods) == 0:
            return apology("No food found", 400)

        return render_template("searched.html", foods=foods, nutrient=nutrient)
    else:
        return render_template("search.html")


@app.route("/stats", methods=["GET", "POST"])
def stats():
    if request.method == "POST":
        if not request.form.get("feet") or not request.form.get("inches") or not request.form.get("weight") or not request.form.get("calorie"):
            return apology("incomplete form", 400)

        if int(request.form.get("feet")) <= 0 or int(request.form.get("inches")) < 0 or int(request.form.get("calorie")) <= 0 or int(request.form.get("weight")) <= 0:
            return apology("invalid input")

        db.execute("INSERT INTO stats (user_id, feet, inches, weight, daily_calories) VALUES(?, ?, ?, ?, ?)", int(session["user_id"]), int(
            request.form.get("feet")), int(request.form.get("inches")), float(request.form.get("weight")), int(request.form.get("calorie")))
        return redirect("/home")
    else:
        return render_template("stats.html")

@app.route("/change", methods=["GET", "POST"])
def change():
    if request.method == "POST":
        if not request.form.get("feet") or not request.form.get("inches") or not request.form.get("weight") or not request.form.get("calorie"):
            return apology("incomplete form", 400)

        if int(request.form.get("feet")) <= 0 or int(request.form.get("inches")) < 0 or int(request.form.get("calorie")) <= 0 or int(request.form.get("weight")) <= 0:
            return apology("invalid input")

        db.execute("UPDATE stats SET feet = ?, inches = ?, weight = ?, daily_calories = ? WHERE user_id = ?", int(request.form.get("feet")), int(request.form.get("inches")), float(request.form.get("weight")), int(request.form.get("calorie")), int(session["user_id"]))
        return redirect("/home")
    else:
        return render_template("change.html")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        if not request.form.get("food") or not request.form.get("portion"):
            return apology("enter valid food", 400)

        food = db.execute("SELECT name FROM food WHERE fdc_id = ?", request.form.get("food"))

        if not food:
            return apology("enter valid food", 400)
        if float(request.form.get("portion")) <= 0:
            return apology("enter valid portion size", 400)

        date = datetime.now()

        nutrients = db.execute("SELECT nutrient_id, amount FROM nutrients WHERE fdc_id = ? ORDER BY nutrient_id", request.form.get("food"))
        portion = float(request.form.get("portion"))

        db.execute("INSERT INTO history (name, portion, protein, carbs, fats, calories, fdc_id, datetime, user) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", food[0]["name"], portion, float(nutrients[0]["amount"]) * portion, float(nutrients[1]["amount"]) * portion, float(nutrients[2]["amount"]) * portion, float(nutrients[3]["amount"]) * portion, request.form.get("food"), date, session["user_id"])

        return redirect("/home")
    else:
        return render_template("add.html")

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code
