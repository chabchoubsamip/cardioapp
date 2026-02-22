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
    y = 800

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "FICHE PATIENT")
    y -= 30
    c.setFont("Helvetica", 11)

    for section, content in data.items():
        c.drawString(50, y, f"{section.upper()}")
        y -= 20

        if isinstance(content, dict):
            for k, v in content.items():
                c.drawString(60, y, f"{k}: {v}")
                y -= 15
        else:
            c.drawString(60, y, str(content))
            y -= 15

        y -= 10

        if y < 100:
            c.showPage()
            y = 800

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

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        print("UPLOAD DRIVE OK:", file.get("id"))

    except Exception as e:
        print("ERREUR UPLOAD DRIVE >>>", str(e))

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

    # Upload automatique vers Google Drive
    upload_to_drive(pdf_path)

    return JSONResponse({
        "status": "success",
        "filename": filename
    })