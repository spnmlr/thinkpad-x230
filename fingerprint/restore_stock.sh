#!/usr/bin/env bash
# ==============================================================================
# ThinkPad X230 Fingerprint Fix - Rollback to Stock Distribution Package
# ==============================================================================
set -euo pipefail

echo "=== Restoring Stock libfprint ==="

if [ -f /etc/pacman.conf ]; then
    # Remove exact 'libfprint' token from IgnorePkg without mangling hyphenated packages (e.g. libfprint-tod)
    sudo sed -i -E '/^IgnorePkg[[:space:]]*=/ { s/([[:space:]=])libfprint([[:space:]]|$)/\1\2/g; s/[[:space:]]+/ /g; s/[[:space:]]+$//; }' /etc/pacman.conf
    # Clean up empty IgnorePkg line if necessary
    sudo sed -i -E '/^IgnorePkg[[:space:]]*=[[:space:]]*$/d' /etc/pacman.conf
fi

if command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm libfprint
    if command -v ldconfig >/dev/null 2>&1; then
        sudo ldconfig
    fi
    if systemctl list-unit-files fprintd.service --no-legend 2>/dev/null | grep -q '^fprintd\.service'; then
        sudo systemctl restart fprintd
    fi
    echo "Stock version of libfprint has been restored."
else
    echo "Error: pacman not found."
    exit 1
fi
