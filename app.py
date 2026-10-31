
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from datetime import date, datetime, time
from config import Config

# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please login to continue."


# ==========================================
# DATABASE MODELS
# ==========================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="patient")

    def get_id(self):
        return str(self.user_id)


class Patient(db.Model):
    __tablename__ = "patients"

    patient_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        unique=True,
        nullable=False
    )
    phone = db.Column(db.String(15))
    gender = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.Text)


class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)


class Doctor(db.Model):
    __tablename__ = "doctors"

    doctor_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        unique=True
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.department_id"),
        nullable=False
    )

    qualification = db.Column(db.String(150))
    specialization = db.Column(db.String(150))
    experience = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Numeric(10, 2), default=0)
    availability_status = db.Column(db.Boolean, default=True)

    user = db.relationship(
        "User",
        backref=db.backref("doctor_profile", uselist=False)
    )

    department = db.relationship(
        "Department",
        backref="doctors"
    )

    @property
    def name(self):
        return self.user.full_name if self.user else "Doctor"

    @property
    def available(self):
        return bool(self.availability_status)


class Appointment(db.Model):
    __tablename__ = "appointments"

    appointment_id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.patient_id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.doctor_id"),
        nullable=False
    )

    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.Text)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    doctor = db.relationship(
        "Doctor",
        backref="appointments"
    )

    patient = db.relationship(
        "Patient",
        backref="appointments"
    )


# ==========================================
# LOGIN MANAGER
# ==========================================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==========================================
# INITIAL DATABASE SETUP
# ==========================================

def initialize_database():

    with app.app_context():

        db.create_all()

        if Department.query.count() == 0:

            departments = [
                Department(
                    department_name="Cardiology",
                    description="Heart and cardiovascular care"
                ),
                Department(
                    department_name="Neurology",
                    description="Brain and nervous system care"
                ),
                Department(
                    department_name="Orthopedics",
                    description="Bone, joint and muscle care"
                ),
                Department(
                    department_name="General Medicine",
                    description="General health consultations"
                ),
                Department(
                    department_name="Dermatology",
                    description="Skin, hair and nail care"
                ),
                Department(
                    department_name="Pediatrics",
                    description="Healthcare for infants and children"
                )
            ]

            db.session.add_all(departments)
            db.session.commit()


# ==========================================
# HOMEPAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# REGISTRATION
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill all required fields.", "error")

        elif len(name) > 100 or len(email) > 120:
            flash("Name or email is too long.", "error")

        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")

        elif password != confirm:
            flash("Passwords do not match.", "error")

        elif User.query.filter_by(email=email).first():
            flash("Email is already registered.", "error")

        else:

            try:

                user = User(
                    full_name=name,
                    email=email,
                    password=generate_password_hash(password),
                    role="patient"
                )

                db.session.add(user)
                db.session.flush()

                patient = Patient(
                    user_id=user.user_id
                )

                db.session.add(patient)
                db.session.commit()

                flash(
                    "Account created successfully! Please login.",
                    "success"
                )

                return redirect(url_for("login"))

            except Exception:

                db.session.rollback()
                app.logger.exception("Registration error")

                flash(
                    "Registration failed. Please try again.",
                    "error"
                )

    return render_template("register.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash("Welcome back!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# ==========================================
# PATIENT DASHBOARD
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "patient":

        flash("Patient access only.", "error")
        return redirect(url_for("home"))

    patient = Patient.query.filter_by(
        user_id=current_user.user_id
    ).first_or_404()

    appointments = Appointment.query.filter_by(
        patient_id=patient.patient_id
    ).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()

    upcoming = Appointment.query.filter(
        Appointment.patient_id == patient.patient_id,
        Appointment.appointment_date >= date.today(),
        Appointment.status.in_(["pending", "confirmed"])
    ).order_by(
        Appointment.appointment_date,
        Appointment.appointment_time
    ).all()

    return render_template(
        "dashboard.html",
        patient=patient,
        appointments=appointments,
        upcoming=upcoming,
        total=len(appointments),
        upcoming_count=len(upcoming),
        today=date.today()
    )


# ==========================================
# DOCTOR DIRECTORY
# ==========================================

@app.route("/doctors")
@login_required
def doctors():

    search = request.args.get("search", "").strip()

    query = Doctor.query.join(User).filter(
        Doctor.availability_status.is_(True)
    )

    if search:

        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                Doctor.specialization.ilike(f"%{search}%"),
                Doctor.qualification.ilike(f"%{search}%")
            )
        )

    doctor_list = query.order_by(
        User.full_name
    ).all()

    return render_template(
        "doctors.html",
        doctors=doctor_list,
        search=search
    )


# ==========================================
# BOOK APPOINTMENT
# ==========================================

@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def book_appointment(doctor_id):

    if current_user.role != "patient":

        flash("Only patients can book appointments.", "error")
        return redirect(url_for("home"))

    doctor = Doctor.query.filter_by(
        doctor_id=doctor_id,
        availability_status=True
    ).first_or_404()

    patient = Patient.query.filter_by(
        user_id=current_user.user_id
    ).first_or_404()

    slots = [
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00"
    ]

    if request.method == "POST":

        date_value = request.form.get(
            "appointment_date", ""
        )

        time_value = request.form.get(
            "appointment_time", ""
        )

        reason = request.form.get(
            "reason", ""
        ).strip()

        try:

            appointment_date = date.fromisoformat(date_value)
            appointment_time = time.fromisoformat(time_value)

            if appointment_date < date.today():
                raise ValueError("Past dates are not allowed.")

            if time_value not in slots:
                raise ValueError("Invalid appointment time.")

            if appointment_date == date.today():

                if appointment_time <= datetime.now().time():
                    raise ValueError(
                        "Please choose a future time."
                    )

            if len(reason) > 500:
                raise ValueError(
                    "Reason must be 500 characters or fewer."
                )

            existing = Appointment.query.filter_by(
                doctor_id=doctor.doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).filter(
                Appointment.status.in_(["pending", "confirmed"])
            ).first()

            if existing:

                flash(
                    "This slot is already booked. Choose another.",
                    "error"
                )

            else:

                appointment = Appointment(
                    patient_id=patient.patient_id,
                    doctor_id=doctor.doctor_id,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    reason=reason,
                    status="pending"
                )

                db.session.add(appointment)
                db.session.commit()

                flash(
                    "Appointment booked successfully!",
                    "success"
                )

                return redirect(url_for("appointments"))

        except ValueError as error:

            flash(str(error), "error")

        except Exception:

            db.session.rollback()
            app.logger.exception("Appointment booking failed")

            flash(
                "Could not book appointment. Please try again.",
                "error"
            )

    return render_template(
        "book_appointment.html",
        doctor=doctor,
        slots=slots,
        today=date.today().isoformat()
    )


# ==========================================
# MY APPOINTMENTS
# ==========================================

@app.route("/appointments")
@login_required
def appointments():

    patient = Patient.query.filter_by(
        user_id=current_user.user_id
    ).first_or_404()

    appointment_list = Appointment.query.filter_by(
        patient_id=patient.patient_id
    ).order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()

    return render_template(
        "appointments.html",
        appointments=appointment_list,
        today=date.today()
    )


# ==========================================
# CANCEL APPOINTMENT
# ==========================================

@app.route("/cancel/<int:appointment_id>", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):

    patient = Patient.query.filter_by(
        user_id=current_user.user_id
    ).first_or_404()

    appointment = Appointment.query.filter_by(
        appointment_id=appointment_id,
        patient_id=patient.patient_id
    ).first_or_404()

    if appointment.status not in ["pending", "confirmed"]:

        flash(
            "This appointment cannot be cancelled.",
            "error"
        )

    elif appointment.appointment_date < date.today():

        flash(
            "Past appointments cannot be cancelled.",
            "error"
        )

    else:

        appointment.status = "cancelled"
        db.session.commit()

        flash(
            "Appointment cancelled successfully.",
            "success"
        )

    return redirect(url_for("appointments"))


# ==========================================
# PATIENT PROFILE
# ==========================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    patient = Patient.query.filter_by(
        user_id=current_user.user_id
    ).first_or_404()

    if request.method == "POST":

        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "").strip()
        dob = request.form.get("date_of_birth", "")
        address = request.form.get("address", "").strip()

        if len(phone) > 15 or len(address) > 2000:

            flash(
                "Please check your phone number or address.",
                "error"
            )

        elif gender not in ["", "Male", "Female", "Other"]:

            flash(
                "Invalid gender selection.",
                "error"
            )

        else:

            try:

                patient.phone = phone or None
                patient.gender = gender or None
                patient.address = address or None

                patient.date_of_birth = (
                    date.fromisoformat(dob) if dob else None
                )

                if (
                    patient.date_of_birth
                    and patient.date_of_birth > date.today()
                ):
                    raise ValueError(
                        "Date of birth cannot be in the future."
                    )

                db.session.commit()

                flash(
                    "Profile updated successfully!",
                    "success"
                )

            except ValueError as error:

                db.session.rollback()
                flash(str(error), "error")

            except Exception:

                db.session.rollback()
                app.logger.exception("Profile update failed")

                flash(
                    "Unable to update profile.",
                    "error"
                )

    return render_template(
        "profile.html",
        patient=patient,
        user=current_user
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(url_for("home"))


# ==========================================
# DATABASE TEST
# ==========================================

@app.route("/test-db")
def test_db():

    result = db.session.execute(
        text("SELECT DATABASE()")
    ).scalar()

    return (
        f"Database connected successfully: {result}"
    )


# ==========================================
# APPLICATION START
# ==========================================

if __name__ == "__main__":

    initialize_database()

    app.run(debug=True)
