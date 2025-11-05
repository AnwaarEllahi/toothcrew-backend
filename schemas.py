# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr , Field, model_validator, validator
from datetime import date, datetime
from typing import Literal, Optional
from typing import List, Optional, Any


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




# class PatientCreate(BaseModel):
#     name: str
#     contact: int
#     doctor_id: Optional[int] = None
#     doctor_name: Optional[str] = None  # 👈 Allow frontend to send name
#     date_of_birth: Optional[date] = None
#     medical_history: Optional[str] = None
#     city: Optional[str] = None


#     @validator('date_of_birth')
#     def validate_dob(cls, v):
#         if v and v > date.today():
#             raise ValueError('Date of birth cannot be in the future')
#         return v
class PatientCreate(BaseModel):
    name: str
    contact: int  # ✅ Keep as int in Pydantic (it handles BigInteger automatically)
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None  # Frontend can send this but we ignore it
    date_of_birth: Optional[date] = None
    medical_history: Optional[str] = None
    city: Optional[str] = None

    @validator('date_of_birth')
    def validate_dob(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v


# class PatientUpdate(BaseModel):
#     name: Optional[str]
#     doctor_id: Optional[int]
#     contact: Optional[int]
#     age: Optional[int]
#     date_of_birth: Optional[date] = None  # ✅ DOB field
#     medical_history: Optional[str]
#     city: Optional[str]

#     @validator('date_of_birth')
#     def validate_dob(cls, v):
#         if v and v > date.today():
#             raise ValueError('Date of birth cannot be in the future')
#         return v

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    doctor_id: Optional[int] = None
    contact: Optional[int] = None
    age: Optional[int] = None
    date_of_birth: Optional[date] = None
    medical_history: Optional[str] = None
    city: Optional[str] = None

    @validator('date_of_birth')
    def validate_dob(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v

# class PatientOut(BaseModel):
#     id: int
#     name: str
#     created_at: datetime
#     doctor_id: Optional[int] = None  # keep it for internal use
#     doctor_name: Optional[str] = None  # show this on frontend
#     contact: int
#     date_of_birth: Optional[date] = None
#     age: Optional[int] = None
#     medical_history: Optional[str] = None
#     city: Optional[str] = None

#     class Config:
#         orm_mode = True
        
#     @validator('age', always=True)
#     def calculate_age(cls, v, values):
#         """Calculate age from date_of_birth"""
#         dob = values.get('date_of_birth')
#         if dob:
#             today = date.today()
#             age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
#             return age
#         return None    


class PatientOut(BaseModel):
    id: int
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    doctor_id: Optional[int] = None
    doctor_name: Optional[Any] = None
    contact: Optional[int] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    medical_history: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True  # ✅ Updated for Pydantic v2 (was orm_mode)
        # orm_mode = True  # Use this if you're on Pydantic v1
        
    @validator('age', always=True)
    def calculate_age(cls, v, values):
        """Calculate age from date_of_birth"""
        dob = values.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        return None



# class AppointmentCreate(BaseModel):
#     patient_id: int
#     doctor_id: int
#     appointment_datetime: datetime
#     status: Optional[str] = "scheduled"
#     notes: Optional[str] = None

# class AppointmentOut(BaseModel):
#     id: int
#     patient_id: int
#     doctor_id: int
#     appointment_datetime: datetime
#     status: str
#     notes: Optional[str]
#     patient_name: Optional[str] = None   # ← add this


#     class Config:
#         orm_mode = True

# class AppointmentCreate(BaseModel):
#     patient_id: int
#     doctor_id: int
#     appointment_datetime: datetime
#     status: Optional[str] = "scheduled"
#     notes: Optional[str] = None

class AppointmentCreate(BaseModel):
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    doctor_id: int
    appointment_datetime: datetime
    status: Optional[str] = "scheduled"
    notes: Optional[str] = None

    @model_validator(mode="after")
    def check_patient_inputs(self):
        if not self.patient_id and not (self.patient_name and self.patient_name.strip()):
            raise ValueError("Provide patient_id or patient_name")
        return self

class AppointmentOut(BaseModel):
    id: int
    patient_id: Optional[int] = None
    doctor_id: int
    appointment_datetime: datetime
    status: str
    notes: str
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AppointmentUpdate(BaseModel):
    doctor_id: Optional[int] = None
    appointment_datetime: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    patient_name: Optional[str] = None
    patient_id: Optional[int] = None

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
    description: str  # Changed from 'procedure'
    quantity: int
    unit_price: float
    total: float
    # Removed per-treatment discount since frontend doesn't use it

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
    diagnosis: Optional[str] = None
    treatments: list[TreatmentCreate]
    subtotal: float
    discount: float = 0.0  # Changed from 'invoice_discount' to match frontend
    total: float  # Added to match frontend calculation
    # Removed due_date, paid_amount, status, note as frontend doesn't use them initially


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
    diagnosis: Optional[str]
    subtotal: float
    discount: float
    total: float
    treatments: List[TreatmentOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceUpdate(BaseModel):
    diagnosis: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    total: Optional[float] = None



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
