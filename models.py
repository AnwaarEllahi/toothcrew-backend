from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, func, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# ---------------- Users ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    role = Column(String(50), default="receptionist")
    password = Column(String(200), nullable=False)

    patients = relationship("Patient", back_populates="owner_doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")


# ---------------- Patients ----------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    contact = Column(Integer, nullable=False)

    # 👇 add these new columns
    age = Column(Integer, nullable=True)
    medical_history = Column(String, nullable=True)
    city = Column(String(100), nullable=True)

    owner_doctor = relationship("User", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")



# ---------------- Appointments ----------------
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    status = Column(String(50), default="scheduled")
    notes = Column(Text, nullable=True)

    doctor = relationship("User", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")


# ---------------- Doctors ----------------
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    qualifications = Column(String(500), nullable=False)


# ---------------- Services ----------------
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), nullable=False)
    price = Column(String(100), nullable=False)        # e.g. "₨ 25,000"
    type = Column(String(100), nullable=False)         # category: Ortho, Endo, Prostho, Maxillofacial
    description = Column(Text, nullable=True)          # optional

# ---------------- Expenses ----------------
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    amount = Column(Integer, nullable=False)
    category = Column(String(100), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)

# --- inventory ---

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    supplier = Column(String(100), nullable=False)
    invoice = Column(String(100), nullable=False)   # 👈 ADD THIS LINE
    amount = Column(Float, nullable=False)
    description = Column(String(255))
    date = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# #..............services ..................
# class Category(Base):
#     __tablename__ = "categories"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(128), unique=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     services = relationship("Service", back_populates="category", cascade="all, delete-orphan")

# class Service(Base):
#     __tablename__ = "services"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(256), nullable=False)
#     price_amount = Column(Integer, nullable=True)  # stored in smallest unit (PKR integer)
#     price_text = Column(String(64), nullable=True)  # e.g. "Rs. 2000"
#     currency = Column(String(8), default="PKR")
#     category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
#     is_active = Column(Boolean, default=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())

#     category = relationship("Category", back_populates="services")