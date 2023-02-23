from flask import Flask, render_template, url_for, redirect, session
from flask_session import Session
from forms import Form
import math as maths
import random
from database import get_db, close_db
from werkzeug.security import generate_password_hash

title = "Pyramid Investments Ltd."
app = Flask(__name__)
app.config["SECRET_KEY"] = str(random.randbytes(20))
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.teardown_appcontext(close_db)
Session(app)

@app.route("/", methods=["GET","POST"])
def home():
    return render_template("home.html", title=title)

@app.route("/buy", methods=["GET","POST"])
def buy():
    return render_template("buy.html", title=title)

@app.route("/sell", methods=["GET","POST"])
def sell():
    return render_template("sell.html", title=title)

@app.route("/query", methods=["GET","POST"])
def query():
    return render_template("query.html", title=title)

@app.route("/login", methods=["GET","POST"])
def login():
    return render_template("login.html", title=title)

@app.route("/register", methods=["GET","POST"])
def register():
    return render_template("register.html", title=title)

@app.route("/account", methods=["GET","POST"])
def account():
    return render_template("account.html", title=title)

@app.route("/about", methods=["GET","POST"])
def about():
    return render_template("about.html", title=title)

@app.route("/admin", methods=["GET","POST"])
def admin():
    return render_template("admin.html", title=title)

@app.route("/gamble", methods=["GET","POST"])
def gamble():
    return render_template("gamble.html", title=title)
