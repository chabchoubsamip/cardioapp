from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Autorise la page HTML locale à parler au backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS fiches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        data TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

class Fiche(BaseModel):
    administratif: dict
    motif_consultation: dict
    facteurs_risque: dict
    antecedents_cardio: dict
    consentement: dict

@app.get("/")
def home():
    return {"message": "Backend OK"}

@app.post("/submit")
def submit_fiche(fiche: Fiche):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO fiches (date, data) VALUES (?, ?)",
        (datetime.now().isoformat(), json.dumps(fiche.dict()))
    )
    conn.commit()
    conn.close()
    return {"status": "fiche enregistrée"}

@app.get("/fiches")
def get_fiches():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM fiches ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows