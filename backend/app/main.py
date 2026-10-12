import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, farms, readings, checkins, predictions, alerts, admin

app = FastAPI(title="Maize Stress Detection API", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:4173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(readings.router)
app.include_router(checkins.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Welcome to Maize Stress Detection Backend API"}
