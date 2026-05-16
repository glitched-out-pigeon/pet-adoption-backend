from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter()

class IntakeRecordCreate(BaseModel):
    animal_id: str
    intake_type: str
    notes: Optional[str] = None
    received_by: Optional[str] = None

class IntakeRecordUpdate(BaseModel):
    animal_id: Optional[str] = None
    intake_type: Optional[str] = None
    notes: Optional[str] = None
    received_by: Optional[str] = None

@router.get("/")
async def get_intake_records():
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT intake_records.*,
               animals.name as animal_name,
               employees.name as employee_name
        FROM intake_records
        LEFT JOIN animals ON intake_records.animal_id = animals.id
        LEFT JOIN employees ON intake_records.received_by = employees.id
        ORDER BY intake_records.intake_date DESC
    """)
    await conn.close()
    return [dict(row) for row in rows]

@router.post("/")
async def add_intake_record(data: IntakeRecordCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        "INSERT INTO intake_records (animal_id, intake_type, notes, received_by) VALUES ($1, $2, $3, $4) RETURNING *",
        data.animal_id, data.intake_type, data.notes, data.received_by
    )
    await conn.close()
    return dict(row)

@router.patch("/{record_id}")
async def update_intake_record(record_id: str, data: IntakeRecordUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE intake_records SET
            animal_id = COALESCE($1, animal_id),
            intake_type = COALESCE($2, intake_type),
            notes = COALESCE($3, notes),
            received_by = COALESCE($4, received_by)
        WHERE id = $5 RETURNING *""",
        data.animal_id, data.intake_type,
        data.notes, data.received_by, record_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return dict(row)

@router.delete("/{record_id}")
async def delete_intake_record(record_id: str):
    conn = await get_connection()
    await conn.execute("DELETE FROM intake_records WHERE id = $1", record_id)
    await conn.close()
    return {"message": "Intake record deleted"}