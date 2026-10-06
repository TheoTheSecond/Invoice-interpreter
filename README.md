# Invoice AI v0.1

Minimal prototyp: XML -> SQLite -> sökning/lista -> AI-frågor. Samma databasoperationer exponeras också som MCP-tools.

## Starta

Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Lägg din OpenAI API-nyckel i `.env`. Starta sedan:

```bash
uvicorn main:app --reload
```

Öppna http://127.0.0.1:8000

## MCP

MCP-servern ligger i `mcp_server.py` och har tre tools:
- `search_invoices`
- `get_invoice`
- `get_supplier_total`

Testa den separat med MCP CLI/Inspector enligt MCP SDK-dokumentationen.

## Viktig begränsning i v0.1

XML-standarder varierar kraftigt. `xml_parser.py` använder avsiktligt en enkel, namespace-tolerant parser och ett fåtal vanliga fältnamn. När vi har dina faktiska XML-filer anpassar vi parsern till just deras format.

Webbchatten använder OpenAI function calling mot samma databasfunktioner. MCP-servern exponerar samma funktionalitet externt. Nästa version kan låta AI-orchestreringen gå direkt genom MCP-klienten också.
