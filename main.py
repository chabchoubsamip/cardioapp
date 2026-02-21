from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3, json
from datetime import datetime

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")

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
    traitement_ocr: str = ""
    consentement: dict


@app.post("/upload-ordo")
async def upload_ordo(file: UploadFile = File(...)):
    return {"traitement": "OCR désactivé sur serveur Render"}


@app.post("/submit")
def submit_fiche(fiche: Fiche):

    data = fiche.dict()

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO fiches (date, data) VALUES (?, ?)",
        (datetime.now().isoformat(), json.dumps(data))
    )
    conn.commit()
    conn.close()

    return {"status": "fiche enregistrée (Render OK)"}