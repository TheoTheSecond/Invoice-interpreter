import sys

from mcp.server import MCPServer
from sqlmodel import Session, select

from database import engine
from models import Invoice, InvoiceLine

from datetime import datetime

def log_tool(message: str):
    with open("mcp_debug.log", "a", encoding="utf-8") as file:
        file.write(
            f"{datetime.now()} - {message}\n"
        )

mcp = MCPServer("Invoice database")





@mcp.tool()
def search_invoices(query: str) -> list[dict]:
    """
    Search invoice HEADER information only.
    """
    log_tool(
        f"search_invoices(query={query})"
    )
    q = query.lower()

    with Session(engine) as session:
        invoices = session.exec(select(Invoice)).all()

        matches = []

        for invoice in invoices:
            searchable_text = " ".join(
                filter(
                    None,
                    [
                        invoice.filename,
                        invoice.supplier,
                        invoice.invoice_number
                    ]
                )
            ).lower()

            if q in searchable_text:
                matches.append({
                    "id": invoice.id,
                    "filename": invoice.filename,
                    "supplier": invoice.supplier,
                    "invoice_number": invoice.invoice_number,
                    "total_amount": invoice.total_amount
                })

        return matches

    """
    Get one invoice and its invoice lines.
    """
@mcp.tool()
def get_invoice(invoice_id: int) -> dict:
    log_tool(
        f"get_invoice(invoice_id={invoice_id})"
    )
    with Session(engine) as session:
        invoice = session.get(Invoice, invoice_id)

        if not invoice:
            return {
                "error": "Invoice not found"
            }

        lines = session.exec(
            select(InvoiceLine)
            .where(InvoiceLine.invoice_id == invoice_id)
            .order_by(InvoiceLine.id)
        ).all()

        return {
            "invoice": invoice.model_dump(exclude={"raw_xml"}),
            "lines": [
                line.model_dump()
                for line in lines
            ]
        }

    """
    Get invoice count and total amount for a supplier.
    """
@mcp.tool()
def get_supplier_total(supplier: str) -> dict:
    log_tool(
        f"get_supplier_total(supplier={supplier})"
    )
    with Session(engine) as session:
        invoices = session.exec(
            select(Invoice)
        ).all()

        matches = [
            invoice
            for invoice in invoices
            if invoice.supplier
               and supplier.lower() in invoice.supplier.lower()
        ]

        return {
            "supplier": supplier,
            "invoice_count": len(matches),
            "total_amount": sum(
                invoice.total_amount or 0
                for invoice in matches
            )
        }

@mcp.tool()
def search_invoice_lines(query: str) -> list[dict]:
    """
   Search the CONTENTS of invoices.
   """
    log_tool(
        f"search_invoice_lines(query={query})"
    )

    q = query.lower()

    with Session(engine) as session:
        lines = session.exec(
            select(InvoiceLine)
        ).all()

        matches = []

        for line in lines:
            searchable_text = " ".join(
                filter(
                    None,
                    [
                        line.description,
                        line.seller_item_id
                    ]
                )
            ).lower()

            if q in searchable_text:
                invoice = session.get(
                    Invoice,
                    line.invoice_id
                )

                matches.append({
                    "invoice_id": line.invoice_id,
                    "invoice_number": (
                        invoice.invoice_number
                        if invoice else None
                    ),
                    "supplier": (
                        invoice.supplier
                        if invoice else None
                    ),
                    "description": line.description,
                    "seller_item_id": line.seller_item_id,
                    "quantity": line.quantity,
                    "unit": line.unit,
                    "unit_price": line.unit_price,
                    "line_total": line.line_total
                })

        return matches


if __name__ == "__main__":
    mcp.run()


