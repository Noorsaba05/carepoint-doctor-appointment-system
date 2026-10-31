
import os
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()

class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "carepoint-development-key"
    )

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username="root",
        password=os.getenv("DB_PASSWORD", "noor0511"),
        host="localhost",
        port=3306,
        database="doctor_appointment_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
