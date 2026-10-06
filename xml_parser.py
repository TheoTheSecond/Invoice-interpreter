import xml.etree.ElementTree as ET


NS = {
    "inv": "urn:sfti:documents:BasicInvoice:1:0",
    "cac": "urn:sfti:CommonAggregateComponents:1:0",
    "cbc": "urn:oasis:names:tc:ubl:CommonBasicComponents:1:0",
}


def text(element, path):
    found = element.find(path, NS)
    if found is not None and found.text:
        return found.text.strip()
    return None


def number(value):
    if value is None:
        return None
    try:
        return float(value.replace(" ", "").replace(",", "."))
    except (ValueError, AttributeError):
        return None


def parse_invoice(xml_text: str):
    root = ET.fromstring(xml_text)

    invoice = root.find("inv:Invoice", NS)
    if invoice is None and root.tag == f"{{{NS['inv']}}}Invoice":
        invoice = root

    if invoice is None:
        raise ValueError("Kunde inte hitta en SFTI BasicInvoice i XML-filen.")

    supplier_party = invoice.find("cac:SellerParty/cac:Party", NS)
    legal_total = invoice.find("cac:LegalTotal", NS)
    tax_total = invoice.find("cac:TaxTotal", NS)
    payment_means = invoice.find("cac:PaymentMeans", NS)

    data = {
        "supplier": (
            text(supplier_party, "cac:PartyName/cbc:Name")
            if supplier_party is not None else None
        ),
        "supplier_id": (
            text(supplier_party, "cac:PartyIdentification/cac:ID")
            if supplier_party is not None else None
        ),
        "invoice_number": text(invoice, "inv:ID"),
        "invoice_date": text(invoice, "cbc:IssueDate"),
        "due_date": (
            text(payment_means, "cbc:DuePaymentDate")
            if payment_means is not None else None
        ),
        "currency": text(invoice, "inv:InvoiceCurrencyCode"),
        "subtotal": (
            number(text(legal_total, "cbc:TaxExclusiveTotalAmount"))
            if legal_total is not None else None
        ),
        "tax_amount": (
            number(text(tax_total, "cbc:TotalTaxAmount"))
            if tax_total is not None else None
        ),
        "total_amount": (
            number(text(legal_total, "cbc:TaxInclusiveTotalAmount"))
            if legal_total is not None else None
        ),
    }

    lines = []

    for line in invoice.findall("cac:InvoiceLine", NS):
        quantity_element = line.find("cbc:InvoicedQuantity", NS)

        lines.append({
            "line_number": text(line, "cac:ID"),
            "description": text(line, "cac:Item/cbc:Description"),
            "seller_item_id": text(
                line,
                "cac:Item/cac:SellersItemIdentification/cac:ID"
            ),
            "quantity": number(text(line, "cbc:InvoicedQuantity")),
            "unit": (
                quantity_element.get("quantityUnitCode")
                if quantity_element is not None else None
            ),
            "unit_price": number(
                text(line, "cac:Item/cac:BasePrice/cbc:PriceAmount")
            ),
            "line_total": number(text(line, "cbc:LineExtensionAmount")),
            "vat_percent": number(
                text(line, "cac:Item/cac:TaxCategory/cbc:Percent")
            ),
        })

    return data, lines
