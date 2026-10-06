from mcp.server import MCPServer
from sqlmodel import Session, select

from database import engine
from models import Invoice, InvoiceLine


mcp = MCPServer("Invoice database")

"""
Search invoices by filename, supplier or invoice number.
"""
@mcp.tool()
def search_invoices(query: str) -> list[dict]:

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


if __name__ == "__main__":
    mcp.run()