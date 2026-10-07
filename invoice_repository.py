from sqlalchemy import text

from database import engine


def search_invoices(query: str) -> list[dict]:
    sql = text("""
               SELECT
                   id,
                   filename,
                   supplier,
                   invoice_number,
                   total_amount
               FROM invoice
               WHERE LOWER(filename) LIKE LOWER(:query)
                  OR LOWER(supplier) LIKE LOWER(:query)
                  OR LOWER(invoice_number) LIKE LOWER(:query)
               ORDER BY id DESC
               """)

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"query": f"%{query}%"}
        ).mappings().all()

        return [dict(row) for row in rows]


def get_invoice(invoice_id: int) -> dict:
    invoice_sql = text("""
                       SELECT
                           id,
                           filename,
                           supplier,
                           supplier_id,
                           invoice_number,
                           invoice_date,
                           due_date,
                           currency,
                           subtotal,
                           tax_amount,
                           total_amount
                       FROM invoice
                       WHERE id = :invoice_id
                       """)

    lines_sql = text("""
                     SELECT
                         id,
                         invoice_id,
                         line_number,
                         description,
                         seller_item_id,
                         quantity,
                         unit,
                         unit_price,
                         line_total,
                         vat_percent
                     FROM invoiceline
                     WHERE invoice_id = :invoice_id
                     ORDER BY id
                     """)

    with engine.connect() as connection:
        invoice = connection.execute(
            invoice_sql,
            {"invoice_id": invoice_id}
        ).mappings().first()

        if invoice is None:
            return {"error": "Invoice not found"}

        lines = connection.execute(
            lines_sql,
            {"invoice_id": invoice_id}
        ).mappings().all()

        return {
            "invoice": dict(invoice),
            "lines": [dict(line) for line in lines],
        }


def get_supplier_total(supplier: str) -> dict:
    sql = text("""
               SELECT
                   COUNT(id) AS invoice_count,
                   COALESCE(SUM(total_amount), 0) AS total_amount
               FROM invoice
               WHERE LOWER(supplier) LIKE LOWER(:supplier)
               """)

    with engine.connect() as connection:
        result = connection.execute(
            sql,
            {"supplier": f"%{supplier}%"}
        ).mappings().one()

        return {
            "supplier": supplier,
            "invoice_count": result["invoice_count"],
            "total_amount": result["total_amount"],
        }


def search_invoice_lines(query: str) -> list[dict]:
    sql = text("""
               SELECT
                   l.invoice_id,
                   i.invoice_number,
                   i.supplier,
                   l.description,
                   l.seller_item_id,
                   l.quantity,
                   l.unit,
                   l.unit_price,
                   l.line_total
               FROM invoiceline AS l
                        JOIN invoice AS i
                             ON l.invoice_id = i.id
               WHERE LOWER(l.description) LIKE LOWER(:query)
                  OR LOWER(l.seller_item_id) LIKE LOWER(:query)
               ORDER BY l.invoice_id, l.id
               """)

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"query": f"%{query}%"}
        ).mappings().all()

        return [dict(row) for row in rows]

def get_invoice_statistics() -> dict:
    sql = text("""
               SELECT
                   COUNT(id) AS invoice_count,
                   COALESCE(SUM(total_amount), 0) AS total_amount,
                   COALESCE(AVG(total_amount), 0) AS average_amount
               FROM invoice
               """)

    with engine.connect() as connection:
        result = connection.execute(sql).mappings().one()

        return dict(result)


def get_most_expensive_invoice() -> dict | None:
    sql = text("""
               SELECT
                   id,
                   filename,
                   invoice_number,
                   supplier,
                   total_amount,
                   currency
               FROM invoice
               WHERE total_amount IS NOT NULL
               ORDER BY total_amount DESC
               LIMIT 1
               """)

    with engine.connect() as connection:
        result = connection.execute(sql).mappings().first()

        return dict(result) if result else None


def get_cheapest_invoice() -> dict | None:
    sql = text("""
               SELECT
                   id,
                   filename,
                   invoice_number,
                   supplier,
                   total_amount,
                   currency
               FROM invoice
               WHERE total_amount IS NOT NULL
               ORDER BY total_amount ASC
               LIMIT 1
               """)

    with engine.connect() as connection:
        result = connection.execute(sql).mappings().first()

        return dict(result) if result else None