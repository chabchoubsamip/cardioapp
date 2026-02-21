from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import os, uuid
from reportlab.pdfgen import canvas

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")


# ===== ADMIN PAGE =====
@app.get("/admin", response_class=HTMLResponse)
def admin():
    files = [f for f in os.listdir(".") if f.endswith(".pdf")]
    files.sort(reverse=True)

    html = "<h1>Fiches PDF</h1>"
    if not files:
        html += "<p>Aucune fiche</p>"

    for f in files:
        html += f'<p><a href="/pdf/{f}">{f}</a></p>'

    return html


# ===== DOWNLOAD PDF =====
@app.get("/pdf/{filename}")
def pdf(filename: str):
    return FileResponse(filename, media_type="application/pdf")


class Fiche(BaseModel):
    administratif: dict
    motif_consultation: dict
    facteurs_risque: dict
    antecedents_cardio: dict
    traitement_ocr: str = ""
    consentement: dict


# ===== PDF GENERATION =====
def make_pdf(data, name):
    c = canvas.Canvas(name)
    y = 800

    c.drawString(50, y, "FICHE PATIENT")
    y -= 40

    c.drawString(50, y, f"Nom: {data['administratif']['nom']}")
    y -= 20
    c.drawString(50, y, f"Prenom: {data['administratif']['prenom']}")
    y -= 20

    c.drawString(50, y, "Facteurs:")
    y -= 20
    for k, v in data['facteurs_risque'].items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 15

    c.save()


# ===== SUBMIT =====
@app.post("/submit")
def submit(fiche: Fiche):
    data = fiche.dict()

    filename = f"fiche_{uuid.uuid4().hex}.pdf"
    make_pdf(data, filename)

    return {"ok": True}