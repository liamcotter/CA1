from flask import Flask, render_template, url_for, redirect, session, g, request, abort
from flask_session import Session
from forms import RegistrationForm, LoginForm, BuyForm, SellForm, AdminNewStockForm
from database import get_db, close_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from classes import Stock, User
from time import time, sleep
import base64
from io import BytesIO
from matplotlib.figure import Figure
from random import randint
from price_gen import generate_new_stock_price

title = "Pyramid Investments Ltd."
app = Flask(__name__)
app.config["SECRET_KEY"] = "efojiwsdlo&^diqwe34 3£93irefj9h-_f".encode('utf8')
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.teardown_appcontext(close_db)
Session(app)

"""
gamble
leaderboard
fix stock price
add info for derek
improve home page
"""

def update_user_stats(username: str):
    uuids = []
    net_worths = []
    db = get_db()
    stocks = db.execute("""SELECT DISTINCT stock_uuid FROM transactions WHERE username = ?;""", (username,)).fetchall()
    for stock in stocks:
        uuids.append(stock["stock_uuid"])
    for uuid in uuids:
        total_buy = db.execute("""SELECT SUM(quantity) as tot_buy FROM transactions 
                                WHERE buy = 1 AND stock_uuid = ? AND username = ?;""", (uuid, username)).fetchone()
        total_sell = db.execute("""SELECT SUM(quantity) as tot_sell FROM transactions 
                                WHERE buy = 0 AND stock_uuid = ? AND username = ?; """, (uuid, username)).fetchone()
        buy = total_buy["tot_buy"]
        sell = total_sell["tot_sell"]
        if sell is None:
            sell = 0
        total = buy-sell
        init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
        value = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"])
        net_worths.append(value*total)
    cash_d = db.execute("""SELECT cash FROM user_hist WHERE username = ? ORDER BY time DESC LIMIT 1;""", (username,)).fetchone()
    cash = cash_d["cash"]
    print("Update: ", cash, net_worths)
    if sum(net_worths) == 0:
        net_worth = cash
    else:
        net_worth = sum(net_worths) + cash 
    db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (username, time()//1, cash, net_worth))
    db.commit()
    sleep(1) #ensures that no two updates occur in 1s

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

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        print("User:", g.user)
        if g.user != "admin":
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
def home():
    return render_template("home.html", title=title)

@app.route("/api/v1/stock/<uuid>")
def api_stock(uuid):
    db = get_db()
    d = {}
    init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
    if init_vals is None:
        d["errcode"] = 1 # Only error possible
        d["error"] = "Invalid stock abbreviation"
        return d
    price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"])
    d["price"] = price
    d["uuid"] = uuid
    d["time"] = time()//1
    return d

@app.route("/stock/<uuid>", methods=["GET", "POST"])
@login_required
def stock(uuid):
    buyForm = BuyForm()
    sellForm = SellForm()
    db = get_db()
    stocks = db.execute("""SELECT stock_uuid from stock_name""").fetchall()
    stocks_list = [s["stock_uuid"] for s in stocks]
    if uuid not in stocks_list:
        abort(404)
    if sellForm.validate_on_submit() and sellForm.quantity_sell.data:
        maxStock = 0
        total_buy = db.execute("""SELECT SUM(quantity) as tot_buy FROM transactions 
                                WHERE buy = 1 AND stock_uuid = ? AND username = ?;""", (uuid, g.user)).fetchone()
        total_sell = db.execute("""SELECT SUM(quantity) as tot_sell FROM transactions 
                                WHERE buy = 0 AND stock_uuid = ? AND username = ?; """, (uuid, g.user)).fetchone()
        buy = total_buy["tot_buy"]
        sell = total_sell["tot_sell"]
        if sell is None:
            sell = 0
        if buy is None:
            maxStock = 0
        else:
            maxStock = buy-sell
        quant = sellForm.quantity_sell.data
        if maxStock < quant or quant < 1:
            sellForm.quantity_sell.errors.append(f"You can only sell between 1 and {maxStock} stocks.")
        else:
            init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
            price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"])
            update_user_stats(g.user)
            db.execute("""INSERT into transactions (username, time, stock_uuid, quantity, price, buy) VALUES (?, ?, ?, ?, ?, ?);""", (g.user, time()//1, uuid, quant, price*quant, False))
            db.commit()
            d = db.execute("""SELECT cash, net_worth FROM user_hist WHERE username = ? ORDER BY time DESC LIMIT 1;""", (g.user,)).fetchone()
            cash = d["cash"]
            cash += price*quant
            net_worth = d["net_worth"]
            print("Sold: ", cash, net_worth)
            db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (g.user, time()//1, cash, net_worth))
            db.commit()
            sleep(1) # avoid duplicate user_info entry
            return redirect(url_for("account"))
    
    elif buyForm.validate_on_submit() and buyForm.quantity_buy.data:
        quant = buyForm.quantity_buy.data
        init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
        price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"])
        cash_worth = db.execute("""SELECT cash, net_worth FROM user_hist WHERE username = ? ORDER BY time DESC;""", (g.user,)).fetchone()
        cash = cash_worth["cash"]
        max_stock = cash // price
        if quant > max_stock or quant < 1:
            buyForm.quantity_buy.errors.append(f"You can only afford up to {max_stock} stocks!")
        else:
            net_worth = cash_worth["net_worth"]
            db.execute("""INSERT into transactions (username, time, stock_uuid, quantity, price, buy) VALUES (?, ?, ?, ?, ?, ?);""", (g.user, time()//1, uuid, quant, price*quant, True))
            db.commit()
            cash = cash - price*quant
            print("Buy: ", cash, net_worth)
            db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (g.user, time()//1, cash, net_worth))
            db.commit()
            sleep(1) # avoid duplicate user_info entry
            return redirect(url_for("account"))
    
    name = db.execute("""SELECT name FROM stock_name WHERE stock_uuid = ?;""", (uuid,)).fetchone()
    name = name["name"]
    init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
    t = init_vals["time"]
    curr_time = time()
    diff = (curr_time - t) /100
    print(diff)
    valuations, time_x = [], []
    for i in range(100):
        new_t = t + diff*i
        price = generate_new_stock_price(t, init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"], curr_time=new_t)
        time_x.append(new_t/(60*60))
        valuations.append(price)
    print(valuations)
    min_time = min(time_x)
    time_x = [t-min_time for t in time_x]
    fig = Figure()
    ax = fig.add_subplot()
    ax.plot(time_x, valuations)
    ax.ticklabel_format(style='plain', useOffset=False)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    graph = f"<img src='data:image/png;base64,{data}'/>"
    total_buy = db.execute("""SELECT SUM(quantity) as tot_buy FROM transactions 
                                WHERE buy = 1 AND stock_uuid = ? AND username = ?;""", (uuid, g.user)).fetchone()
    total_sell = db.execute("""SELECT SUM(quantity) as tot_sell FROM transactions 
                                WHERE buy = 0 AND stock_uuid = ? AND username = ?; """, (uuid, g.user)).fetchone()
    buy = total_buy["tot_buy"]
    sell = total_sell["tot_sell"]
    if sell is None:
        sell = 0
    if buy is None:
        net_stock = None
    else:
        net_stock = buy-sell
    return render_template("stock_info.html", graph=graph, name=name, title=title, BuyForm=buyForm, SellForm=sellForm, net_stock=net_stock)


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
        init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
        price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"])
        share_count = latest_info["share_count"]
        market_value = round(share_count * price,2)
        last_update = (time() - update_time) //3600 # minutes ago
        instace_of_stock = Stock(uuid, name, last_update, round(price,2), share_count, market_value)
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
                next_page = url_for('query')
            return redirect(next_page)
    return render_template("login.html", form=form, title=title)

@app.route("/logout")
@login_required
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
            now_time = time()
            cash = 200000 # Starting cash
            net_worth = cash
            db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (username, now_time//1, cash, net_worth))
            db.commit()
            return redirect(url_for('login'))
    return render_template("register.html", form=form, title=title)

@app.route("/account", methods=["GET","POST"])
@login_required
def account():
    # latest data
    update_user_stats(g.user)
    db = get_db()
    username = g.user
    latest_data = db.execute("""SELECT * FROM user_hist WHERE username = ? ORDER BY time DESC;""", (username,) ).fetchone()
    if latest_data is not None:
        cashes = round(latest_data["cash"],2)
        net_worths = round(latest_data["net_worth"],2)
        user = User(username, cashes, net_worths)
    else:
        user = None
        return render_template("account.html", title=title, graph=None, user=user, stocks=None)
    # stock numbers owned
    uuids = []
    stock_dict = []
    db = get_db()
    stocks = db.execute("""SELECT DISTINCT stock_uuid FROM transactions WHERE username = ?;""", (username,)).fetchall()
    for stock in stocks:
        uuids.append(stock["stock_uuid"])
    for uuid in uuids:
        d = {}
        total_buy = db.execute("""SELECT SUM(quantity) as tot_buy FROM transactions 
                                WHERE buy = 1 AND stock_uuid = ? AND username = ?;""", (uuid, username)).fetchone()
        total_sell = db.execute("""SELECT SUM(quantity) as tot_sell FROM transactions 
                                WHERE buy = 0 AND stock_uuid = ? AND username = ?; """, (uuid, username)).fetchone()
        buy = total_buy["tot_buy"]
        sell = total_sell["tot_sell"]
        if sell is None:
            sell = 0
        total = buy-sell
        if total > 0:
            d["total"] = total
            init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
            value = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"], init_vals["seed"])
            d["net_worth"] = round(value*total,2)
            d["value"] = round(value,2)
            stock = db.execute("""SELECT name FROM stock_name WHERE stock_uuid = ?;""", (uuid,)).fetchone()
            d["name"] = stock["name"]
            d["uuid"] = uuid
            stock_dict.append(d)
    # net worth graph
    user_data = db.execute("""SELECT * FROM user_hist WHERE username = ? ORDER BY time ASC;""", (username,) ).fetchall()
    x_time, y_net_worth = [], []
    for instance in user_data:
        x_time.append(instance["time"])
        y_net_worth.append(instance["net_worth"])
    min_time = min(x_time)
    x_time = [(t-min_time) //60 for t in x_time]
    fig = Figure()
    ax = fig.add_subplot()
    ax.plot(x_time, y_net_worth)
    ax.ticklabel_format(style='plain', useOffset=False)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    graph = f"<img src='data:image/png;base64,{data}'/>"
    return render_template("account.html", title=title, graph=graph, user=user, stocks=stock_dict)

@app.route("/about", methods=["GET","POST"])
def about():
    return render_template("about.html", title=title)

@app.route("/admin", methods=["GET","POST"])
@admin_required
def admin():
    form = AdminNewStockForm()
    if form.validate_on_submit():
        stockname = form.stockname.data
        shorthand = form.shorthand.data
        init_valuation = form.valuation.data
        share_count = form.share_count.data
        start_time = time()
        sigma = (randint(0,40000)-20000) /100000 # returns a value bewteen -0.2 and 0.2
        mu = (randint(0,10000)-5000)/100000 # returns a value between -0.05 and 0.05
        seed = randint(0,100000)
        db = get_db()
        stocks = db.execute("""SELECT * FROM stock_name""").fetchall()
        for stock in stocks:
            if shorthand == stock["stock_uuid"]:
                form.shorthand.errors.append("Unique abbreviation needed.")
            if stockname == stock["name"]:
                form.stockname.errors.append("Stock name already exists.")
            if len(form.stockname.errors) != 0 or len(form.stockname.errors) != 0:
                return render_template("admin.html", form=form,  title=title)
        db.execute("""INSERT INTO stock_name VALUES (?, ?)""", (shorthand, stockname))
        db.execute("""INSERT INTO stock_hist VALUES (?, ?, ?, ?, ?, ?, ?)""", (shorthand, start_time, init_valuation, share_count, sigma, mu, seed))
        db.commit()
        return redirect(url_for("query"))
    return render_template("admin.html", form=form,  title=title)

@app.route("/gamble", methods=["GET","POST"])
def gamble():
    return render_template("gamble.html", title=title)

# https://flask.palletsprojects.com/en/1.1.x/patterns/errorpages/ 
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500