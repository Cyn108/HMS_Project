from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(_name_)
app.config['SECRET_KEY'] = "secret123"
# Render works best with an absolute path for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hms.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "login"

# ------------ MODELS ------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    illness = db.Column(db.String(200))

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------ DATABASE INITIALIZATION ------------
# Moving this OUTSIDE the "if _name_ == '_main_'" block 
# so Render runs it every time the app starts.
with app.app_context():
    db.create_all()
    # OPTIONAL: Create a default admin user if the table is empty
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="password123", role="admin")
        db.session.add(admin)
        db.session.commit()

# ------------ ROUTES ------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login_route(): # Renamed function to 'login_route' to avoid conflict with 'login' manager
    if request.method == "POST":
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.password == request.form['password']:
            login_user(u)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/register_patient", methods=["GET", "POST"])
@login_required
def register_patient():
    if request.method == "POST":
        p = Patient(
            name=request.form["name"],
            age=request.form["age"],
            gender=request.form["gender"],
            illness=request.form["illness"]
        )
        db.session.add(p)
        db.session.commit()
        flash("Patient Registered")
        return redirect(url_for("dashboard")) # Changed to dashboard so you can see success
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login_route"))

# ------------ RUN ------------

if _name_ == "_main_":
    app.run(debug=True)
