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


@mcp.tool()
def get_invoice(invoice_id: int) -> dict:
    """
    Get one invoice and its invoice lines.
    """
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


@mcp.tool()
def get_invoice_summary() -> dict:
    """
    Get a summary of all invoices in the database.

    Use this tool for questions about the entire invoice collection,
    such as:
    - how many invoices there are
    - total spending
    - average invoice amount
    - the most expensive invoice
    - the cheapest invoice

    Do not use this tool when searching for a specific supplier,
    invoice number, product or service.
    """
    log_tool("get_invoice_summary()")

    with Session(engine) as session:
        invoices = session.exec(select(Invoice)).all()

        if not invoices:
            return {
                "invoice_count": 0,
                "total_amount": 0,
                "average_amount": 0,
                "most_expensive_invoice": None,
                "cheapest_invoice": None,
            }

        invoices_with_amount = [
            invoice
            for invoice in invoices
            if invoice.total_amount is not None
        ]

        total_amount = sum(
            invoice.total_amount
            for invoice in invoices_with_amount
        )

        average_amount = (
            total_amount / len(invoices_with_amount)
            if invoices_with_amount
            else 0
        )

        most_expensive = (
            max(
                invoices_with_amount,
                key=lambda invoice: invoice.total_amount
            )
            if invoices_with_amount
            else None
        )

        cheapest = (
            min(
                invoices_with_amount,
                key=lambda invoice: invoice.total_amount
            )
            if invoices_with_amount
            else None
        )

        return {
            "invoice_count": len(invoices),
            "total_amount": total_amount,
            "average_amount": average_amount,
            "most_expensive_invoice": {
                "id": most_expensive.id,
                "filename": most_expensive.filename,
                "invoice_number": most_expensive.invoice_number,
                "supplier": most_expensive.supplier,
                "total_amount": most_expensive.total_amount,
                "currency": most_expensive.currency,
            } if most_expensive else None,
            "cheapest_invoice": {
                "id": cheapest.id,
                "filename": cheapest.filename,
                "invoice_number": cheapest.invoice_number,
                "supplier": cheapest.supplier,
                "total_amount": cheapest.total_amount,
                "currency": cheapest.currency,
            } if cheapest else None,
        }

if __name__ == "__main__":
    mcp.run()


