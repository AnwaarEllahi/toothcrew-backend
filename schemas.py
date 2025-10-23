# schemas.py
from pydantic import BaseModel, EmailStr , Field, validator
from datetime import date, datetime
from typing import Literal, Optional
from typing import List, Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "receptionist"
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int
    role: str

class PatientCreate(BaseModel):
    name: str
    doctor_id: Optional[int] 
    contact : int
    age: Optional[int] = None   # ✅ make it optional
    date_of_birth: Optional[date] = None  # ✅ DOB field
    medical_history: Optional[str] = None
    city: Optional[str] = None
    # name: str
    # contact: int
    # city: Optional[str] = None
    # date_of_birth: Optional[date] = None
    # medical_history: Optional[str] = None

    @validator('date_of_birth')
    def validate_dob(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v


class PatientUpdate(BaseModel):
    name: Optional[str]
    doctor_id: Optional[int]
    contact: Optional[int]
    age: Optional[int]
    date_of_birth: Optional[date] = None  # ✅ DOB field
    medical_history: Optional[str]
    city: Optional[str]

    @validator('date_of_birth')
    def validate_dob(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v

class PatientOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    doctor_id: Optional[int]
    contact: int
    date_of_birth: Optional[date] = None  # ✅ DOB field
    age: Optional[int] = None  # ✅ Calculated age (computed property)
    medical_history: Optional[str] = None
    city: Optional[str] = None

    class Config:
        orm_mode = True
        
    @validator('age', always=True)
    def calculate_age(cls, v, values):
        """Calculate age from date_of_birth"""
        dob = values.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        return None    

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_datetime: datetime
    status: Optional[str] = "scheduled"
    notes: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_datetime: datetime
    status: str
    notes: Optional[str]

    class Config:
        orm_mode = True

# schemas.py

# from typing import Optional

from typing import Optional
from pydantic import BaseModel

class DoctorCreate(BaseModel):
    name: str
    qualifications: str
    pmdc_no: str
    cnic: str
    is_disabled: Optional[bool] = False

class DoctorOut(BaseModel):
    id: int
    name: str
    qualifications: str
    pmdc_no: str
    cnic: str
    is_disabled: bool

    class Config:
        from_attributes = True  # Updated for Pydantic v2 (use orm_mode = True for Pydantic v1)

# # schemas.py (services)
# from pydantic import BaseModel
# from typing import Optional

# class ServiceCreate(BaseModel):
#     name: str
#     price: str
#     type: str
#     description: Optional[str] = None

# class ServiceOut(BaseModel):
#     id: int
#     name: str
#     price: str
#     type: str
#     description: Optional[str] = None

#     class Config:
#         orm_mode = True


# ---------------- Expense Schemas ----------------
# from datetime import datetime
# from pydantic import BaseModel
# from typing import Optional

# class ExpenseBase(BaseModel):
#     title: str
#     amount: int
#     category: Optional[str] = None
#     description: Optional[str] = None

# class ExpenseCreate(ExpenseBase):
#     pass

# class ExpenseOut(ExpenseBase):
#     id: int
#     date: datetime

#     class Config:
#         orm_mode = True



class ExpenseBase(BaseModel):
    title: str
    amount: int
    category: Optional[str] = None
    source: Literal["Doctor", "Assistant", "Receptionist", "Others"] = "Others"
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseOut(ExpenseBase):
    id: int
    date: datetime
    class Config:
        orm_mode = True



# --- inventory schemas ---
class InventoryCreate(BaseModel):
    supplier: str
    invoice: Optional[str] = ""  # ADD THIS LINE
    amount: float
    paid_amount: Optional[float] = 0           # ✅ NEW
    remaining_amount: Optional[float] = 0      # ✅ NEW
    description: Optional[str] = ""

class InventoryOut(BaseModel):
    id: int
    supplier: str
    invoice: str  # ADD THIS LINE
    amount: float
    paid_amount: float                       # ✅ NEW
    remaining_amount: float                  # ✅ NEW
    description: str
    date: str
    time: str
    created_at: datetime

    class Config:
        from_attributes = True


# #...... servies schemas ..........
# class CategoryBase(BaseModel):
#     name: str = Field(..., example="Ortho")

# class CategoryCreate(CategoryBase):
#     pass

# class CategoryOut(CategoryBase):
#     id: int
#     created_at: Optional[datetime]

#     class Config:
#         orm_mode = True

# class ServiceBase(BaseModel):
#     name: str = Field(..., example="Root Canal")
#     price_text: Optional[str] = Field(None, example="Rs. 2000")
#     price_amount: Optional[int] = Field(None, example=2000, description="Price in PKR integer")
#     currency: Optional[str] = Field("PKR")

# class ServiceCreate(ServiceBase):
#     category_id: int

# class ServiceUpdate(BaseModel):
#     name: Optional[str]
#     price_text: Optional[str]
#     price_amount: Optional[int]
#     is_active: Optional[bool]
#     category_id: Optional[int]

# class ServiceOut(ServiceBase):
#     id: int
#     category_id: int
#     is_active: bool
#     created_at: Optional[datetime]
#     updated_at: Optional[datetime]

#     class Config:
#         orm_mode = True



#..........invoice ..........
# Treatment schemas
class TreatmentBase(BaseModel):
    procedure: str
    quantity: int
    unit_price: float
    discount: float = 0.0
    total: float

class TreatmentCreate(TreatmentBase):
    pass

class TreatmentOut(TreatmentBase):
    id: int
    invoice_id: int

    class Config:
        from_attributes = True


# Invoice schemas
class InvoiceCreate(BaseModel):
    invoice_no: str
    patient_id: int
    doctor_id: Optional[int] = None
    patient_name: str
    patient_age: int
    patient_contact: str
    doctor_name: Optional[str] = None
    date: str
    due_date: str
    diagnosis: Optional[str] = None
    treatments: list[TreatmentCreate]
    subtotal: float
    invoice_discount: float = 0.0
    amount_due: float
    paid_amount: float = 0.0
    status: str = "Pending"
    note: Optional[str] = None


class InvoiceOut(BaseModel):
    id: int
    invoice_no: str
    patient_id: int
    doctor_id: Optional[int]
    patient_name: str
    patient_age: int
    patient_contact: str
    doctor_name: Optional[str]
    date: str
    due_date: str
    diagnosis: Optional[str]
    subtotal: float
    invoice_discount: float
    amount_due: float
    paid_amount: float
    status: str
    note: Optional[str]
    treatments: List[TreatmentOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    paid_amount: Optional[float] = None
    note: Optional[str] = None



# #...... servies schemas ..........
class CategoryBase(BaseModel):
    name: str = Field(default=..., examples=["Ortho"])

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class ServiceBase(BaseModel):
    name: str = Field(default=..., examples=["Root Canal"])
    price_text: Optional[str] = Field(default=None, examples=["Rs. 2000"])
    price_amount: Optional[int] = Field(default=None, examples=[2000], description="Price in PKR integer")
    currency: Optional[str] = Field(default="PKR")

# class ServiceCreate(ServiceBase):
#     category_id: int

class ServiceUpdate(BaseModel):
    name: Optional[str]
    price_text: Optional[str]
    price_amount: Optional[int]
    is_active: Optional[bool]
    category_id: Optional[int]

# class ServiceOut(ServiceBase):
#     id: int
#     category_id: int
#     is_active: bool
#     created_at: Optional[datetime]
#     updated_at: Optional[datetime]

#     class Config:
#         orm_mode = True


# schemas.py (services)
from pydantic import BaseModel
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    price_amount: int
    price_text: Optional[str] = None
    currency: Optional[str] = "PKR"
    category_id: int


class ServiceOut(BaseModel):
    id: int
    name: str
    price_amount: Optional[int]
    price_text: Optional[str]
    currency: Optional[str]
    category_id: int
    is_active: bool

    class Config:
        orm_mode = True
