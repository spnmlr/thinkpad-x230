#!/usr/bin/env bash
# ==============================================================================
# ThinkPad X230 Fingerprint Fix Installer
# Automated: Arch Linux / CachyOS / Manjaro
# Other distros (Fedora / Debian / Ubuntu): applies TLP rule & prints manual build steps
# Hardware: Upek TouchChip Fingerprint Coprocessor (USB ID 147e:2020)
# ==============================================================================
set -euo pipefail

if [ "${EUID}" -eq 0 ]; then
    echo "Error: Do not run this script as root (makepkg refuses to run as root)." >&2
    echo "Run it as your normal user; sudo will be requested when needed." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "  ThinkPad X230: Upek 147e:2020 Fingerprint Fix Installer "
echo "=========================================================="
echo

# 1. TLP Autosuspend Fix
echo "[1/5] Configuring TLP USB Autosuspend Denylist..."
if [ -d /etc/tlp.d ]; then
    sudo cp "${SCRIPT_DIR}/01-fingerprint.conf" /etc/tlp.d/01-fingerprint.conf
    if command -v tlp >/dev/null 2>&1; then
        sudo tlp start >/dev/null 2>&1 || true
    fi
    echo "  [OK] Added USB 147e:2020 to /etc/tlp.d/01-fingerprint.conf"
else
    echo "  [INFO] /etc/tlp.d/ not found (TLP not installed). Skipping."
fi

# 2. Clean up dangerous backup files in /usr/lib that mislead ldconfig
echo "[2/5] Checking /usr/lib for legacy or backup libfprint libraries..."
for stale_lib in /usr/lib/libfprint-2.so*.orig /usr/lib/libfprint-2.so*.bak; do
    if [ -f "${stale_lib}" ]; then
        echo "  [WARN] Found '${stale_lib}' in /usr/lib/!"
        echo "         Removing from /usr/lib to prevent ldconfig symlink hijacking..."
        sudo rm -f "${stale_lib}"
    fi
done

# 3. Build & install patched libfprint
echo "[3/5] Building & installing patched libfprint..."
if command -v pacman >/dev/null 2>&1 && command -v makepkg >/dev/null 2>&1; then
    cd "${SCRIPT_DIR}"
    makepkg -si --noconfirm

    # Protect against accidental overwrite by pacman -Syu
    if [ -f /etc/pacman.conf ]; then
        if grep -Eq '^[[:space:]]*IgnorePkg[[:space:]]*=.*([[:space:]=]|^)libfprint([[:space:]]|#|$)' /etc/pacman.conf; then
            echo "  [OK] libfprint is already protected in /etc/pacman.conf"
        else
            sudo sed -i '/^\[options\]/a IgnorePkg = libfprint' /etc/pacman.conf
            echo "  [OK] Added 'IgnorePkg = libfprint' under [options] in /etc/pacman.conf"
        fi
    fi
else
    echo "  [NOTICE] Non-Arch distribution detected."
    echo "  TLP rule (if applicable) was configured. To build libfprint manually for your"
    echo "  distro, apply 'libfprint-upektc-fix.patch' to upstream libfprint sources and"
    echo "  build with meson (see fingerprint/README.md Section 4)."
    exit 0
fi

# 4. Refresh dynamic linker & restart service
echo "[4/5] Updating dynamic linker cache & restarting fprintd.service..."
if command -v ldconfig >/dev/null 2>&1; then
    sudo ldconfig
fi
if systemctl list-unit-files fprintd.service --no-legend 2>/dev/null | grep -q '^fprintd\.service'; then
    sudo systemctl daemon-reload
    sudo systemctl restart fprintd
    echo "  [OK] fprintd restarted with patched libfprint."
else
    echo "  [INFO] fprintd.service not installed yet. Install 'fprintd' to enroll fingerprints."
fi

# 5. Optional PAM integration
echo "[5/5] Checking PAM configuration for sudo..."
if grep -q "pam_fprintd.so" /etc/pam.d/sudo 2>/dev/null; then
    echo "  [OK] PAM for sudo is already configured (/etc/pam.d/sudo)."
else
    if [ -t 0 ]; then
        read -r -p "Enable fingerprint unlock for 'sudo'? [Y/n]: " answer
        answer=${answer:-Y}
        if [[ "$answer" =~ ^[yYjJ] ]]; then
            if [ ! -f /etc/pam.d/sudo ]; then
                if [ -f /usr/lib/pam.d/sudo ]; then
                    sudo cp /usr/lib/pam.d/sudo /etc/pam.d/sudo
                else
                    echo "  [WARN] /etc/pam.d/sudo not found. Skipping PAM configuration."
                fi
            fi
            if [ -f /etc/pam.d/sudo ]; then
                if head -n1 /etc/pam.d/sudo | grep -q '^#%PAM-1\.0'; then
                    sudo sed -i '1a auth      sufficient pam_fprintd.so' /etc/pam.d/sudo
                else
                    sudo sed -i '1s/^/auth      sufficient pam_fprintd.so\n/' /etc/pam.d/sudo
                fi
                echo "  [OK] Fingerprint auth enabled in /etc/pam.d/sudo."
            fi
        fi
    fi
fi

echo
echo "=========================================================="
echo "  Installation Complete!                                  "
echo "=========================================================="
echo "Important recommendation:"
echo "Re-enroll your finger now to replace low-quality stock templates"
echo "(captures 25-30 minutiae instead of only 4-5):"
echo
echo "  fprintd-enroll -f right-index-finger"
echo
echo "Then test 1st-swipe verification:"
echo "  fprintd-verify -f right-index-finger"
echo "  sudo -k && sudo whoami"
echo "=========================================================="
