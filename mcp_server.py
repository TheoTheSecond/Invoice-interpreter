from mcp.server import MCPServer
from sqlmodel import Session, select
from database import engine
from models import Invoice


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

@mcp.tool()
def get_invoice(invoice_id: int) -> dict:
    """
    Get one invoice and its invoice lines.
    """
    pass


@mcp.tool()
def get_supplier_total(supplier: str) -> dict:
    """
    Get invoice count and total amount for a supplier.
    """
    pass


if __name__ == "__main__":
    mcp.run()