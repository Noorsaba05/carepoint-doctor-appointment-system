
from app import app, db, User, Doctor, Department
from werkzeug.security import generate_password_hash

demo_doctors = [
    {
        "name": "Dr. Ayesha Khan",
        "email": "ayesha.khan@carepoint.demo",
        "department": "Cardiology",
        "qualification": "MBBS, MD Cardiology",
        "specialization": "Cardiology",
        "experience": 12,
        "fee": 800
    },
    {
        "name": "Dr. Rahul Sharma",
        "email": "rahul.sharma@carepoint.demo",
        "department": "Neurology",
        "qualification": "MBBS, DM Neurology",
        "specialization": "Neurology",
        "experience": 10,
        "fee": 700
    },
    {
        "name": "Dr. Priya Deshmukh",
        "email": "priya.deshmukh@carepoint.demo",
        "department": "Orthopedics",
        "qualification": "MBBS, MS Orthopedics",
        "specialization": "Orthopedics",
        "experience": 8,
        "fee": 600
    },
    {
        "name": "Dr. Sameer Patel",
        "email": "sameer.patel@carepoint.demo",
        "department": "General Medicine",
        "qualification": "MBBS, MD Medicine",
        "specialization": "General Medicine",
        "experience": 15,
        "fee": 500
    },
    {
        "name": "Dr. Fatima Shaikh",
        "email": "fatima.shaikh@carepoint.demo",
        "department": "Dermatology",
        "qualification": "MBBS, MD Dermatology",
        "specialization": "Dermatology",
        "experience": 9,
        "fee": 650
    },
    {
        "name": "Dr. Neha Joshi",
        "email": "neha.joshi@carepoint.demo",
        "department": "Pediatrics",
        "qualification": "MBBS, MD Pediatrics",
        "specialization": "Pediatrics",
        "experience": 11,
        "fee": 600
    }
]

with app.app_context():

    try:
        for item in demo_doctors:

            existing_user = User.query.filter_by(
                email=item["email"]
            ).first()

            if existing_user:
                print("Already exists:", item["name"])
                continue

            department = Department.query.filter_by(
                department_name=item["department"]
            ).first()

            if not department:
                raise ValueError(
                    "Department not found: " + item["department"]
                )

            user = User(
                full_name=item["name"],
                email=item["email"],
                password=generate_password_hash("DemoDoctor123!"),
                role="doctor"
            )

            db.session.add(user)
            db.session.flush()

            doctor = Doctor(
                user_id=user.user_id,
                department_id=department.department_id,
                qualification=item["qualification"],
                specialization=item["specialization"],
                experience=item["experience"],
                consultation_fee=item["fee"],
                availability_status=True
            )

            db.session.add(doctor)

        db.session.commit()
        print("\nDoctor records added successfully!")

    except Exception as error:
        db.session.rollback()
        print("Error:", error)
        raise

    print("\nCurrent doctor directory:")

    doctors = Doctor.query.all()

    for doctor in doctors:
        print(
            doctor.name,
            "|",
            doctor.specialization,
            "|",
            doctor.department.department_name
        )
