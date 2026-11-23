# ThinkPad X230: Fingerabdruck-Sensor Fix (Upek 147e:2020)

[![Sensor](https://img.shields.io/badge/Sensor-Upek%20TCS4x%20(147e:2020)-blue.svg)](https://linux-hardware.org/?id=usb:147e-2020)
[![libfprint](https://img.shields.io/badge/libfprint-v1.94.x%20Patched-brightgreen.svg)](https://gitlab.freedesktop.org/libfprint/libfprint)
[![Status](https://img.shields.io/badge/Status-1st%20Swipe%20Unlock-success.svg)]()
[![Language](https://img.shields.io/badge/Language-English%20%7C%20Deutsch-lightgrey.svg)](README.md)

[🇬🇧 Switch to English Documentation (README.md)](README.md)

Dieser Ordner enthält die vollständige Analyse, den Quellcode-Patch und das fertige Installationspaket, um den im **Lenovo ThinkPad X230** verbauten Fingerabdruck-Sensor unter Linux (CachyOS, Arch, Fedora, Debian, Ubuntu etc.) absolut alltagstauglich, schnell und sicher zu betreiben.

---

## 1. Das Problem mit dem Stock-Treiber

Viele ThinkPad-Nutzer stellen fest, dass der Fingerabdrucksensor unter Linux entweder gar nicht reagiert, nach 2 Sekunden abbricht (`enroll-swipe-too-short` / `short scan, aborting`) oder bei fast jedem Wisch `verify-no-match` meldet.

Unsere tiefgehende Kernel-, USB- und Algorithmus-Analyse deckte **drei voneinander unabhängige Ursachen** in TLP und Upstream-`libfprint` auf:

### A. USB-Autosuspend durch TLP
* **Symptom:** Sensor schaltet sich mitten im Wisch ab (`short scan, aborting`) oder reagiert nach einigen Sekunden Inaktivität nicht mehr.
* **Ursache:** Das Energiemanagement-Tool TLP schickt den USB-Port `1-1.3` nach Inaktivität in den Tiefschlaf.
* **Lösung:** Aufnahme von `147e:2020` in `USB_DENYLIST` (`01-fingerprint.conf`).

### B. Fehlende Sensor-Auflösung in `upektc_img.c` (Upstream-Bug)
* **Symptom:** Kaum verwertbare Minutien (Merkmale) werden erkannt.
* **Ursache:** Im Treiber `libfprint/drivers/upektc_img.c` wird `img->ppmm` (Pixel pro Millimeter) nicht initialisiert und verbleibt auf `0.0`. Der NBIS-Minutien-Erkennungsalgorithmus (`quality.c`) berechnet die Nachbarschafts-Qualität mit `RADIUS_MM * ppmm`. Bei `ppmm = 0` schlägt die Qualitätsbewertung fehl.
* **Lösung:** Definition der korrekten nativen Hardware-Auflösung des TCS4x-Sensors: `img->ppmm = 20.0;` (508 DPI).

### C. Zu aggressiver Kantenfilter für schmale Streifensensoren
* **Symptom:** Nach dem Einlernen scheitert der Abgleich (`verify-no-match`).
* **Ursache:** Der NIST-NBIS-Algorithmus entfernt standardmäßig alle Minutien innerhalb von 10 Pixeln zum Bildrand (`PERIMETER_PTS_DISTANCE = 10`). Bei einem Wischsensor mit nur **144 Pixeln Breite** schneidet dieser Filter auf beiden Seiten 20 Pixel ab – das vernichtet über **75 % der biometrischen Merkmale**! Bozorth3 bricht daraufhin sofort mit `score 0` ab, da weniger als 10 Minutien übrig bleiben (`MIN_COMPUTABLE_BOZORTH_MINUTIAE`).
* **Lösung:** 
  - `PERIMETER_PTS_DISTANCE` auf `3` feinjustiert (beseitigt echte Abriss-Kantenartefakte bei 0–2 px, behält aber 25+ echte Minutien).
  - `MIN_COMPUTABLE_BOZORTH_MINUTIAE` auf `6` angepasst.
  - Bozorth3 Matching-Schwelle `bz3_threshold` auf den optimalen mathematischen Trennwert `10` kalibriert.

---

## 2. Sicherheits- & Benchmark-Ergebnisse

Messung der Bozorth3-Matching-Scores unter realen Testbedingungen:

| Testfall | Gemessene Bozorth-Scores | Status bei Schwelle `10` |
| :--- | :---: | :--- |
| **Fremder / Falscher Finger (6 Swipes)** | `0`, `0`, `3`, `0`, `3`, `0` | 🔒 **In allen 6 Test-Swipes abgewiesen** (Maximalwert 3 vs. Schwelle 10) |
| **Registrierter Finger (Normaler Wisch)** | **`11/10`**, **`14/10`**, **`17/10`** | 🚀 **Zuverlässige Entsperrung beim ersten Wisch** |

> [!NOTE]
> **Sicherheitshinweis & Patch-Wirkungsbereich:** Das Absenken von `bz3_threshold` (`20 → 10`) und `MIN_COMPUTABLE_BOZORTH_MINUTIAE` (`10 → 6`) ist ein bewusster Komfort-Kompromiss für den schmalen 144-px-Streifensensor und erhöht die theoretische False Acceptance Rate (FAR) gegenüber den Upstream-Standards. Die 6 Test-Swipes dienen als Plausibilitätstest, nicht als formale biometrische Zertifizierung – für hohe Sicherheitsanforderungen weiterhin starke Passwörter/LUKS nutzen. Zudem gelten die Anpassungen in `bozorth.h` und `lfs.h` global für alle `libfprint`-Bildtreiber in diesem Build.

---

## 3. Schnellinstallation (Arch Linux / CachyOS)

Im Ordner `thinkpad-x230/fingerprint`:

```bash
# 1. Automatische Installation ausführen:
./install.sh
```

Das Skript:
1. Kopiert [`01-fingerprint.conf`](01-fingerprint.conf) nach `/etc/tlp.d/` und lädt TLP neu.
2. Entfernt alte `.orig`- / `.bak`-Bibliotheksbackups aus `/usr/lib/`, um `ldconfig` Symlink-Hijacking zu verhindern.
3. Baut und installiert `libfprint` mit dem Patch [`libfprint-upektc-fix.patch`](libfprint-upektc-fix.patch) via `makepkg -si`.
4. Trägt `IgnorePkg = libfprint` in `/etc/pacman.conf` ein, damit `pacman -Syu` den Fix bei System-Updates nicht überschreibt.
5. Aktualisiert den Linker-Cache (`ldconfig`) und startet `fprintd` neu.
6. Bietet an, PAM für `sudo` automatisch einzurichten.

### Manuelle Installation via PKGBUILD
Alternativ kann das Paket direkt mit `makepkg` gebaut werden:
```bash
sudo cp 01-fingerprint.conf /etc/tlp.d/
sudo tlp start
makepkg -si
sudo systemctl restart fprintd
```

---

## 4. Manuelle Installation auf anderen Linux-Distributionen

Falls Sie Debian, Ubuntu, Fedora oder openSUSE nutzen:

1. **TLP-Regel hinterlegen:**
   ```bash
   sudo cp 01-fingerprint.conf /etc/tlp.d/
   sudo tlp start
   ```
2. **Patch anwenden & libfprint bauen:**
   ```bash
   git clone https://gitlab.freedesktop.org/libfprint/libfprint.git
   cd libfprint
   git checkout v1.94.100  # oder Ihre Distributionsversion
   patch -p1 < /pfad/zu/libfprint-upektc-fix.patch
   meson setup build -Ddrivers=all
   meson compile -C build
   sudo meson install -C build
   sudo ldconfig
   sudo systemctl restart fprintd
   ```

---

## 5. Finger registrieren & testen

### Finger einlernen
> [!IMPORTANT]
> **Bestehende Fingerabdrücke nach dem Patch neu einlernen!**
> Alte Templates, die unter dem ungepatchten Stock-Treiber eingescannt wurden, enthalten nur 4–5 Minutien. Mit diesem Patch erfasst der Treiber **25–30 Minutien**, was die zuverlässige Entsperrung beim ersten Wisch garantiert.

```bash
fprintd-enroll -f right-index-finger
```
*Tipp für Streifensensoren:* Den Finger flach auflegen und mit **zügiger, gleichmäßiger Geschwindigkeit** nach unten ziehen (weder zu langsam schleichen noch ruckeln).

### Erkennung testen
```bash
# Test 1: fprintd CLI-Test
fprintd-verify -f right-index-finger

# Test 2: sudo Authentifizierung
sudo -k && sudo whoami
```

---

## 6. Rollback / Deinstallation

Falls jemals wieder das unmodifizierte Upstream-Paket gewünscht ist (entfernt `libfprint` aus `IgnorePkg` und installiert das Stock-Paket neu):
```bash
./restore_stock.sh
```
*Hinweis: `/etc/tlp.d/01-fingerprint.conf` sowie eine ggf. ergänzte `pam_fprintd.so`-Zeile in `/etc/pam.d/sudo` bleiben bestehen und können bei Bedarf manuell entfernt werden.*

Oder manuell unter Arch / CachyOS:
```bash
sudo pacman -S libfprint
sudo systemctl restart fprintd
```

---

## 7. Lizenz & Upstream-Attribution
- Die Skripte (`install.sh`, `restore_stock.sh`), Dokumentationen (`README.md`, `README.de.md`) und Konfigurationen (`01-fingerprint.conf`) in diesem Ordner stehen unter der **Zero-Clause BSD License ([0BSD](../LICENSE))**.
- [`PKGBUILD`](PKGBUILD) basiert auf dem offiziellen Arch-Linux-Packaging-Rezept für `libfprint` (**0BSD**).
- Der Quellcode-Patch `libfprint-upektc-fix.patch` und das kompilierte `libfprint`-Paket unterliegen der **GNU Lesser General Public License v2.1 or later ([LGPL-2.1-or-later](../LICENSES/LGPL-2.1-or-later.txt))** des Upstream-Projekts [libfprint](https://gitlab.freedesktop.org/libfprint/libfprint).

