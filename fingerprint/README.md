# ThinkPad X230: Fingerprint Reader Fix (Upek 147e:2020)

[![Sensor](https://img.shields.io/badge/Sensor-Upek%20TCS4x%20(147e:2020)-blue.svg)](https://linux-hardware.org/?id=usb:147e-2020)
[![libfprint](https://img.shields.io/badge/libfprint-v1.94.x%20Patched-brightgreen.svg)](https://gitlab.freedesktop.org/libfprint/libfprint)
[![Status](https://img.shields.io/badge/Status-1st%20Swipe%20Unlock-success.svg)]()
[![Language](https://img.shields.io/badge/Language-English%20%7C%20Deutsch-lightgrey.svg)](README.de.md)

[🇩🇪 Zur deutschen Dokumentation wechseln (README.de.md)](README.de.md)

This directory contains the root-cause analysis, source patch, build recipe (PKGBUILD), and automated installer to make the **Upek TouchChip TCS4x fingerprint swipe reader (USB ID `147e:2020`)** in the **Lenovo ThinkPad X230** (and compatible X220, T430, W530 models) work reliably, securely, and instantly on Linux (Arch Linux, CachyOS, Fedora, Ubuntu, Debian, etc.).

---

## 1. Upstream Driver Bugs & Failure Analysis

Users frequently report that the X230 fingerprint sensor under Linux either times out, aborts mid-swipe (`enroll-swipe-too-short` / `short scan, aborting`), or fails to match registered fingers (`verify-no-match`).

Our deep-dive kernel, USB, and algorithmic trace revealed **three distinct, compounding upstream bugs**:

### A. Aggressive USB Autosuspend (TLP)
* **Symptom:** Sensor disconnects mid-swipe or fails to wake up on auth requests.
* **Cause:** Linux power-management tools (TLP) place the USB port (`1-1.3`) into autosuspend after brief inactivity.
* **Solution:** Whitelist `147e:2020` in `USB_DENYLIST` ([`01-fingerprint.conf`](01-fingerprint.conf)).

### B. Uninitialized Sensor DPI in `upektc_img.c`
* **Symptom:** Almost zero minutiae are recognized, causing match scores of `0`.
* **Cause:** In upstream `libfprint/drivers/upektc_img.c`, `img->ppmm` (pixels per millimeter) was left uninitialized at `0.0`. The NIST NBIS minutiae extraction engine (`quality.c`) computes neighborhood minutiae quality using `RADIUS_MM * ppmm`. With `ppmm = 0.0`, all minutiae fail quality checks.
* **Solution:** Set the native physical resolution of the TCS4x swipe sensor: `img->ppmm = 20.0;` (508 DPI).

### C. Overly Aggressive Perimeter Filter for Narrow Swipe Sensors
* **Symptom:** After enrollment, almost all verification swipes fail (`verify-no-match`).
* **Cause:** The NIST NBIS algorithm defaults to removing all minutiae within 10 pixels of the scan boundary (`PERIMETER_PTS_DISTANCE = 10`). On a swipe sensor only **144 pixels wide**, this edge filter cuts off 20 pixels total—**destroying over 75% of valid minutiae**! Bozorth3 then terminates with `score 0` because fewer than 10 minutiae survive (`MIN_COMPUTABLE_BOZORTH_MINUTIAE`).
* **Solution:**
  - Fine-tune `PERIMETER_PTS_DISTANCE` from `10` down to `3` (removes true scan-boundary artifacts while preserving 25+ real minutiae).
  - Adjust `MIN_COMPUTABLE_BOZORTH_MINUTIAE` to `6`.
  - Calibrate Bozorth3 matching threshold `bz3_threshold` from `20` to `10`.

---

## 2. Biometric Security & Benchmark Validation

Real-world Bozorth3 match scores tested on the ThinkPad X230:

| Test Scenario | Measured Bozorth Scores | Result with Threshold `10` |
| :--- | :---: | :--- |
| **Unregistered / Wrong Finger (6 Swipes)** | `0`, `0`, `3`, `0`, `3`, `0` | 🔒 **Rejected in all 6 test swipes** (Max observed score: 3 vs. threshold 10) |
| **Registered Finger (Normal Swipe)** | **`11/10`**, **`14/10`**, **`17/10`** | 🚀 **Reliable 1st-swipe unlock** |

> [!NOTE]
> **Security Trade-off & Patch Scope:** Lowering `bz3_threshold` (`20 → 10`) and `MIN_COMPUTABLE_BOZORTH_MINUTIAE` (`10 → 6`) is a deliberate usability trade-off for the narrow 144 px swipe sensor and increases the theoretical False Acceptance Rate (FAR) compared to upstream defaults. The 6-swipe check above is a sanity test, not a formal biometric evaluation; keep strong password/LUKS encryption for high-security use cases. Also note that the edits in `bozorth.h` and `lfs.h` apply globally to all `libfprint` image drivers in this build.

---

## 3. Quick Installation (Arch Linux / CachyOS / Manjaro)

```bash
cd fingerprint
chmod +x install.sh
./install.sh
```

What `install.sh` does automatically:
1. Installs [`01-fingerprint.conf`](01-fingerprint.conf) into `/etc/tlp.d/` and reloads TLP.
2. Removes any leftover `.orig` / `.bak` shared objects from `/usr/lib/` to prevent `ldconfig` symlink hijacking.
3. Builds and installs the patched `libfprint` package via `makepkg -si`.
4. Adds `IgnorePkg = libfprint` in `/etc/pacman.conf` to prevent subsequent `pacman -Syu` from silently overwriting the fix.
5. Updates dynamic linker cache (`ldconfig`) and restarts `fprintd.service`.
6. Offers optional PAM configuration for `sudo` authentication.

---

## 4. Manual Installation on Other Distributions (Debian, Ubuntu, Fedora)

1. **Configure TLP:**
   ```bash
   sudo cp 01-fingerprint.conf /etc/tlp.d/
   sudo tlp start
   ```

2. **Apply Patch & Build `libfprint`:**
   ```bash
   git clone https://gitlab.freedesktop.org/libfprint/libfprint.git
   cd libfprint
   git checkout v1.94.100  # or your distribution's version
   patch -p1 < /path/to/libfprint-upektc-fix.patch
   meson setup build -Ddrivers=all
   meson compile -C build
   sudo meson install -C build
   sudo ldconfig
   sudo systemctl restart fprintd
   ```

---

## 5. Enrolling & Testing Fingerprints

### Enrolling
> [!IMPORTANT]
> **Re-enroll existing fingerprints after applying this patch!**
> Old templates enrolled under the unpatched stock driver only contain 4–5 minutiae. With this patch, the driver captures **25–30 minutiae**, enabling effortless 1st-swipe unlocking.

```bash
fprintd-enroll -f right-index-finger
```
*Swipe tip:* Place the finger flat against the sensor and swipe downward in a steady, smooth motion (neither too fast nor too hesitant).

### Testing
```bash
# Test via fprintd CLI:
fprintd-verify -f right-index-finger

# Test sudo integration:
sudo -k && sudo whoami
```

---

## 6. Rollback / Uninstallation

To revert to your distribution's vanilla `libfprint` package (removes `libfprint` from `IgnorePkg` and reinstalls stock `libfprint`):
```bash
./restore_stock.sh
```
*Note: `/etc/tlp.d/01-fingerprint.conf` and any `pam_fprintd.so` line added to `/etc/pam.d/sudo` are left intact; remove them manually if you want a full cleanup.*

---

## 7. License & Credits

- The installation scripts (`install.sh`, `restore_stock.sh`), documentation (`README.md`, `README.de.md`), and configs (`01-fingerprint.conf`) are licensed under the **Zero-Clause BSD License ([0BSD](../LICENSE))**.
- [`PKGBUILD`](PKGBUILD) is derived from the official Arch Linux `libfprint` packaging recipe (**0BSD**).
- The patch [`libfprint-upektc-fix.patch`](libfprint-upektc-fix.patch) and compiled `libfprint` binaries are subject to the **GNU Lesser General Public License v2.1 or later ([LGPL-2.1-or-later](../LICENSES/LGPL-2.1-or-later.txt))** from upstream [libfprint](https://gitlab.freedesktop.org/libfprint/libfprint).
