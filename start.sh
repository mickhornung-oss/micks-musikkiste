#!/bin/bash
# Micks Musikkiste - Start Script (Linux/macOS)

echo ""
echo "====================================="
echo "  Micks Musikkiste - Start V2"
echo "====================================="
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "[!] Virtual Environment nicht gefunden"
    echo "[*] Erstelle .venv..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install requirements if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "[*] Installiere Requirements..."
    pip install -r backend/requirements.txt
fi

# Start backend
echo ""
echo "[*] Starte Backend-Server..."
echo "[*] Frontend: http://localhost:8000"
echo "[*] API Docs: http://localhost:8000/docs"
echo "[*] Hinweis: ENGINE_MODE=mock fuer lokalen V2-Flow empfohlen"
echo ""

python backend/run.py
