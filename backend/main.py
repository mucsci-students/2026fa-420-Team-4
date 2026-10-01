# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.controllers import config_controller, generator_controller

app = FastAPI(title="2026fa-420-Team-4 Academic Scheduler API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_controller.router)
app.include_router(generator_controller.router)

@app.get("/")
def root():
    return {"status": "online", "message": "Academic Scheduler API active"}