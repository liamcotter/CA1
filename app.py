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