from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3, json, smtplib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from email.message import EmailMessage
import os

app = FastAPI()

# -----------------------------
# CONFIG EMAIL
# -----------------------------
EMAIL_SENDER = "chabchoubsamip@gmail.com"
EMAIL_PASSWORD = "vvom aifo epkd yazs"
EMAIL_RECEIVER = "chabchoubsamip@gmail.com"

# -----------------------------
# SERVE INDEX
# -----------------------------
@app.get("/")
def home():
    return FileResponse("index.html")

# -----------------------------
# DB
# -----------------------------
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

# -----------------------------
# MODELE
# -----------------------------
class Fiche(BaseModel):
    administratif: dict
    motif_consultation: dict
    facteurs_risque: dict
    antecedents_cardio: dict
    traitement_ocr: str = ""
    consentement: dict

# -----------------------------
# GENERATION PDF
# -----------------------------
def generate_pdf(data):

    filename = "fiche.pdf"
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
        c.drawString(60, y, f"{k} : {v}")
        y -= 15

    c.save()
    return filename

# -----------------------------
# EMAIL
# -----------------------------
def send_email(pdf_path):

    msg = EmailMessage()
    msg["Subject"] = "Nouvelle fiche patient"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("Fiche en pièce jointe.")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename="fiche.pdf"
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

# -----------------------------
# SUBMIT
# -----------------------------
@app.post("/submit")
def submit_fiche(fiche: Fiche):

    data = fiche.dict()

    # Sauvegarde DB
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO fiches (date, data) VALUES (?, ?)",
        (datetime.now().isoformat(), json.dumps(data))
    )
    conn.commit()
    conn.close()

    # PDF
    pdf_file = generate_pdf(data)

    # Email
    send_email(pdf_file)

    return {"status": "fiche envoyée par email"}