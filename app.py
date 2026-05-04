from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(_name_)
app.config['SECRET_KEY'] = "nsrit_smart_hms_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///smart_hms.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20)) # 'admin', 'doctor', 'patient'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_custom_id = db.Column(db.String(30), unique=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    consultations = db.relationship('Consultation', backref='patient', lazy=True)

class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_name = db.Column(db.String(100))
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

def generate_patient_id():
    count = Patient.query.count()
    return f"NSR-HMS-2026-{count + 1:04d}"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password="password123", role="admin"))
        db.session.add(User(username="doctor1", password="docpassword", role="doctor"))
        db.session.add(User(username="patient1", password="password123", role="patient"))
        db.session.commit()

# --- ROUTES ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template("admin_dash.html", patients=Patient.query.all())
    elif current_user.role == 'doctor':
        return render_template("doctor_dash.html", patients=Patient.query.all())
    else:
        p_record = Patient.query.filter_by(name=current_user.username).first()
        return render_template("patient_dash.html", patient=p_record)

@app.route("/register_patient", methods=["GET", "POST"])
@login_required
def register_patient():
    if current_user.role != 'admin': return "Denied", 403
    if request.method == "POST":
        p = Patient(patient_custom_id=generate_patient_id(), name=request.form.get("name"), 
                    age=request.form.get("age"), gender=request.form.get("gender"), 
                    address=request.form.get("address"))
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/consultation/<int:patient_id>", methods=["GET", "POST"])
@login_required
def consultation(patient_id):
    p = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        # Combines the notes and follow-up for a complete prescription view
        notes_with_date = f"{request.form.get('notes')}\n\nFollow-up: {request.form.get('follow_up')}"
        c = Consultation(patient_id=p.id, doctor_name=current_user.username,
                         diagnosis=request.form.get("diagnosis"), notes=notes_with_date)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("consultation.html", patient=p)

@app.route("/logout")
def logout():
    logout_user(); return redirect(url_for("home"))

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
