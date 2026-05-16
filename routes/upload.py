from fastapi import APIRouter, UploadFile, HTTPException
from supabase import create_client
from database import get_connection
import os

router = APIRouter()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@router.post("/{animal_id}")
async def upload_image(animal_id: str, file: UploadFile):
    contents = await file.read()
    path = f"{animal_id}/{file.filename}"

    # Upload to Supabase Storage
    supabase.storage.from_("animal-images").upload(path, contents, {
        "content-type": file.content_type
    })

    # Get the public URL
    url = supabase.storage.from_("animal-images").get_public_url(path)

    # Save URL to the database
    conn = await get_connection()
    row = await conn.fetchrow(
        "UPDATE animals SET image_url = $1 WHERE id = $2 RETURNING *",
        url, animal_id
    )
    await conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Animal not found")

    return {"image_url": url, "animal": dict(row)}