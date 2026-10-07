from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select
from dotenv import load_dotenv

from database import create_db, get_session
from models import Invoice, InvoiceLine
from xml_parser import parse_invoice
from ai_service import ask, startup, shutdown


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()

    try:
        yield
    finally:
        await shutdown()


app = FastAPI(
    title="Invoice AI v0.1",
    lifespan=lifespan
)

create_db()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return Path("templates/index.html").read_text(encoding="utf-8")


@app.post("/api/upload")
async def upload(
        files: list[UploadFile] = File(...),
        session: Session = Depends(get_session),
):
    added = []

    existing_filenames = set(
        session.exec(select(Invoice.filename)).all()
    )

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".xml"):
            continue

        filename = Path(file.filename).name

        if filename in existing_filenames:
            continue

        xml_text = (await file.read()).decode("utf-8-sig")

        try:
            data, lines = parse_invoice(xml_text)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Kunde inte läsa {filename}: {exc}",
            )

        invoice = Invoice(
            filename=filename,
            raw_xml=xml_text,
            **data,
        )

        session.add(invoice)
        session.commit()
        session.refresh(invoice)

        for line in lines:
            session.add(
                InvoiceLine(
                    invoice_id=invoice.id,
                    **line,
                )
            )

        session.commit()

        added.append(filename)
        existing_filenames.add(filename)

    return {"added": added}


@app.get("/api/invoices")
def invoices(
        q: str = "",
        session: Session = Depends(get_session),
):
    rows = session.exec(
        select(Invoice).order_by(Invoice.id.desc())
    ).all()

    query = q.lower().strip()

    if query:
        rows = [
            invoice
            for invoice in rows
            if query
               in " ".join(
                filter(
                    None,
                    [
                        invoice.filename,
                        invoice.supplier,
                        invoice.supplier_id,
                        invoice.invoice_number,
                    ],
                )
            ).lower()
        ]

    return [
        invoice.model_dump(exclude={"raw_xml"})
        for invoice in rows
    ]


@app.get("/api/invoices/{invoice_id}")
def invoice(
        invoice_id: int,
        session: Session = Depends(get_session),
):
    invoice = session.get(Invoice, invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Fakturan finns inte",
        )

    lines = session.exec(
        select(InvoiceLine)
        .where(InvoiceLine.invoice_id == invoice_id)
        .order_by(InvoiceLine.id)
    ).all()

    return {
        "invoice": invoice.model_dump(exclude={"raw_xml"}),
        "lines": [line.model_dump() for line in lines],
    }


@app.delete("/api/invoices")
def delete_all_invoices(
        session: Session = Depends(get_session)
):
    lines = session.exec(select(InvoiceLine)).all()

    for line in lines:
        session.delete(line)

    invoices = session.exec(select(Invoice)).all()

    for invoice in invoices:
        session.delete(invoice)

    session.commit()

    return {"message": "Databasen är tömd"}


class Question(BaseModel):
    question: str


@app.post("/api/ask")
async def ai(question: Question):
    return {
        "answer": await ask(question.question)
    }