from fastapi import FastAPI
from app.routers import auth, farms, readings, checkins, predictions, alerts, admin

app = FastAPI(title="Maize Stress Detection API", version="0.1.0")

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
