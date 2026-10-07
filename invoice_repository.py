from datetime import datetime
from typing import Literal

from mcp.server import MCPServer
from sqlmodel import Session, select

from database import engine
from models import Invoice, InvoiceLine


def log_tool(message: str) -> None:
    with open("mcp_debug.log", "a", encoding="utf-8") as file:
        file.write(f"{datetime.now()} - {message}\n")


def invoice_summary(invoice: Invoice) -> dict:
    return {
        "id": invoice.id,
        "filename": invoice.filename,
        "supplier": invoice.supplier,
        "supplier_id": invoice.supplier_id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "currency": invoice.currency,
        "subtotal": invoice.subtotal,
        "tax_amount": invoice.tax_amount,
        "total_amount": invoice.total_amount,
    }


mcp = MCPServer("Invoice database")


def search_invoices(query: str, limit: int = 10000) -> list[dict]:
    log_tool(f"search_invoices(query={query!r}, limit={limit})")
    query = query.strip()
    if not query or query == "*":
        raise ValueError(
            "query must contain a search term; use analyze_invoices for "
            "comparisons across all invoices"
        )

    limit = max(1, min(limit, 100))
    pattern = f"%{query.lower()}%"

    with Session(engine) as session:
        statement = (
            select(Invoice)
            .where(
                (Invoice.filename.ilike(pattern))
                | (Invoice.supplier.ilike(pattern))
                | (Invoice.supplier_id.ilike(pattern))
                | (Invoice.invoice_number.ilike(pattern))
            )
            .order_by(Invoice.id.desc())
            .limit(limit)
        )
        return [
            invoice_summary(invoice)
            for invoice in session.exec(statement)
        ]


def find_invoice_by_number(invoice_number: str) -> dict:
    log_tool(f"find_invoice_by_number(invoice_number={invoice_number!r})")
    invoice_number = invoice_number.strip()
    if not invoice_number:
        raise ValueError("invoice_number must not be empty")

    with Session(engine) as session:
        statement = select(Invoice).where(
            Invoice.invoice_number == invoice_number
        )
        invoice = session.exec(statement).first()
        if not invoice:
            return {"error": "Invoice not found", "invoice_number": invoice_number}
        return invoice_summary(invoice)


def get_invoice(invoice_id: int) -> dict:
    log_tool(f"get_invoice(invoice_id={invoice_id})")
    with Session(engine) as session:
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            return {"error": "Invoice not found", "invoice_id": invoice_id}

        lines = session.exec(
            select(InvoiceLine)
            .where(InvoiceLine.invoice_id == invoice_id)
            .order_by(InvoiceLine.id)
        ).all()

        return {
            "invoice": invoice_summary(invoice),
            "lines": [line.model_dump() for line in lines],
        }


def analyze_invoices(
    operation: Literal[
        "highest_total",
        "lowest_total",
        "earliest_date",
        "latest_date",
        "count",
        "total_amount",
    ],
    supplier: str | None = None,
) -> dict:
    log_tool(f"analyze_invoices(operation={operation!r}, supplier={supplier!r})")
    supplier = supplier.strip() if supplier else None

    with Session(engine) as session:
        statement = select(Invoice)
        if supplier:
            statement = statement.where(Invoice.supplier.ilike(f"%{supplier}%"))

        if operation == "count":
            invoices = session.exec(statement).all()
            return {"operation": operation, "supplier": supplier, "count": len(invoices)}

        if operation == "total_amount":
            invoices = session.exec(statement).all()
            total = sum(invoice.total_amount or 0 for invoice in invoices)
            return {
                "operation": operation,
                "supplier": supplier,
                "total_amount": total,
                "currency": invoices[0].currency if invoices else None,
            }

        date_field = (
            Invoice.invoice_date
            if operation in {"earliest_date", "latest_date"}
            else Invoice.total_amount
        )
        statement = statement.where(date_field.is_not(None))
        descending = operation in {"highest_total", "latest_date"}
        statement = statement.order_by(
            date_field.desc() if descending else date_field.asc()
        ).limit(1)
        invoice = session.exec(statement).first()

        return {
            "operation": operation,
            "supplier": supplier,
            "invoice": invoice_summary(invoice) if invoice else None,
        }


def get_invoice_statistics() -> dict:
    log_tool("get_invoice_statistics()")

    with Session(engine) as session:
        invoices = session.exec(select(Invoice)).all()
        amounts = [
            invoice.total_amount
            for invoice in invoices
            if invoice.total_amount is not None
        ]

        return {
            "invoice_count": len(invoices),
            "total_amount": sum(amounts, 0),
            "average_amount": sum(amounts, 0) / len(amounts)
            if amounts
            else 0,
        }


def get_supplier_total(supplier: str) -> dict:
    log_tool(f"get_supplier_total(supplier={supplier!r})")
    supplier = supplier.strip()
    if not supplier:
        raise ValueError("supplier must not be empty")

    with Session(engine) as session:
        statement = select(Invoice).where(Invoice.supplier.ilike(f"%{supplier}%"))
        invoices = session.exec(statement).all()
        return {
            "supplier": supplier,
            "invoice_count": len(invoices),
            "total_amount": sum(invoice.total_amount or 0 for invoice in invoices),
            "currency": invoices[0].currency if invoices else None,
        }


def search_invoice_lines(query: str, limit: int = 50) -> list[dict]:
    log_tool(f"search_invoice_lines(query={query!r}, limit={limit})")
    query = query.strip()
    if not query or query == "*":
        raise ValueError("query must contain a line-item search term")

    limit = max(1, min(limit, 100))
    pattern = f"%{query.lower()}%"

    with Session(engine) as session:
        statement = (
            select(InvoiceLine, Invoice)
            .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
            .where(
                (InvoiceLine.description.ilike(pattern))
                | (InvoiceLine.seller_item_id.ilike(pattern))
            )
            .order_by(InvoiceLine.id)
            .limit(limit)
        )
        return [
            {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "supplier": invoice.supplier,
                "description": line.description,
                "seller_item_id": line.seller_item_id,
                "quantity": line.quantity,
                "unit": line.unit,
                "unit_price": line.unit_price,
                "line_total": line.line_total,
            }
            for line, invoice in session.exec(statement)
        ]


if __name__ == "__main__":
    mcp.run()
