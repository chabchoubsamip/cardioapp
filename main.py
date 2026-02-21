from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3, json, shutil, os, smtplib
from datetime import datetime
from PIL import Image
import pytesseract

# PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = FastAPI()

# =========================
# CONFIG EMAIL (GMAIL SMTP)
# =========================
EMAIL_SENDER = "chabchoubsamip@gmail.com"
EMAIL_PASSWORD = "aoer hzkh ffig bmuc"  # ⚠️ mot de passe application Gmail
EMAIL_RECEIVER = "chabchoubsamip@gmail.com"


# =========================
# SERVE INDEX.HTML
# =========================
@app.get("/")
def home():
    return FileResponse("index.html")


# =========================
# BASE SQLITE
# =========================
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


# =========================
# MODELE FICHE
# =========================
class Fiche(BaseModel):
    administratif: dict
    motif_consultation: dict
    facteurs_risque: dict
    antecedents_cardio: dict
    traitement_ocr: str = ""
    consentement: dict


# =========================
# UPLOAD ORDONNANCE + OCR
# =========================
@app.post("/upload-ordo")
async def upload_ordo(file: UploadFile = File(...)):

    path = "ordo.jpg"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = Image.open(path)
    texte = pytesseract.image_to_string(img, lang="fra")

    return {"traitement": texte}


# =========================
# GENERATION PDF
# =========================
def generate_pdf(data, filename="fiche.pdf"):

    c = canvas.Canvas(filename, pagesize=letter)
    y = 750

    c.setFont("Helvetica", 11)
    c.drawString(50, y, "FICHE PRE-CONSULTATION CARDIOLOGIQUE")
    y -= 40

    # ADMIN
    c.drawString(50, y, f"Nom : {data['administratif']['nom']}")
    y -= 20
    c.drawString(50, y, f"Prénom : {data['administratif']['prenom']}")
    y -= 20
    c.drawString(50, y, f"Date naissance : {data['administratif']['naissance']}")
    y -= 30

    # MOTIF
    c.drawString(50, y, f"Motif : {data['motif_consultation']['motif']}")
    y -= 30

    # TRAITEMENT OCR
    c.drawString(50, y, "Traitement détecté (OCR) :")
    y -= 20

    texte = data.get("traitement_ocr", "")
    for line in texte.split("\n"):
        c.drawString(60, y, line[:90])
        y -= 15
        if y < 100:
            c.showPage()
            y = 750

    c.save()
    return filename


# =========================
# ENVOI EMAIL + PDF
# =========================
def send_email_with_pdf(pdf_path):

    from email.message import EmailMessage

    msg = EmailMessage()
    msg["Subject"] = "Nouvelle fiche patient"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("Fiche patient en pièce jointe.")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="fiche.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)


# =========================
# SUBMIT FICHE COMPLETE
# =========================
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

    # Génère PDF
    pdf_file = generate_pdf(data)

    # Envoie mail
    send_email_with_pdf(pdf_file)

    return {"status": "fiche enregistrée + PDF envoyé"}