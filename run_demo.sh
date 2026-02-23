#!/usr/bin/env bash

set -euo pipefail

# ---------- Colors ----------
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
RESET='\033[0m'

# ---------- Helpers ----------
info() {
  printf "%b[INFO]%b %s\n" "$BLUE" "$RESET" "$1"
}

success() {
  printf "%b[OK]%b %s\n" "$GREEN" "$RESET" "$1"
}

warn() {
  printf "%b[WARN]%b %s\n" "$YELLOW" "$RESET" "$1"
}

error() {
  printf "%b[ERROR]%b %s\n" "$RED" "$RESET" "$1"
}

print_header() {
  printf "\n%b=============================================%b\n" "$BLUE" "$RESET"
  printf "%b   Kelsen-Graph Zero-Setup Demo Launcher%b\n" "$GREEN" "$RESET"
  printf "%b=============================================%b\n\n" "$BLUE" "$RESET"
}

# ---------- 1) Corporate banner ----------
print_header

# ---------- 2) System dependency check ----------
if ! command -v python3 >/dev/null 2>&1; then
  error "python3 is not installed on this system."
  error "Please install Python 3 and run this script again."
  exit 1
fi
success "System dependency check passed (python3 found)."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ---------- 3) Silent environment isolation ----------
info "Configuring the engine (virtual environment)..."
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv >/dev/null 2>&1
  success "Virtual environment created."
else
  success "Virtual environment already available."
fi

# shellcheck disable=SC1091
source .venv/bin/activate

cleanup() {
  deactivate >/dev/null 2>&1 || true
}
trap cleanup EXIT

# ---------- 4) Silent provisioning ----------
info "Provisioning dependencies (quiet mode)..."
python -m pip install --upgrade pip --quiet >/dev/null 2>&1
python -m pip install -r requirements.txt --quiet >/dev/null 2>&1
success "Dependencies are ready."

# ---------- 5) Demo execution ----------
info "Launching executive showroom demo (offline mock mode)..."
python demo.py --mock
success "Demo completed successfully."
