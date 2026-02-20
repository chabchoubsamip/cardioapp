from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime

app = FastAPI()

# Sert le fichier index.html
@app.get("/")
def home():
    return FileResponse("index.html")


# Base SQLite
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