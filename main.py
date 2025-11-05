from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List

import io
import csv

# --------------------
# App & templating
# --------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --------------------
# Database (SQLite)
# --------------------
Base = declarative_base()

class Note(Base):
    __tablename__ = "note"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # created_at = Column(DateTime, default=datetime.now)

sqlite_file_name = "notes.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

# --------------------
# Routes: CRUD
# --------------------

@app.get("/")
def home(request: Request):
    with SessionLocal() as session:
        notes = session.query(Note).order_by(Note.id).all()

    # konversi created_at ke WIB untuk ditampilkan
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    notes_for_template = []
    for n in notes:
        created_local = None
        if getattr(n, "created_at", None):
            # jika stored datetime aware => astimezone, jika naive => asume UTC then convert
            dt = n.created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            created_local = dt.astimezone(jakarta_tz).strftime("%d %b %Y %H:%M")
        notes_for_template.append({
            "id": n.id,
            "content": n.content,
            "created_local": created_local
        })

    return templates.TemplateResponse("index.html", {"request": request, "notes": notes_for_template})


# @app.get("/")
# def home(request: Request):
#     with SessionLocal() as session:
#         notes: List[Note] = session.query(Note).order_by(Note.id).all()
#     return templates.TemplateResponse("index.html", {"request": request, "notes": notes})


@app.post("/add")
def add_note(content: str = Form(...)):
    with SessionLocal() as session:
        note = Note(content=content)
        session.add(note)
        session.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/edit/{note_id}")
def edit_note(note_id: int, content: str = Form(...)):
    with SessionLocal() as session:
        note = session.get(Note, note_id)
        if note:
            note.content = content
            session.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{note_id}")
def delete_note(note_id: int):
    with SessionLocal() as session:
        note = session.get(Note, note_id)
        if note:
            session.delete(note)
            session.commit()
    return RedirectResponse(url="/", status_code=303)


# --------------------
# Endpoint: download CSV (in-memory)
# --------------------
@app.get("/download_csv")
def download_csv():
    with SessionLocal() as session:
        notes = session.query(Note).order_by(Note.id).all()

    if not notes:
        return {"error": "Belum ada catatan untuk diunduh."}

    output = io.StringIO()
    # BOM supaya Excel di Windows membuka UTF-8 dengan benar
    output.write("\ufeff")
    writer = csv.writer(output)

    # Header
    writer.writerow(["id", "content", "created_at"])

    jakarta_tz = ZoneInfo("Asia/Jakarta")

    for n in notes:
        if getattr(n, "created_at", None):
            dt = n.created_at
            # pastikan aware dan konversi ke WIB
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_wib = dt.astimezone(jakarta_tz)
            created = dt_wib.strftime("%Y-%m-%d %H:%M:%S")
        else:
            created = ""

        writer.writerow([n.id, n.content, created])

    # for n in notes:
    #     created = n.created_at.isoformat(sep=" ", timespec="seconds") if getattr(n, "created_at", None) else ""
    #     writer.writerow([n.id, n.content, created])

    output.seek(0)

    filename = f"catatan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        output,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/dashboard")
def dashboard(request: Request):
    """Halaman utama dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/list")
def list_anggota(request: Request):
    """Halaman daftar semua anggota"""
    with SessionLocal() as session:
        notes = session.query(Note).order_by(Note.id).all()

    jakarta_tz = ZoneInfo("Asia/Jakarta")
    notes_for_template = []
    for n in notes:
        created_local = None
        if getattr(n, "created_at", None):
            dt = n.created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            created_local = dt.astimezone(jakarta_tz).strftime("%d %b %Y %H:%M")
        notes_for_template.append({
            "id": n.id,
            "content": n.content,
            "created_local": created_local
        })

    return templates.TemplateResponse("list.html", {"request": request, "notes": notes_for_template})






# from fastapi import FastAPI, Request, Form
# from fastapi.responses import RedirectResponse
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles

# from sqlalchemy import Column, Integer, String, DateTime, create_engine
# from sqlalchemy.orm import declarative_base, sessionmaker, Session
# from datetime import datetime
# from typing import List

# from fastapi.responses import FileResponse
# import os

# # =====================================================
# # 🚀 KONFIGURASI DASAR
# # =====================================================
# app = FastAPI()

# # Mount folder static (CSS, JS, gambar)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# templates = Jinja2Templates(directory="templates")

# # =====================================================
# # 🧩 DATABASE SETUP
# # =====================================================
# Base = declarative_base()

# class Note(Base):
#     __tablename__ = "note"

#     id = Column(Integer, primary_key=True, index=True)
#     content = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.now)  # ✅ otomatis isi waktu

# # Buat engine SQLite
# sqlite_file_name = "notes.db"
# sqlite_url = f"sqlite:///{sqlite_file_name}"
# engine = create_engine(sqlite_url, echo=True)

# # Session untuk interaksi database
# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# # Buat tabel jika belum ada
# Base.metadata.create_all(bind=engine)

# # =====================================================
# # 🌐 ROUTES
# # =====================================================

# @app.get("/")
# def home(request: Request):
#     with SessionLocal() as session:
#         notes: List[Note] = session.query(Note).all()
#     return templates.TemplateResponse("index.html", {"request": request, "notes": notes})


# @app.post("/add")
# def add_note(content: str = Form(...)):
#     with SessionLocal() as session:
#         note = Note(content=content)
#         session.add(note)
#         session.commit()
#     return RedirectResponse(url="/", status_code=303)


# @app.post("/edit/{note_id}")
# def edit_note(note_id: int, content: str = Form(...)):
#     with SessionLocal() as session:
#         note = session.get(Note, note_id)
#         if note:
#             note.content = content
#             session.commit()
#     return RedirectResponse(url="/", status_code=303)


# @app.post("/delete/{note_id}")
# def delete_note(note_id: int):
#     with SessionLocal() as session:
#         note = session.get(Note, note_id)
#         if note:
#             session.delete(note)
#             session.commit()
#     return RedirectResponse(url="/", status_code=303)

# from fastapi.responses import FileResponse
# import os
# from datetime import datetime

# # di bagian import atas file main.py
# import io
# import csv
# from fastapi.responses import StreamingResponse
# from datetime import datetime

# # -------------------------
# # Endpoint: download CSV
# # -------------------------
# @app.get("/download_csv")
# def download_csv():
#     # Ambil semua catatan dari DB
#     with SessionLocal() as session:
#         notes = session.query(Note).all()

#     if not notes:
#         return {"error": "Belum ada catatan untuk diunduh."}

#     # Tulis CSV ke memory (StringIO) supaya tidak perlu file fisik
#     output = io.StringIO()
#     # Tambahkan BOM UTF-8 agar Excel di Windows membuka encoding UTF-8 dengan benar
#     output.write("\ufeff")

#     writer = csv.writer(output)
#     # Header kolom
#     writer.writerow(["id", "content", "created_at"])

#     # Isi baris
#     for n in notes:
#         created = n.created_at.isoformat(sep=" ", timespec="seconds") if getattr(n, "created_at", None) else ""
#         writer.writerow([n.id, n.content, created])

#     # Reset posisi stream supaya bisa dibaca dari awal
#     output.seek(0)

#     # Nama file dengan timestamp
#     filename = f"catatan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

#     # StreamingResponse untuk mengirim CSV ke browser sebagai file download
#     return StreamingResponse(
#         output,
#         media_type="text/csv; charset=utf-8",
#         headers={
#             "Content-Disposition": f"attachment; filename={filename}"
#         }
#     )

# # @app.get("/download")
# # def download_notes():
# #     # Gunakan timestamp supaya file unik dan tidak bentrok
# #     date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# #     file_path = f"catatan_{date_str}.txt"

# #     with Session(engine) as session:
# #         notes = session.exec(select(Note)).all()

# #     # Cegah error jika tidak ada catatan
# #     if not notes:
# #         return {"error": "Belum ada catatan untuk diunduh."}

# #     # Tulis file secara aman
# #     try:
# #         with open(file_path, "w", encoding="utf-8") as f:
# #             f.write("📘 Catatan Saya\n")
# #             f.write("====================\n\n")
# #             for idx, note in enumerate(notes, start=1):
# #                 f.write(f"{idx}. {note.content}\n")
# #             f.write(f"\nTotal: {len(notes)} catatan.\n")

# #         # Pastikan file benar-benar ada sebelum dikirim
# #         if not os.path.exists(file_path):
# #             return {"error": "Gagal membuat file unduhan."}

# #         # Kirim file ke browser
# #         return FileResponse(
# #             path=file_path,
# #             filename="catatan_saya.txt",
# #             media_type="text/plain"
# #         )

# #     except Exception as e:
# #         # Tangani semua error internal dengan pesan aman
# #         return {"error": f"Terjadi kesalahan: {str(e)}"}

# # @app.get("/download")
# # def download_notes():
# #     date_str = datetime.now().strftime("%Y-%m-%d")
# #     file_path = f"catatan_{date_str}.txt"
# #     # file_path = "catatan_saya.txt"
# #     with Session(engine) as session:
# #         notes = session.exec(select(Note)).all()
# #         with open(file_path, "w", encoding="utf-8") as f:
# #             f.write("📘 Catatan Saya\n")
# #             f.write("====================\n\n")
# #             for idx, note in enumerate(notes, start=1):
# #                 f.write(f"{idx}. {note.content}\n")
# #             f.write("\nTotal: " + str(len(notes)) + " catatan.\n")

# #     # Pastikan file dikirim ke browser untuk diunduh
# #     return FileResponse(
# #         path=file_path,
# #         media_type="text/plain",
# #         filename="catatan_saya.txt"
# #     )

