from flask import Flask, render_template, url_for, redirect, session, g, request, abort
from flask_session import Session
from forms import RegistrationForm, LoginForm, BuyForm, SellForm, AdminNewStockForm, GambleForm
from database import get_db, close_db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from classes import Stock, User
from time import time, sleep
import base64
from io import BytesIO
from matplotlib.figure import Figure
from random import randint, seed
from price_gen import generate_new_stock_price
from operator import itemgetter

title = "Pyramid Investments Ltd."
app = Flask(__name__)
app.config["SECRET_KEY"] = "efojiwsdlo&^diqwe34 3£93irefj9h-_f".encode('utf8')
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.teardown_appcontext(close_db)
Session(app)

"""
To log in as admin, use the username "admin" and password "3.14159" and you can access an extra dashboard

The formula used to calculate stock prices is based on a few factors and is calculated as a function of 
expected growth (mu), variability (sigma), the initial value of the stock, the time since the stock was
made and a randomness seed. This can be found in price_gen.py

Try to cause a 404 error and it will lead to an error page.
Similarly, a 500 error will also do the same, but is harder to trigger (hopefully)

on /gamble, there is an colour animation that only works on browsers that are not Safari or Firefox
(ie, chromium only) as it is an experimental feature.

I also added an API route, try with "NXCR" for a successful return value, and anything else for the error message.
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
        seed(init_vals["seed"])
        random_seeds = [randint(0,9999) for _ in range(100)]
        seed_no = random_seeds[int((time()//1)%100)]
        price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"],seed_no)
        net_worths.append(price*total)
    cash_d = db.execute("""SELECT cash FROM user_hist WHERE username = ? ORDER BY time DESC LIMIT 1;""", (username,)).fetchone()
    cash = cash_d["cash"]
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
    seed(init_vals["seed"])
    random_seeds = [randint(0,9999) for _ in range(100)]
    seed_no = random_seeds[int((time()//1)%100)]
    price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"],seed_no)
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
            seed(init_vals["seed"])
            random_seeds = [randint(0,9999) for _ in range(100)]
            seed_no = random_seeds[int((time()//1)%100)]
            price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"],seed_no)
            update_user_stats(g.user)
            db.execute("""INSERT into transactions (username, time, stock_uuid, quantity, price, buy) VALUES (?, ?, ?, ?, ?, ?);""", (g.user, time()//1, uuid, quant, price*quant, False))
            db.commit()
            d = db.execute("""SELECT cash, net_worth FROM user_hist WHERE username = ? ORDER BY time DESC LIMIT 1;""", (g.user,)).fetchone()
            cash = d["cash"]
            cash += price*quant
            net_worth = d["net_worth"]
            db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (g.user, time()//1, cash, net_worth))
            db.commit()
            sleep(1) # avoid duplicate user_info entry
            return redirect(url_for("account"))
    
    elif buyForm.validate_on_submit() and buyForm.quantity_buy.data:
        quant = buyForm.quantity_buy.data
        init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
        # consistent randomness
        seed(init_vals["seed"])
        random_seeds = [randint(0,9999) for _ in range(100)]
        seed_no = random_seeds[int((time()//1)%100)]
        price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"],seed_no)
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
            db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (g.user, time()//1, cash, net_worth))
            db.commit()
            sleep(1) # avoid duplicate user_info entry
            return redirect(url_for("account"))
    
    name = db.execute("""SELECT name FROM stock_name WHERE stock_uuid = ?;""", (uuid,)).fetchone()
    name = name["name"]
    init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
    t = init_vals["time"]
    curr_time = time()
    size = 100
    diff = (curr_time - t) / size
    valuations, time_x = [], []
    seed(init_vals["seed"])
    random_seeds = [randint(0,9999) for _ in range(size)]
    for i in range(size):
        new_t = t + diff*i
        seed_no = random_seeds[int((new_t//1)%size)]
        price = generate_new_stock_price(t, init_vals["valuation"], init_vals["mu"], init_vals["sigma"], seed_no, curr_time=new_t)
        time_x.append(new_t)
        valuations.append(price)
    min_time = min(time_x)
    time_x = [(t-min_time)/(3600) for t in time_x]
    fig = Figure()
    ax = fig.add_subplot()
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Value (€)")
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
    # Update for better data/records
    users = db.execute("""SELECT username FROM users""").fetchall()
    users = [user["username"] for user in users]
    for user in users:
        update_user_stats(user)
    stockList = []
    stocks = db.execute("""SELECT * FROM stock_name;""").fetchall()
    for stock in stocks:
        name = stock["name"]
        uuid = stock["stock_uuid"]
        latest_info = db.execute("""SELECT * FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC;""", (uuid,)).fetchone()
        update_time = latest_info["time"]
        init_vals = db.execute("""SELECT time, valuation, sigma, mu, seed FROM stock_hist WHERE stock_uuid = ? ORDER BY time DESC LIMIT 1""", (uuid,)).fetchone()
        seed(init_vals["seed"])
        random_seeds = [randint(0,9999) for _ in range(100)]
        seed_no = random_seeds[int((time()//1)%100)]
        price = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"],seed_no)
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
            seed(init_vals["seed"])
            random_seeds = [randint(0,9999) for _ in range(100)]
            seed_no = random_seeds[int((time()//1)%100)]
            value = generate_new_stock_price(init_vals["time"], init_vals["valuation"], init_vals["mu"], init_vals["sigma"],seed_no)
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
    x_time = [(t-min_time) /3600 for t in x_time]
    fig = Figure()
    ax = fig.add_subplot()
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Net Worth (€)")
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
        sigma = (randint(0,60000)-30000) /100000 # returns a value bewteen -0.3 and 0.3
        mu = (randint(0,20000)-10000)/100000 # returns a value between -0.1 and 0.1
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
        db.execute("""INSERT INTO stock_name VALUES (?, ?);""", (shorthand, stockname))
        db.execute("""INSERT INTO stock_hist VALUES (?, ?, ?, ?, ?, ?, ?);""", (shorthand, start_time, init_valuation, share_count, sigma, mu, seed))
        db.commit()
        return redirect(url_for("query"))
    return render_template("admin.html", form=form,  title=title)

@app.route("/gamble", methods=["GET","POST"])
@login_required
def gamble():
    form = GambleForm()
    if form.validate_on_submit():
        db = get_db()
        cash_d = db.execute("""SELECT cash, net_worth FROM user_hist WHERE username = ? ORDER BY time DESC LIMIT 1;""", (g.user,)).fetchone()
        cash = cash_d["cash"]
        net_worth = cash_d["net_worth"] - cash # stocks only
        guess = form.guess.data
        limit = form.limit.data
        bet = form.bet.data
        if bet > cash:
            form.bet.errors.append("You cannot afford your bet!")
            return render_template("gamble.html", title=title)
        if guess > limit:
            form.guess.errors.append("Guess cannot exceed the chosen limit.")
            return render_template("gamble.html", title=title)
        # to give a disadvantage to the user, I make limit+1 options. This reduces the expected value without changing the prize
        # It is deceiving to do this, but they will never know!
        guess_user = randint(1, limit+1) # User has illusion of the chosen number but I override it.
        target = randint(1,limit+1)
        if guess_user == target:
            payout = (limit*bet - bet)
            outcome = 1
        else:
            payout = -bet
            outcome = 0
        cash += payout
        net_worth = net_worth + cash # stocks + new cash
        db.execute("""INSERT INTO user_hist VALUES (?, ?, ?, ?);""", (g.user, time()//1, cash, net_worth))
        db.commit()
        d = {}
        d["payout"] = abs(payout)
        d["bet"] = bet
        d["user"] = g.user
        d["outcome"] = outcome
        return render_template("gamble_outcome.html", title=title, d=d)
    return render_template("gamble.html", title=title, form=form)

@app.route("/leaderboard")
@login_required
def leaderboard():
    db = get_db()
    users = db.execute("""SELECT username FROM users""").fetchall()
    users = [user["username"] for user in users]
    user_list = []
    for user in users:
        update_user_stats(user)
        net_val_dict = db.execute("""SELECT net_worth FROM user_hist WHERE username = ? ORDER BY time DESC LIMIT 1;""", (user,)).fetchone()
        net_val = net_val_dict["net_worth"]
        change = (net_val - 200000) / 2000
        d = {}
        d["net_val"] = round(net_val,2)
        d["change"] = round(change,2)
        d["name"] = user
        user_list.append(d)
    # Quick sorting by key of dict
    # https://docs.python.org/3/library/operator.html#operator.itemgetter
    sorted_leaderboard = sorted(user_list, key=itemgetter('change'), reverse=True) 
    return render_template("leaderboard.html", title=title, lb=sorted_leaderboard)

# https://flask.palletsprojects.com/en/1.1.x/patterns/errorpages/ 
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title=title), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html', title=title), 500