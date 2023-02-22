from flask import Flask, render_template
from forms import Form
from database import get_db, close_db
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "1"
app.teardown_appcontext(close_db)

@app.route("/", methods=["GET","POST"])
def home():
    form = Form()
    if form.validate_on_submit():
        data = form.obj.data
        print(data)
    return render_template("home.html", form=form)

@app.route("/buy", methods=["GET","POST"])
def buy():
    pass

@app.route("/sell", methods=["GET","POST"])
def sell():
    pass

@app.route("/query", methods=["GET","POST"])
def query():
    pass

@app.route("/login", methods=["GET","POST"])
def login():
    pass

@app.route("/register", methods=["GET","POST"])
def register():
    pass

@app.route("/gamble", methods=["GET","POST"])
def gamble():
    pass

@app.route("/account", methods=["GET","POST"])
def account():
    pass

@app.route("/about", methods=["GET","POST"])
def about():
    pass

@app.route("/admin", methods=["GET","POST"])
def admin():
    pass