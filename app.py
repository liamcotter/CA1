from flask import Flask, render_template, url_for, redirect, session, g, request
from flask_session import Session
from forms import Form, RegistrationForm, LoginForm
from database import get_db, close_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from classes import Stock
from time import time

title = "Pyramid Investments Ltd."
app = Flask(__name__)
app.config["SECRET_KEY"] = "efojiwsdlo&^diqwe34 3£93irefj9h-_f".encode('utf8')
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.teardown_appcontext(close_db)
Session(app)

@app.before_request
def logged_in_user():
    g.user = session.get("username", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
def home():
    return render_template("home.html", title=title)

@app.route("/buy", methods=["GET","POST"])
def buy():
    return render_template("buy.html", title=title)

@app.route("/sell", methods=["GET","POST"])
def sell():
    return render_template("sell.html", title=title)

@app.route("/query", methods=["GET","POST"])
@login_required
def query():
    db = get_db()
    stockList = []
    stocks = db.execute("""SELECT * FROM stock_name;""").fetchall()
    for stock in stocks:
        name = stock["name"]
        uuid = stock["stock_uuid"]
        latest_info = db.execute("""SELECT * FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC;""", (uuid,)).fetchone()
        update_time = latest_info["time"]
        valuation = latest_info["valuation"]
        share_count = latest_info["share_count"]
        market_value = share_count * valuation
        last_update = time()//3600 - update_time # minutes ago
        instace_of_stock = Stock(uuid, name, last_update, valuation, share_count, market_value)
        stockList.append(instace_of_stock)
    return render_template("query.html", stocks=stockList, title=title)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        possible_clashing_user = db.execute("""SELECT * FROM users WHERE
									username = ?;""", (username,) ).fetchone()
        if possible_clashing_user is None or not check_password_hash(possible_clashing_user['password'], password):
            form.password.errors.append("Incorrect username or password")
        else:
            session.clear()
            session["username"] = username
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for('home')
            return redirect(next_page)
    return render_template("login.html", form=form, title=title)

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for('home'))

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        clashing_user = db.execute("""SELECT * FROM users WHERE username = ?;""", (username,) ).fetchone()
        if clashing_user:
            form.username.errors.append("Username is taken.")
        else:
            db.execute("""INSERT INTO users (username, password, about) VALUES (?, ?, ?);""", (username, generate_password_hash(password), ""))
            db.commit()
            return redirect(url_for('login'))
    return render_template("register.html", form=form, title=title)

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
