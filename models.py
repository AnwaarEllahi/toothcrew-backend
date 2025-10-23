from sqlalchemy import Column, Date, Integer, String, ForeignKey, DateTime, Text, Float, func, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy.orm import Mapped, mapped_column


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
    date_of_birth = Column(Date, nullable=True)  # Store DOB
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
from sqlalchemy.orm import Mapped, mapped_column

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    qualifications: Mapped[str] = mapped_column(String(500), nullable=False)
    pmdc_no: Mapped[str] = mapped_column(String(100), nullable=False)
    cnic: Mapped[str] = mapped_column(String(20), nullable=False)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------- Services ----------------
# class Service(Base):
#     __tablename__ = "services"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(250), nullable=False)
#     price = Column(String(100), nullable=False)        # e.g. "₨ 25,000"
#     type = Column(String(100), nullable=False)         # category: Ortho, Endo, Prostho, Maxillofacial
#     description = Column(Text, nullable=True)          # optional

# ---------------- Expenses ----------------
# class Expense(Base):
#     __tablename__ = "expenses"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String(200), nullable=False)
#     amount = Column(Integer, nullable=False)
#     category = Column(String(100), nullable=True)
#     date = Column(DateTime, default=datetime.utcnow)
#     description = Column(Text, nullable=True)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)       # e.g. "Doctor Commission (Dr ABC - X-Ray)"
    amount = Column(Integer, nullable=False)
    category = Column(String(100), nullable=True)     # optional tag like "Doctor", "Assistant", etc.
    source = Column(String(32), nullable=False, default="Others")  # NEW: "Doctor" | "Assistant" | "Receptionist" | "Others"
    date = Column(DateTime, default=datetime.utcnow, index=True)
    description = Column(Text, nullable=True)


# --- inventory ---

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    supplier = Column(String, nullable=False)
    invoice = Column(String, nullable=True)  # ← ADD THIS LINE if missing
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)            # ✅ NEW
    remaining_amount = Column(Float, default=0)       # ✅ NEW
    description = Column(String, nullable=True)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

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

#..........invoice ............


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String, unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    
    # Patient info snapshot (at time of invoice)
    patient_name = Column(String, nullable=False)
    patient_age = Column(Integer, nullable=False)
    patient_contact = Column(String, nullable=False)
    doctor_name = Column(String, nullable=True)
    
    # Invoice details
    date = Column(String, nullable=False)  # Invoice date
    due_date = Column(String, nullable=False)
    diagnosis = Column(Text, nullable=True)
    
    # Financial details
    subtotal = Column(Float, nullable=False, default=0.0)
    invoice_discount = Column(Float, nullable=False, default=0.0)
    amount_due = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    
    # Status and notes
    status = Column(String, nullable=False, default="Pending")  # Pending or Completed
    note = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    treatments = relationship("InvoiceTreatment", back_populates="invoice", cascade="all, delete-orphan")
    patient = relationship("Patient")
    doctor = relationship("Doctor")


class InvoiceTreatment(Base):
    __tablename__ = "invoice_treatments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    
    procedure = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, nullable=False, default=0.0)  # Discount percentage
    total = Column(Float, nullable=False)
    
    # Relationship
    invoice = relationship("Invoice", back_populates="treatments")


    
# #..............services ..................
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    services = relationship("Service", back_populates="category", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    price_amount = Column(Integer, nullable=True)  # stored in smallest unit (PKR integer)
    price_text = Column(String(64), nullable=True)  # e.g. "Rs. 2000"
    currency = Column(String(8), default="PKR")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category", back_populates="services")