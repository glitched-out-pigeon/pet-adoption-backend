from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter()

class RehomingCreate(BaseModel):
    owner_name: str
    owner_email: str
    owner_phone: Optional[str] = None
    animal_name: str
    species: str
    breed: Optional[str] = None
    age: Optional[int] = None
    description: Optional[str] = None
    reason_for_rehoming: Optional[str] = None
    image_url: Optional[str] = None

class RehomingUpdate(BaseModel):
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    animal_name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    description: Optional[str] = None
    reason_for_rehoming: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[str] = None

# Get all rehoming applications
@router.get("/")
async def get_rehoming_applications():
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT rehoming_applications.*,
               employees.name as reviewer_name
        FROM rehoming_applications
        LEFT JOIN employees ON rehoming_applications.reviewed_by = employees.id
        ORDER BY rehoming_applications.submitted_at DESC
    """)
    await conn.close()
    return [dict(row) for row in rows]

# Submit a new rehoming application
@router.post("/")
async def submit_rehoming_application(data: RehomingCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """INSERT INTO rehoming_applications
           (owner_name, owner_email, owner_phone, animal_name, species, breed,
            age, description, reason_for_rehoming, image_url)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING *""",
        data.owner_name, data.owner_email, data.owner_phone,
        data.animal_name, data.species, data.breed, data.age,
        data.description, data.reason_for_rehoming, data.image_url
    )
    await conn.close()
    return dict(row)

# Update a rehoming application
@router.patch("/{application_id}")
async def update_rehoming_application(application_id: str, data: RehomingUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE rehoming_applications SET
            owner_name = COALESCE($1, owner_name),
            owner_email = COALESCE($2, owner_email),
            owner_phone = COALESCE($3, owner_phone),
            animal_name = COALESCE($4, animal_name),
            species = COALESCE($5, species),
            breed = COALESCE($6, breed),
            age = COALESCE($7, age),
            description = COALESCE($8, description),
            reason_for_rehoming = COALESCE($9, reason_for_rehoming),
            image_url = COALESCE($10, image_url),
            status = COALESCE($11, status),
            reviewed_by = COALESCE($12, reviewed_by)
        WHERE id = $13 RETURNING *""",
        data.owner_name, data.owner_email, data.owner_phone,
        data.animal_name, data.species, data.breed, data.age,
        data.description, data.reason_for_rehoming, data.image_url,
        data.status, data.reviewed_by, application_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)

# Approve a rehoming application — moves animal to animals table
@router.patch("/{application_id}/approve")
async def approve_rehoming_application(application_id: str):
    conn = await get_connection()

    rehoming = await conn.fetchrow(
        "SELECT * FROM rehoming_applications WHERE id = $1", application_id
    )

    if not rehoming:
        await conn.close()
        raise HTTPException(status_code=404, detail="Application not found")

    if rehoming["status"] == "approved":
        await conn.close()
        raise HTTPException(status_code=400, detail="Already approved")

    # Insert into animals table
    animal = await conn.fetchrow(
        """INSERT INTO animals (name, species, breed, age, description, image_url, is_adopted)
           VALUES ($1, $2, $3, $4, $5, $6, FALSE) RETURNING *""",
        rehoming["animal_name"],
        rehoming["species"],
        rehoming["breed"],
        rehoming["age"],
        rehoming["description"],
        rehoming["image_url"]
    )

    # Create an intake record for traceability
    await conn.execute(
        """INSERT INTO intake_records (animal_id, intake_type, notes)
           VALUES ($1, 'surrendered', $2)""",
        animal["id"],
        f"Rehomed by {rehoming['owner_name']} ({rehoming['owner_email']}). Reason: {rehoming['reason_for_rehoming'] or 'Not specified'}"
    )

    # Mark rehoming application as approved
    await conn.execute(
        "UPDATE rehoming_applications SET status = 'approved' WHERE id = $1",
        application_id
    )

    await conn.close()
    return {
        "message": "Animal approved and added to shelter",
        "animal": dict(animal)
    }

# Reject a rehoming application
@router.patch("/{application_id}/reject")
async def reject_rehoming_application(application_id: str):
    conn = await get_connection()
    row = await conn.fetchrow(
        "UPDATE rehoming_applications SET status = 'rejected' WHERE id = $1 RETURNING *",
        application_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application rejected", "application": dict(row)}

# Delete a rehoming application
@router.delete("/{application_id}")
async def delete_rehoming_application(application_id: str):
    conn = await get_connection()
    await conn.execute(
        "DELETE FROM rehoming_applications WHERE id = $1", application_id
    )
    await conn.close()
    return {"message": "Application deleted"}