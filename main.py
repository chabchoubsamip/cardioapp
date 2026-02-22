from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from reportlab.pdfgen import canvas
from pathlib import Path
import uuid

# ==== GOOGLE DRIVE ====
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DRIVE_FOLDER_ID = "1ERp9e96G1CnQPjKg70jn4I8fCWh0rlcx"

# ==== APP ====
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdfs"
PDF_DIR.mkdir(exist_ok=True)

# ==== MODEL ====
class Fiche(BaseModel):
    administratif: dict = {}
    motif_consultation: dict = {}
    facteurs_risque: dict = {}
    antecedents_cardio: dict = {}
    traitement_ocr: str = ""
    consentement: dict = {}

# ==== PDF GENERATION ====
def make_pdf(data, filename):
    path = PDF_DIR / filename
    c = canvas.Canvas(str(path))
    width, height = 595, 842  # A4
    y = height - 40

    def line(txt, space=16):
        nonlocal y
        c.drawString(40, y, txt)
        y -= space
        if y < 80:
            c.showPage()
            y = height - 40

    c.setFont("Helvetica-Bold", 16)
    line("DEMANDE DE CONSULTATION CARDIOLOGIQUE", 30)

    c.setFont("Helvetica", 12)

    # ADMIN
    line("1. DONNEES ADMINISTRATIVES", 20)
    admin = data["administratif"]
    line(f"Date de naissance : {admin.get('dob','')}")
    line(f"Sexe : {admin.get('sexe','')}")
    line(f"Telephone : {admin.get('tel','')}")
    line(f"Email : {admin.get('mail','')}", 25)

    # MOTIF
    line("2. MOTIF DE CONSULTATION", 20)
    line(f"Motif choisi : {data['motif_consultation'].get('motif','')}", 25)

    # FRCV
    line("3. FACTEURS DE RISQUE CARDIOVASCULAIRE", 20)
    fr = data["facteurs_risque"]
    line(f"Tabac : {fr.get('tabac','')}")
    line(f"HTA : {fr.get('hta','')}")
    line(f"Diabete : {fr.get('diabete','')}")
    line(f"Cholesterol : {fr.get('cholesterol','')}", 25)

    # ATCD
    line("4. ANTECEDENTS CARDIOVASCULAIRES", 20)
    at = data["antecedents_cardio"]
    line(f"Arythmie : {at.get('arythmie','')}")
    line(f"Infarctus / Stent / Pontage : {at.get('infarctus','')}")
    line(f"Insuffisance cardiaque : {at.get('insuffisance_cardiaque','')}")
    line(f"Probleme de valve : {at.get('valve','')}")
    line(f"Aorte dilatee : {at.get('aorte','')}")
    line(f"Chirurgie cardiaque ancienne : {at.get('chirurgie','')}")
    line(f"Maladie thrombo-embolique : {at.get('mtev','')}", 25)

    # TRAITEMENT
    line("5. TRAITEMENT ACTUEL", 20)
    traitement = data.get("traitement_ocr", "")
    for t in traitement.split("\n"):
        line(t)

    c.save()
    return path

# ==== GOOGLE DRIVE UPLOAD ====
def upload_to_drive(filepath):
    try:
        creds = service_account.Credentials.from_service_account_file(
            "/etc/secrets/service_account.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": filepath.name,
            "parents": [DRIVE_FOLDER_ID]
        }

        media = MediaFileUpload(str(filepath), mimetype="application/pdf")

        service.files().create(
            body=file_metadata,
            media_body=media
        ).execute()

        print("DRIVE OK")

    except Exception as e:
        print("DRIVE ERROR:", str(e))

# ==== ROUTES ====
@app.get("/")
def home():
    return {"message": "CardioApp API active"}

@app.get("/admin", response_class=HTMLResponse)
def admin():
    files = sorted([f.name for f in PDF_DIR.glob("*.pdf")], reverse=True)
    html = "<h2>PDF générés</h2>"
    for f in files:
        html += f'<p><a href="/pdf/{f}" target="_blank">{f}</a></p>'
    return html

@app.get("/pdf/{filename}")
def get_pdf(filename: str):
    path = PDF_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF introuvable")
    return FileResponse(path, media_type="application/pdf")

@app.post("/submit")
def submit(fiche: Fiche):
    data = fiche.dict()

    filename = f"fiche_{uuid.uuid4().hex}.pdf"
    pdf_path = make_pdf(data, filename)

    upload_to_drive(pdf_path)

    return JSONResponse({
        "status": "success",
        "filename": filename
    })