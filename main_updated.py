from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from reportlab.pdfgen import canvas


# -------- App --------
app = FastAPI(title="CardioApp")

# Allow the frontend to be hosted elsewhere (Netlify / GitHub Pages, etc.)
# For production, replace ["*"] with your exact frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = BASE_DIR / "index.html"


# -------- Models --------
class Fiche(BaseModel):
    administratif: Dict[str, Any] = {}
    motif_consultation: Dict[str, Any] = {}
    facteurs_risque: Dict[str, Any] = {}
    antecedents_cardio: Dict[str, Any] = {}
    traitement_ocr: str = ""
    consentement: Dict[str, Any] = {}


# -------- Helpers --------
def _draw_multiline(c: canvas.Canvas, x: int, y: int, text: str, max_len: int = 95, line_h: int = 14) -> int:
    """Draw text with basic wrapping; returns new y."""
    if text is None:
        return y
    s = str(text).strip()
    if not s:
        return y

    # naive wrap
    words = s.split()
    line = ""
    for w in words:
        if len(line) + len(w) + 1 <= max_len:
            line = (line + " " + w).strip()
        else:
            c.drawString(x, y, line)
            y -= line_h
            line = w
    if line:
        c.drawString(x, y, line)
        y -= line_h
    return y


def make_pdf(data: Dict[str, Any], filename: str) -> Path:
    path = PDF_DIR / filename
    c = canvas.Canvas(str(path))
    y = 800

    c.setTitle("Fiche Patient")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "FICHE PATIENT")
    y -= 30

    c.setFont("Helvetica", 11)

    admin = data.get("administratif", {}) or {}
    nom = admin.get("nom", "")
    prenom = admin.get("prenom", "")
    c.drawString(50, y, f"Nom: {nom}")
    y -= 16
    c.drawString(50, y, f"Prénom: {prenom}")
    y -= 22

    def section(title: str, obj: Any):
        nonlocal y
        if y < 120:
            c.showPage()
            y = 800
            c.setFont("Helvetica", 11)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, title)
        y -= 18
        c.setFont("Helvetica", 11)

        if isinstance(obj, dict):
            if not obj:
                c.drawString(60, y, "-")
                y -= 16
                return
            for k, v in obj.items():
                if y < 120:
                    c.showPage()
                    y = 800
                    c.setFont("Helvetica", 11)
                y = _draw_multiline(c, 60, y, f"{k}: {v}")
        else:
            y = _draw_multiline(c, 60, y, str(obj))
        y -= 6

    section("Motif de consultation", data.get("motif_consultation", {}))
    section("Facteurs de risque", data.get("facteurs_risque", {}))
    section("Antécédents cardio", data.get("antecedents_cardio", {}))

    if data.get("traitement_ocr"):
        section("Traitement (OCR)", data.get("traitement_ocr", ""))

    section("Consentement", data.get("consentement", {}))

    c.save()
    return path


# -------- Routes --------
@app.get("/", response_class=HTMLResponse)
def home():
    if not INDEX_FILE.exists():
        return HTMLResponse("<h3>index.html introuvable sur le serveur.</h3>", status_code=500)
    return FileResponse(str(INDEX_FILE))


@app.get("/admin", response_class=HTMLResponse)
def admin():
    # Optional: protect with an admin key (set ADMIN_KEY in Render env vars).
    admin_key = os.getenv("ADMIN_KEY")
    # If you want to enforce it, uncomment these 2 lines:
    # if admin_key and request.query_params.get("key") != admin_key:
    #     raise HTTPException(status_code=401, detail="Unauthorized")

    files = sorted([p.name for p in PDF_DIR.glob("*.pdf")], reverse=True)

    html = "<h1>Fiches PDF</h1>"
    html += "<p>Liste des PDFs générés (du plus récent au plus ancien).</p>"
    if not files:
        html += "<p><i>Aucune fiche</i></p>"
        return html

    for f in files:
        html += f'<p><a href="/pdf/{f}" target="_blank" rel="noopener">{f}</a></p>'
    return html


@app.get("/pdf/{filename}")
def pdf(filename: str):
    path = PDF_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="PDF introuvable")
    return FileResponse(str(path), media_type="application/pdf", filename=filename)


@app.post("/submit")
def submit(fiche: Fiche):
    data = fiche.model_dump()

    filename = f"fiche_{uuid.uuid4().hex}.pdf"
    pdf_path = make_pdf(data, filename)

    return JSONResponse(
        {
            "ok": True,
            "filename": filename,
            "pdf_url": f"/pdf/{pdf_path.name}",
            "admin_url": "/admin",
        }
    )
