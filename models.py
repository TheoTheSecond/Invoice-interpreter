from sqlmodel import SQLModel, Field


class Invoice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    supplier: str | None = Field(default=None, index=True)
    supplier_id: str | None = Field(default=None, index=True)
    invoice_number: str | None = Field(default=None, index=True)
    invoice_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    raw_xml: str


class InvoiceLine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)
    line_number: str | None = None
    description: str | None = None
    seller_item_id: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    line_total: float | None = None
    vat_percent: float | None = None
