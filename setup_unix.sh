#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  Hermes Translate — macOS / Linux Setup
#  Run once after cloning. Re-run quarterly to update language packs.
# ─────────────────────────────────────────────────────────────────

set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo " Hermes Translate — Setup"
echo " ═══════════════════════"
echo ""

if ! command -v python3 &>/dev/null; then
    echo " [ERROR] Python 3 not found."
    echo "         macOS:  brew install python"
    echo "         Debian: sudo apt install python3 python3-pip"
    exit 1
fi

echo " [1/3] Installing Python dependencies..."
pip3 install -r "$DIR/requirements.txt"
echo ""

echo " [2/3] Downloading language packs (~1-2 GB total)..."
python3 - <<'PYEOF'
import argostranslate.package as pkg

PAIRS = [
    ("en","fr"),("fr","en"),
    ("en","de"),("de","en"),
    ("en","tr"),("tr","en"),
    ("fr","de"),("de","fr"),
]

print("  Fetching package index...")
pkg.update_package_index()
available = pkg.get_available_packages()
installed = {(p.from_code, p.to_code) for p in pkg.get_installed_packages()}

for fc, tc in PAIRS:
    if (fc, tc) in installed:
        print(f"  Already installed: {fc} -> {tc}")
        continue
    match = next((p for p in available if p.from_code == fc and p.to_code == tc), None)
    if match:
        print(f"  Installing {fc} -> {tc}...")
        try:
            pkg.install_from_path(match.download())
            print(f"    OK")
        except Exception as e:
            print(f"    FAILED: {e}")
    else:
        print(f"  Not found: {fc} -> {tc}")
PYEOF

echo ""
echo " [3/3] Creating launcher..."
cat > "$DIR/run.sh" <<LAUNCHER
#!/usr/bin/env bash
cd "$(dirname "\$0")"
python3 hermes.py
LAUNCHER
chmod +x "$DIR/run.sh"

echo ""
echo " ═══════════════════════════════════════════════"
echo "  Done! Launch with:"
echo "    bash run.sh"
echo "    — or —"
echo "    python3 hermes.py"
echo " ═══════════════════════════════════════════════"
echo ""
