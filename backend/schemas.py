from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

class ProfileCreateSchema(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str
    city: str
    postal_code: str
    premise_type: str = "house"
    household_size: int = 1
    upi_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RecyclingEntrySchema(BaseModel):
    user_id: Optional[int] = None
    waste_category: str
    weight_kg: float = Field(..., gt=0, description="Weight must be greater than 0")
    payout_amount: float
    station_id: Optional[str] = None
    payout_method: Optional[str] = "upi"
    model_config = ConfigDict(from_attributes=True)

class StaffRegisterSchema(BaseModel):
    email: EmailStr
    full_name: str
    assigned_pincode: str
    password: str

class StaffLoginSchema(BaseModel):
    email: EmailStr
    password: str

class StaffReviewSchema(BaseModel):
    action: str  
    rejection_reason: Optional[str] = None

class EntryReviewSchema(BaseModel):
    action: str  
    rejection_reason: Optional[str] = None
    staff_id: Optional[int] = None
    
    
class OrderCreateSchema(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in INR to create an order for")
    user_id: int

class PaymentVerifySchema(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    entry_id: Optional[int] = None

class UPIPayoutSchema(BaseModel):
    user_id: int
    upi_id: str = Field(..., description="UPI VPA handle", examples=["user@upi"])
    amount: float = Field(..., gt=0, description="Payout amount in INR")