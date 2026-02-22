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

# ==== SERVIR LE FORMULAIRE HTML ====
@app.get("/", response_class=HTMLResponse)
def home():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"error": "index.html introuvable"}

# ==== PDF ====
def make_pdf(data, filename):
    path = PDF_DIR / filename
    c = canvas.Canvas(str(path))
    y = 800

    def line(txt, space=16):
        nonlocal y
        c.drawString(40, y, txt)
        y -= space
        if y < 80:
            c.showPage()
            y = 800

    c.setFont("Helvetica-Bold", 14)
    line("DEMANDE DE CONSULTATION CARDIOLOGIQUE", 30)
    c.setFont("Helvetica", 11)

    admin = data["administratif"]
    line("1. DONNEES ADMINISTRATIVES")
    line(f"Date naissance : {admin.get('dob','')}")
    line(f"Sexe : {admin.get('sexe','')}")
    line(f"Tel : {admin.get('tel','')}")
    line(f"Email : {admin.get('mail','')}", 25)

    line("2. MOTIF")
    line(data["motif_consultation"].get("motif",""), 25)

    fr = data["facteurs_risque"]
    line("3. FACTEURS DE RISQUE")
    line(f"Tabac : {fr.get('tabac','')}")
    line(f"HTA : {fr.get('hta','')}")
    line(f"Diabete : {fr.get('diabete','')}")
    line(f"Cholesterol : {fr.get('cholesterol','')}", 25)

    at = data["antecedents_cardio"]
    line("4. ANTECEDENTS CARDIAQUES")
    line(f"Arythmie : {at.get('arythmie','')}")
    line(f"Infarctus : {at.get('infarctus','')}")
    line(f"IC : {at.get('insuffisance_cardiaque','')}")
    line(f"Valve : {at.get('valve','')}")
    line(f"Aorte : {at.get('aorte','')}")
    line(f"Chirurgie : {at.get('chirurgie','')}")
    line(f"MTEV : {at.get('mtev','')}", 25)

    line("5. TRAITEMENT")
    for t in data.get("traitement_ocr","").split("\n"):
        line(t)

    c.save()
    return path

# ==== GOOGLE DRIVE ====
def upload_to_drive(filepath):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        DRIVE_FOLDER_ID = "1ERp9e96G1CnQPjKg70jn4I8fCWh0rlcx"

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
            media_body=media,
            supportsAllDrives=True   # ← IMPORTANT
        ).execute()

        print("DRIVE OK")

    except Exception as e:
        print("DRIVE ERROR:", str(e))
        
# ==== ADMIN ====
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
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="application/pdf")

# ==== SUBMIT ====
@app.post("/submit")
def submit(fiche: Fiche):
    data = fiche.dict()
    filename = f"fiche_{uuid.uuid4().hex}.pdf"
    pdf_path = make_pdf(data, filename)
    upload_to_drive(pdf_path)
    return JSONResponse({"status": "ok"})
