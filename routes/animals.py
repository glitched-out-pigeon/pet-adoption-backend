from fastapi import APIRouter, HTTPException
from database import get_connection
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AnimalCreate(BaseModel):
    name: str
    species: str
    breed: str
    age: int
    description: str
    image_url: Optional[str] = None

class AnimalUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_adopted: Optional[bool] = None

# Get all animals
@router.get("/")
async def get_animals():
    conn = await get_connection()
    rows = await conn.fetch("SELECT * FROM animals ORDER BY created_at DESC")
    await conn.close()
    return [dict(row) for row in rows]

# Get a single animal by ID
@router.get("/{animal_id}")
async def get_animal(animal_id: str):
    conn = await get_connection()
    row = await conn.fetchrow("SELECT * FROM animals WHERE id = $1", animal_id)
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Animal not found")
    return dict(row)

# Add a new animal
@router.post("/")
async def add_animal(data: AnimalCreate):
    conn = await get_connection()
    row = await conn.fetchrow(
        "INSERT INTO animals (name, species, breed, age, description, image_url) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *",
        data.name, data.species, data.breed, data.age, data.description, data.image_url
    )
    await conn.close()
    return dict(row)

# General update for any animal field
@router.patch("/{animal_id}")
async def update_animal(animal_id: str, data: AnimalUpdate):
    conn = await get_connection()
    row = await conn.fetchrow(
        """UPDATE animals SET
            name = COALESCE($1, name),
            species = COALESCE($2, species),
            breed = COALESCE($3, breed),
            age = COALESCE($4, age),
            description = COALESCE($5, description),
            image_url = COALESCE($6, image_url),
            is_adopted = COALESCE($7, is_adopted)
        WHERE id = $8 RETURNING *""",
        data.name, data.species, data.breed, data.age,
        data.description, data.image_url, data.is_adopted, animal_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Animal not found")
    return dict(row)

# Mark an animal as adopted
@router.patch("/{animal_id}/adopt")
async def adopt_animal(animal_id: str):
    conn = await get_connection()
    row = await conn.fetchrow(
        "UPDATE animals SET is_adopted = TRUE WHERE id = $1 RETURNING *",
        animal_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Animal not found")
    return dict(row)

# Mark an animal as available again
@router.patch("/{animal_id}/unadopt")
async def unadopt_animal(animal_id: str):
    conn = await get_connection()
    row = await conn.fetchrow(
        "UPDATE animals SET is_adopted = FALSE WHERE id = $1 RETURNING *",
        animal_id
    )
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Animal not found")
    return dict(row)

# Delete an animal
@router.delete("/{animal_id}")
async def delete_animal(animal_id: str):
    conn = await get_connection()
    await conn.execute("DELETE FROM animals WHERE id = $1", animal_id)
    await conn.close()
    return {"message": "Animal deleted"}