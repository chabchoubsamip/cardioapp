from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3, json, uuid
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

def generate_pdf(data, filename):

    c = canvas.Canvas(filename, pagesize=letter)
    y = 750
    c.setFont("Helvetica", 11)

    c.drawString(50, y, "FICHE PRE-CONSULTATION CARDIOLOGIQUE")
    y -= 40

    c.drawString(50, y, f"Nom : {data['administratif']['nom']}")
    y -= 20
    c.drawString(50, y, f"Prénom : {data['administratif']['prenom']}")
    y -= 20
    c.drawString(50, y, f"Date naissance : {data['administratif']['naissance']}")
    y -= 30

    c.drawString(50, y, f"Motif : {data['motif_consultation']['motif']}")
    y -= 30

    c.drawString(50, y, "Facteurs de risque :")
    y -= 20

    for k, v in data['facteurs_risque'].items():
        c.drawString(50, y, f"{k} : {v}")
        y -= 15

    y -= 20
    c.drawString(50, y, "Antécédents cardiovasculaires :")
    y -= 20

    for k, v in data['antecedents_cardio'].items():
        c.drawString(50, y, f"{k} : {v}")
        y -= 15

    c.save()

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

    pdf_name = f"fiche_{uuid.uuid4().hex}.pdf"
    generate_pdf(data, pdf_name)

    return FileResponse(pdf_name, media_type="application/pdf", filename="fiche.pdf")