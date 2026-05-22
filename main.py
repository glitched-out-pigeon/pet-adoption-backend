from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import animals, upload, employees, adopters, applications, vet_records, intake_records
from routes import animals, upload, employees, adopters, applications, vet_records, intake_records, auth
from routes import animals, upload, employees, adopters, applications, vet_records, intake_records, auth, rehoming

app = FastAPI(title="Pet Adoption API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(animals.router,        prefix="/animals",        tags=["Animals"])
app.include_router(upload.router,         prefix="/upload",         tags=["Upload"])
app.include_router(employees.router,      prefix="/employees",      tags=["Employees"])
app.include_router(adopters.router,       prefix="/adopters",       tags=["Adopters"])
app.include_router(applications.router,   prefix="/applications",   tags=["Applications"])
app.include_router(vet_records.router,    prefix="/vet-records",    tags=["Vet Records"])
app.include_router(intake_records.router, prefix="/intake-records", tags=["Intake Records"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(rehoming.router, prefix="/rehoming", tags=["Rehoming"])

@app.get("/")
def root():
    return {"message": "Pet Adoption API is running 🐾"}