from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
from backend.database import get_db, UserProfile, RecyclingEntry
from backend.custom_logging import logger
from backend.schemas import RecyclingEntrySchema
from pdf_generator import generate_receipt_pdf

router = APIRouter(prefix="/api/recycling", tags=["Recycling Transactions"])

@router.post("/entry")
async def add_recycling_entry(data: RecyclingEntrySchema, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first() if data.user_id else None
    if not user:
        raise HTTPException(status_code=404, detail=f"User ID {data.user_id} not found.")
        
    new_entry = RecyclingEntry(
        user_id=user.id,
        waste_category=data.waste_category,
        weight_kg=data.weight_kg,
        payout_amount=data.payout_amount,
        station_id=data.station_id,
        status="pending"
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"status": "success", "message": "Recycling transaction recorded!", "entry_id": new_entry.entry_id}

@router.get("/pending-payments")
async def get_pending_payments(user_id: Optional[int] = Query(None), email: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        user_id = user.id

    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id, RecyclingEntry.status == "pending").all()
    return {"status": "success", "total_pending_amount": sum(float(e.payout_amount) for e in entries), "entries": [{"entry_id": e.entry_id, "waste_category": e.waste_category, "weight_kg": float(e.weight_kg), "payout_amount": float(e.payout_amount)} for e in entries]}

@router.get("/reviewed-requests")
async def get_reviewed_requests(user_id: Optional[int] = Query(None), email: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        user_id = user.id

    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id, RecyclingEntry.status.in_(["approved", "declined"])).all()
    return {"status": "success", "entries": [{"entry_id": e.entry_id, "waste_category": e.waste_category, "weight_kg": float(e.weight_kg), "payout_amount": float(e.payout_amount), "status": e.status} for e in entries]}

@router.get("/summary")
async def get_user_recycling_summary(user_id: Optional[int] = Query(None), email: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if not user_id and email:
        user = db.query(UserProfile).filter(UserProfile.email == email).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        user_id = user.id
    entries = db.query(RecyclingEntry).filter(RecyclingEntry.user_id == user_id).all() if user_id else []
    return {"status": "success", "total_earnings": sum(float(e.payout_amount) for e in entries if e.status == "approved"), "pending_release": sum(float(e.payout_amount) for e in entries if e.status == "pending")}

@router.get("/receipt/{entry_id}")
async def download_receipt(entry_id: int, db: Session = Depends(get_db)):
    result = db.query(RecyclingEntry, UserProfile).join(UserProfile, RecyclingEntry.user_id == UserProfile.id).filter(RecyclingEntry.entry_id == entry_id).first()
    if not result: raise HTTPException(status_code=404, detail="Receipt not found")
    entry, user = result
    pdf_bytes = generate_receipt_pdf({"entry_id": entry.entry_id, "user_name": user.full_name, "waste_category": entry.waste_category, "weight_kg": float(entry.weight_kg), "payout_amount": float(entry.payout_amount)})
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=receipt_{entry_id}.pdf"})