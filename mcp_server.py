from datetime import datetime

from mcp.server import MCPServer

import invoice_repository as repository


mcp = MCPServer("Invoice database")


def log_tool(message: str):
    with open("mcp_debug.log", "a", encoding="utf-8") as file:
        file.write(f"{datetime.now()} - {message}\n")


@mcp.tool()
def search_invoices(query: str) -> list[dict]:
    """
    Search invoice HEADER information only.

    Searches:
    - filename
    - supplier name
    - invoice number

    Do not use this tool to search for products, services,
    purchases, article numbers or invoice line descriptions.
    Use search_invoice_lines for those searches.
    """
    log_tool(f"search_invoices(query={query})")

    return repository.search_invoices(query)


@mcp.tool()
def get_invoice(invoice_id: int) -> dict:
    """
    Get one invoice and all of its invoice lines.

    Use this tool when the invoice ID is known and detailed
    information about that invoice is needed.
    """
    log_tool(f"get_invoice(invoice_id={invoice_id})")

    return repository.find_invoice_by_number(invoice_id)


@mcp.tool()
def get_supplier_total(supplier: str) -> dict:
    """
    Get the number of invoices and total spending for a supplier.

    Use this tool for questions about how many invoices there are
    from a supplier or how much has been spent with that supplier.
    """
    log_tool(f"get_supplier_total(supplier={supplier})")

    return repository.get_supplier_total(supplier)


@mcp.tool()
def search_invoice_lines(query: str) -> list[dict]:
    """
    Search the CONTENTS of invoices.

    Use this tool to search for products, services, purchases,
    article numbers and invoice line descriptions.

    Use this when the user asks which invoices contain a
    particular product or service.
    """
    log_tool(f"search_invoice_lines(query={query})")

    return repository.search_invoice_lines(query)

@mcp.tool()
def get_invoice_summary() -> dict:
    """
    Get a summary of all invoices in the database.

    Use this tool for questions about the entire invoice collection,
    such as:
    - how many invoices there are in total
    - total spending across all invoices
    - average invoice amount
    - the most expensive invoice
    - the cheapest invoice

    Do not use this tool when searching for a specific supplier,
    invoice number, product or service.
    """
    log_tool("get_invoice_summary()")

    return repository.invoice_summary()

@mcp.tool()
def get_invoice_statistics() -> dict:
    """
    Get statistics about all invoices, including invoice count,
    total spending and average invoice amount.
    """
    log_tool("get_invoice_statistics()")

    return repository.get_invoice_statistics()


@mcp.tool()
def get_most_expensive_invoice() -> dict | None:
    """
    Get the invoice with the highest total amount.
    """
    log_tool("get_most_expensive_invoice()")

    return repository.analyze_invoices("highest_total")


@mcp.tool()
def get_cheapest_invoice() -> dict | None:
    """
    Get the invoice with the lowest total amount.
    """
    log_tool("get_cheapest_invoice()")

    return repository.analyze_invoices("lowest_total")
if __name__ == "__main__":
    mcp.run()