from flask import Flask, render_template, url_for, redirect
from forms import Form
from database import get_db, close_db
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "1"
app.teardown_appcontext(close_db)

@app.route("/", methods=["GET","POST"])
def home():
    return render_template("home.html", title="Pyramid Investments Ltd.")

@app.route("/buy", methods=["GET","POST"])
def buy():
    return render_template("buy.html", title="Pyramid Investments Ltd.")

@app.route("/sell", methods=["GET","POST"])
def sell():
    return render_template("sell.html", title="Pyramid Investments Ltd.")

@app.route("/query", methods=["GET","POST"])
def query():
    return render_template("query.html", title="Pyramid Investments Ltd.")

@app.route("/login", methods=["GET","POST"])
def login():
    return render_template("login.html", title="Pyramid Investments Ltd.")

@app.route("/register", methods=["GET","POST"])
def register():
    return render_template("register.html", title="Pyramid Investments Ltd.")

@app.route("/account", methods=["GET","POST"])
def account():
    return render_template("account.html", title="Pyramid Investments Ltd.")

@app.route("/about", methods=["GET","POST"])
def about():
    return render_template("about.html", title="Pyramid Investments Ltd.")

@app.route("/admin", methods=["GET","POST"])
def admin():
    return render_template("admin.html", title="Pyramid Investments Ltd.")

@app.route("/gamble", methods=["GET","POST"])
def gamble():
    return render_template("gamble.html", title="Pyramid Investments Ltd.")
