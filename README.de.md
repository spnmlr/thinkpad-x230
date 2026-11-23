# ThinkPad X230: Mod-BIOS, thinkpad-ec Akku-Patch & Linux-Optimierungs-Guide

[![ThinkPad](https://img.shields.io/badge/ThinkPad-X230-red.svg)](https://www.thinkwiki.org/wiki/Category:X230)
[![BIOS](https://img.shields.io/badge/BIOS-1vyrain%202.77%20Mod-blue.svg)](https://1vyra.in/)
[![EC](https://img.shields.io/badge/EC-thinkpad--ec%201.14%20(Patched)-brightgreen.svg)](https://github.com/hamishcoleman/thinkpad-ec)
[![OS](https://img.shields.io/badge/OS-CachyOS%20%2F%20Linux%207.x-orange.svg)](https://cachyos.org)
[![License: 0BSD](https://img.shields.io/badge/License-0BSD-yellow.svg)](LICENSE)
[![Vibe Coded](https://img.shields.io/badge/Vibe_Coded-AI_Assisted_Engineering-blueviolet.svg)](#über-dieses-projekt--vibe-coding)
[![Language](https://img.shields.io/badge/Language-English%20%7C%20Deutsch-lightgrey.svg)](README.md)

[🇬🇧 Switch to English Documentation (README.md)](README.md)

Dieses Repository ist ein lückenloser, praxiserprobter **All-in-One-Leitfaden** zur Maximierung des legendären **Lenovo ThinkPad X230** – **100 % Vibe Coded** in Zusammenarbeit zwischen Mensch und KI (UEFI-Reverse-Engineering, C-Treiber-Debugging und Tests direkt an der echten Hardware):
- **`thinkpad-ec` Akku-Patch:** Entfernt die herstellerseitige Authentifizierungssperre, sodass günstige und ausdauernde **Dritthersteller- / Nachbau-Akkus** uneingeschränkt geladen werden.
- **`1vyrain` Mod-BIOS (Version 2.77):** Entfernt die WLAN-/WWAN-Whitelist und schaltet das BIOS *Advanced Menu* frei.
- **Dead-Battery-Bypass:** Ermöglicht das Flashen auch bei komplett defektem, leerem oder unauthentifiziertem Akku.
- **Budget-Hardware-Upgrades:** Die besten Upgrades für maximalen Nutzen bei minimalem Budget (AC-WLAN, Dual-Channel-RAM, SSD, IPS-Display).
- **CachyOS / Linux Vollsupport:** Vollständige Treiberunterstützung (Grafik, VA-API, TrackPoint, Fingerprint, Audio) und BIOS-Konfigurations-Empfehlungen.

---

## Inhaltsverzeichnis
1. [Empfohlene Budget-Upgrades (Hardware-Sweetspot)](#empfohlene-budget-upgrades)
2. [Optimale BIOS-Einstellungen (Setup-Guide)](#optimale-bios-einstellungen)
3. [Repository-Struktur](#repository-struktur)
4. [Flashing-Leitfaden](#flashing-leitfaden)
   - [Der Ohne-Akku-Bypass (Dead-Battery-Bypass)](#der-ohne-akku-bypass-dead-battery-bypass)
   - [Schritt 1: BIOS Downgrade auf 2.75](#schritt-1-bios-downgrade-auf-275)
   - [Schritt 2: thinkpad-ec Akku-Patch flashen](#schritt-2-thinkpad-ec-akku-patch-flashen)
   - [Schritt 3a: BIOS-Only Downgrade auf 2.60](#schritt-3a-bios-only-downgrade-auf-260-ivprep)
   - [Schritt 3b: 1vyrain Mod-BIOS 2.77 aufspielen](#schritt-3b-1vyrain-mod-bios-277-aufspielen)
5. [CachyOS / Linux Treiber- & System-Support](#cachyos--linux-treiber---system-support)
6. [Akkumanagement & TLP](#akkumanagement--tlp)
7. [Hardware-Optimierungen im Detail](#hardware-optimierungen-im-detail)
8. [Sicherheitshinweise & Disclaimer](#sicherheitshinweise--disclaimer)
9. [Über dieses Projekt / Vibe Coding](#über-dieses-projekt--vibe-coding)
10. [Credits & Referenzen](#credits--referenzen)

---

## Empfohlene Budget-Upgrades

Mit wenigen, sehr günstigen Gebraucht- oder Nachrüstteilen wird das X230 zu einer modernen, lautlosen und extrem ausdauernden Arbeitsmaschine:

| Komponente | Empfehlung & Modell | Ca.-Preis | Warum & Nutzen |
| :--- | :--- | :---: | :--- |
| **WLAN** | **Intel Dual Band Wireless-AC 7260** (mPCIe) | ~10–15 € | Ersetzt langsames 2,4-GHz-WLAN durch **802.11ac (bis 867 Mbit/s im 5-GHz-Band)**. *(Benötigt das 1vyrain Mod-BIOS wegen der Lenovo-Whitelist).* |
| **Arbeitsspeicher** | **8 GB DDR3-1600 (2x 4 GB)** | ~10–15 € | **WICHTIG:** 2 Riegel aktivieren **Dual-Channel (128-Bit)**! Das verdoppelt die Speicherbandbreite und steigert die Grafikleistung der Intel HD 4000 GPU spürbar. *(Maximal 16 GB via 2x 8 GB möglich).* |
| **Hauptspeicher** | **2,5" SATA SSD (250 GB – 500 GB)** | ~20–30 € | z. B. Samsung 850/860 EVO oder Crucial MX500. Macht das System lautlos, schockresistent und bootet CachyOS in unter 10 Sekunden. |
| **Akku** | **9-Zellen-Nachbauakku (`45N1029`)** | ~25–35 € | Liefert **94 Wh Kapazität** für 8–11 Stunden reale Laufzeit. Lädt dank unserem `thinkpad-ec`-Patch sofort ohne Ladesperre. |
| **Display** | **IPS-Panel (`LP125WH2-SLB3` / `SLT1`)** | ~35–45 € | 178°-Blickwinkelstabilität, satte Kontraste und leuchtende Farben – ein gigantischer Unterschied zum blassen ab Werk verbauten TN-Panel. |
| **Zweitlaufwerk** | **mSATA SSD (interner Slot)** | optional | Der durch den Ausbau des veralteten 3G-WWAN-Moduls frei werdende Slot unterstützt mSATA (SATA II, 3 Gbit/s) für eine zweite interne SSD. |

---

## Optimale BIOS-Einstellungen

Vor dem Flashen und für den optimalen Betrieb unter modernem Linux (CachyOS) sollten im BIOS (Taste **F1** beim Booten) folgende Einstellungen gesetzt werden:

### 1. Vorbereitungen für das Flashing & Downgrades
* **`Security` $\rightarrow$ `Secure Boot`:**  
  $\rightarrow$ `Secure Boot`: **[Disabled]** *(Zwingend erforderlich, damit der modifizierte Bootloader und 1vyrain starten können).*
* **`Security` $\rightarrow$ `UEFI BIOS Update Option`:**  
  $\rightarrow$ `Flash BIOS Updating by End-Users`: **[Enabled]**  
  $\rightarrow$ `Secure Rollback Prevention`: **[Disabled]** *(Zwingend erforderlich, damit BIOS-Downgrades erlaubt werden).*

### 2. Boot- & Betriebs-Einstellungen
* **`Startup` $\rightarrow$ `UEFI/Legacy Boot`:**  
  $\rightarrow$ `UEFI/Legacy Boot`: **[Both]**  
  $\rightarrow$ `UEFI/Legacy Boot Priority`: **[UEFI First]**  
  $\rightarrow$ `CSM Support`: **[Yes]**  
  *(Ermöglicht schnelles natives UEFI-Booten für CachyOS und hält gleichzeitig DOS/MBR-Kompatibilität für ältere Rettungs-Sticks bereit).*
* **`Config` $\rightarrow$ `Serial ATA (SATA)`:**  
  $\rightarrow$ `SATA Controller Mode`: **[AHCI]** *(Maximaler SSD-Datendurchsatz und TRIM-Unterstützung).*
* **`Config` $\rightarrow$ `Power`:**  
  $\rightarrow$ `Intel SpeedStep technology`: **[Enabled]**, `Mode`: **[Battery Optimized]** / **[Maximum Performance]**  
  $\rightarrow$ `CPU Power Management`: **[Automatic]**

---

## Repository-Struktur

```text
thinkpad-x230/
├── README.md                     # Vollständiger All-in-One-Leitfaden (Englisch)
├── README.de.md                  # Vollständiger All-in-One-Leitfaden (Deutsch)
├── llms.txt                      # Maschinenlesbarer LLM-Index & Problem-Lösungs-Baum (llmstxt.org)
├── LICENSE                       # Zero-Clause BSD License (0BSD)
├── LICENSES/                     # Volltexte von Drittanbieter-Lizenzen (LGPL-2.1-or-later für libfprint-Patch)
│   └── LGPL-2.1-or-later.txt
├── scripts/                      # Firmware-Patcher & USB-Flashing-Skripte
│   ├── patch_battery_bypass.py   # Python-Patcher: Entfernt Akku- & Modellchecks aus BootX64.efi
│   ├── flash_usb_bios.sh         # Schreibt das BIOS-Downgrade-Image auf USB
│   ├── flash_usb_ec.sh           # Schreibt das gepatchte thinkpad-ec-Image auf USB
│   └── flash_usb_1vyrain.sh      # Schreibt das offizielle 1vyrain-Image auf USB
├── configs/                      # Linux-System- & Stromspar-Konfigurationen
│   ├── 00-battery.conf           # TLP-Konfiguration (Ladeschwellen, ASPM, Radio-Deaktivierung beim Start)
│   └── 81-disable-intel-bt.rules # Udev-Regel zur Abschaltung des Intel-Bluetooths
├── fingerprint/                  # Fix für Fingerabdrucksensor (147e:2020): libfprint-Patch, PKGBUILD, TLP-Regel & Installer
│   ├── README.md                 # Detaillierte Fehleranalyse & Anleitung (Englisch)
│   ├── README.de.md              # Detaillierte Fehleranalyse & Anleitung (Deutsch)
│   ├── libfprint-upektc-fix.patch # Quellcode-Patch für libfprint (508 DPI, Perimeter-Filter, Bozorth3)
│   ├── PKGBUILD                  # Arch / CachyOS Build-Rezept (makepkg)
│   ├── 01-fingerprint.conf       # TLP Autosuspend-Denylist für USB 147e:2020
│   ├── install.sh                # Vollautomatischer Installer
│   └── restore_stock.sh          # Rollback auf Original-Paket
└── thinkpad-ec/                  # Git-Submodul: thinkpad-ec Quellcode für den EC-Akku-Patch
```

---

## Flashing-Leitfaden

> [!IMPORTANT]
> **Voraussetzungen:**
> - Das ThinkPad muss während aller Flashvorgänge **am Netzteil** angeschlossen sein.
> - Ein leerer USB-Stick (mindestens 512 MB).

```mermaid
flowchart LR
    A["Original BIOS (z. B. 2.77)"] --> B["1. Downgrade auf 2.75<br/>(Akku-Bypass aktiv)"]
    B --> C["2. thinkpad-ec Flash<br/>(Akku-Patch aktiv)"]
    C --> D["3a. Downgrade BIOS 2.60<br/>(IVprep / EC bleibt erhalten)"]
    D --> E["3b. 1vyrain 2.77 Mod<br/>(Keine Whitelist + EC gepatcht)"]
```

### Der Ohne-Akku-Bypass (Dead-Battery-Bypass)
Das klassische Henne-Ei-Problem: Lenovo blockiert jeden BIOS-Flash, wenn der Akku defekt, tiefentladen oder ein noch nicht freigeschalteter Nachbau-Akku ist (*„Battery charge is low / Connect AC and fully charged battery“*). 

Um dieses Problem sauber zu lösen, überbrückt [`scripts/patch_battery_bypass.py`](scripts/patch_battery_bypass.py) alle Prüfungen direkt im 32-MB-Boot-Image (`bios_2.75.img` bzw. `patched.x230.img`) sowohl für den UEFI-Updater (`BootX64.efi`) als auch für die Legacy-DOS-Tools (`DOSFLASH.EXE`, `TPCHKS.EXE`, `UPDTFLSH.EXE`):

| Offset (`BootX64.efi`) | Original-Bytes | Gepatcht (`x86_64`) | Funktion |
| :--- | :--- | :--- | :--- |
| `0x911D1` | `55 48 89` | `31 c0 c3` (`xor eax, eax; ret`) | Netzteil-/Power-Check erzwingt `EFI_SUCCESS` |
| `0xE3FBC` | `48 8b c4` | `31 c0 c3` (`xor eax, eax; ret`) | Primäre Akkustandsprüfung meldet vollen Akku |
| `0x12D0E7` | `e8 dc ff` | `31 c0 c3` (`xor eax, eax; ret`) | Akku-Statusüberprüfung meldet Erfolg |
| `0xD98CF` | `74 07` | `eb 07` (`jmp +7`) | Überspringt den Plattform-Mismatch-Fehler (Downgrade-Modus) |
| `0xD74FA` | `25` | `35` (`--ec-only` Modus) | Deaktiviert BIOS-Flash, sodass nur der EC geflasht wird |
| `0xD9BCB` | `66 3b ce` | `eb 13 90` (`--ec-only` Modus) | Erzwingt EC-Flash trotz identischer Versionsnummer (`1.14`) |

**Anwendung:**
```bash
# Komplettes BIOS-Downgrade-Image (Schritt 1) direkt patchen:
python3 scripts/patch_battery_bypass.py build/bios_2.75.img

# Komplettes thinkpad-ec Image (Schritt 2, inkl. EC-Force-Flash) direkt patchen:
python3 scripts/patch_battery_bypass.py --ec-only thinkpad-ec/patched.x230.img
```

---

### Schritt 1: BIOS Downgrade auf 2.75
Neuere Lenovo-Versionen blockieren das Beschreiben des Embedded Controllers. Daher wird zunächst auf BIOS 2.75 downgegradet. Alle Akku- und Stromprüfungen werden vorab mit `scripts/patch_battery_bypass.py` überbrückt.

1. **Original Lenovo ISO 2.75 herunterladen, Prüfsummen verifizieren, extrahieren & Akku-Bypass patchen:**
   ```bash
   mkdir -p build
   wget https://download.lenovo.com/ibmdl/pub/pc/pccbbs/mobiles/g2uj31us.iso -O build/g2uj31us.iso
   wget https://raw.githubusercontent.com/rainer042/geteltorito/46474a4a86692b7c38ecdb4f135bee7badbfa8b0/geteltorito.pl -O build/geteltorito.pl
   printf '%s\n' \
     "520d3304d52aa2ec33332a3752b1426eb32ae9309331071e2af5717530dbf73c  build/g2uj31us.iso" \
     "97bc0b45189937058608a23d888510cfb7324985baa620c6348a9b78b88d22dc  build/geteltorito.pl" \
     | sha256sum -c -
   perl build/geteltorito.pl build/g2uj31us.iso > build/bios_2.75.img
   python3 scripts/patch_battery_bypass.py build/bios_2.75.img
   ```
2. **USB-Stick vorbereiten:**
   ```bash
   ./scripts/flash_usb_bios.sh /dev/sdX
   ```
3. Laptop neustarten, mit **F12** den USB-Stick im UEFI-Modus booten.
4. Den Bildschirmanweisungen folgen (Option **2** wählen, mit `Y` bestätigen).

---

### Schritt 2: thinkpad-ec Akku-Patch flashen
Flasht den modifizierten Embedded Controller `1.14` (`CONFIG_BATTERY = y`), der die Überprüfung des Akku-Authentifizierungschips deaktiviert.

1. **Submodul initialisieren, Patch-Image bauen & Akku-/EC-Force-Bypass anwenden:**
   ```bash
   git submodule update --init
   cd thinkpad-ec
   printf "CONFIG_BATTERY = y\nCONFIG_KEYBOARD = n\n" > .config
   make patched.x230.img
   cd ..
   python3 scripts/patch_battery_bypass.py --ec-only thinkpad-ec/patched.x230.img
   ```
2. **USB-Stick vorbereiten:**
   ```bash
   ./scripts/flash_usb_ec.sh /dev/sdX
   ```
3. Vom USB-Stick booten (**F12**).
4. Den Flashvorgang durchlaufen lassen. Das ThinkPad piept mehrmals und schaltet sich ab.
5. Nach dem Einschalten ist der Akku-Patch dauerhaft im EC verankert.

---

### Schritt 3a: BIOS-Only Downgrade auf 2.60 (IVprep)
Damit `1vyrain` ausgeführt werden kann, wird der bekannte S3-Bootscript-Exploit benötigt, der bis einschließlich BIOS `2.60` offen ist. Hierbei wird **nur** das BIOS downgegradet; der gepatchte EC (`1.14`) bleibt unberührt, da der Updater erkennt, dass EC `1.14` bereits installiert ist.

1. **Offizielles IVprep BIOS 2.60 herunterladen, Prüfsumme verifizieren & direkt in das Downgrade-Image injizieren:**
   ```bash
   mkdir -p build
   wget https://raw.githubusercontent.com/n4ru/IVprep/7faecc72be8776be32f37e7ff00af22a25dfc3cf/BIOS/X230.FL1 -O build/X230.FL1
   echo "c24934bdec1aa67550c54b542a015e4ceb1448fb279308331aeca7d950f35a99  build/X230.FL1" | sha256sum -c -
   python3 scripts/patch_battery_bypass.py --inject-bios build/X230.FL1 build/bios_2.75.img
   ```
2. **USB-Stick mit dem BIOS-2.60-Image beschreiben:**
   ```bash
   ./scripts/flash_usb_bios.sh /dev/sdX
   ```
3. Vom USB-Stick im UEFI-Modus starten (**F12**), Option **2** wählen und mit `Y` bestätigen.

---

### Schritt 3b: 1vyrain Mod-BIOS 2.77 aufspielen
Aktualisiert das BIOS auf die modifizierte Version 2.77 (ohne WLAN-Whitelist und mit freiem Menü), während der EC-Patch zu 100 % erhalten bleibt.

1. **1vyrain Live-ISO beziehen:**
   - Image von [1vyra.in](https://1vyra.in/) (Direktlink: [Google Drive Mirror](https://drive.google.com/open?id=1yusq98ja6NmI4G4txKVueFqY_ZEwaZvO), MD5: `dd30313a8665e870360920b00cec55c4`) herunterladen und als `build/1vyrain.iso` ablegen.
2. **Auf USB-Stick schreiben:**
   ```bash
   ./scripts/flash_usb_1vyrain.sh /dev/sdX
   ```
3. Im UEFI-Modus vom USB-Stick booten.
4. Wenn das ThinkPad in den Standby (S3) geht (pulsierende Power-LED), kurz die **Power-Taste drücken**, um es aufzuwecken.
5. Im Menü Option **`1` (`Flash Modified Lenovo BIOS`)** wählen.
6. Nach dem Neustart läuft das System auf **1vyrain 2.77 Mod + gepatchtem EC 1.14**.

---

## CachyOS / Linux Treiber- & System-Support

Unter **CachyOS** (oder jeder modernen Arch-basierten Distribution) funktioniert das X230 mit 100 %iger Treiberunterstützung *Out-of-the-Box*:

| Hardware-Komponente | Linux-Treiber / Modul | Status & Konfiguration |
| :--- | :--- | :--- |
| **Grafik (Intel HD 4000)** | `i915`, `mesa`, `vulkan-intel` | Native Hardwarebeschleunigung, flüssiges Wayland & X11 *(Vulkan via `hasvk` auf Ivy Bridge eingeschränkt/experimentell)* |
| **Video-Decoding (VA-API)** | `libva-intel-driver` | Entlastet die CPU beim Videostreaming (siehe unten) |
| **Audio (Realtek ALC269)** | `snd_hda_intel`, `pipewire` | Lautsprecher, Mikrofon, Dock-Anschlüsse & Klinke voll unterstützt |
| **TrackPoint & TouchPad** | `libinput` (Wayland) / `xf86-input-libinput` (X11) | Echtes TrackPoint-Scrollen mit mittlerer Maustaste nativ aktiv |
| **WLAN (Intel 7260AC)** | `iwlwifi` | Volle 802.11ac Geschwindigkeit und automatische Kanalwahl |
| **Bluetooth (Broadcom)** | `btusb` | Läuft über das BDC-4.0 Modul mit eigener interner Antenne |
| **Fingerabdrucksensor** | `fprintd` (`147e:2020`) | Zuverlässiges Entsperren beim 1. Wisch (Fix & Sicherheitshinweis in [`fingerprint/`](fingerprint/)) |
| **ThinkLight & Tastatur-LED**| `thinkpad_acpi` | Regelbar über Fn-Tastenkombinationen oder `/sys/class/leds` |

---

## Akkumanagement & TLP

Zur Schonung des Akkus sind Ladeschwellen (Start bei 75 %, Stop bei 85 %) in [`configs/00-battery.conf`](configs/00-battery.conf) vorkonfiguriert. Diese werden direkt in die Hardware-Register des ThinkPads geschrieben und bleiben auch bei ausgeschaltetem Gerät aktiv.

### TLP-Konfiguration aktivieren
```bash
sudo cp configs/00-battery.conf /etc/tlp.d/
sudo tlp start
```

### Nützliche Befehle im Alltag

| Aktion | Befehl |
| :--- | :--- |
| **Status & Gesundheit prüfen** | `upower -i $(upower -e \| grep -m1 'BAT')` |
| **Ausführlicher TLP-Bericht** | `sudo tlp-stat -b` |
| **Einmalig auf 100 % laden (z. B. vor Reisen)** | `sudo tlp fullcharge BAT0` |
| **Ladeschwellen temporär aufheben** | `sudo tlp setcharge 75 100 BAT0` |
| **Standard-Ladeschwellen wiederherstellen** | `sudo tlp setcharge 75 85 BAT0` |

---

## Hardware-Optimierungen im Detail

### 1. WLAN & Bluetooth (Dual-Adapter Trennung)
Die verbaute **Intel 7260AC** mPCIe-Karte bringt eigenes USB-Bluetooth mit (`8087:07dc`). Im X230 ist jedoch bereits die originale Broadcom Bluetooth Daughter Card (`BCM20702A1`) verbaut, welche über eine eigene Antenne im Displayrahmen verfügt.

Um Interferenzen, Audio-Aussetzer und Doppel-Adapter-Konflikte zu vermeiden, wird das Intel-Bluetooth dauerhaft per udev-Regel deaktiviert:
```bash
sudo cp configs/81-disable-intel-bt.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```
*Vorteil: Kein physisches Abkleben von Pin 51 an der mPCIe-Karte nötig!*  
*Hinweis: [`configs/00-battery.conf`](configs/00-battery.conf) deaktiviert Bluetooth beim Booten (`DEVICES_TO_DISABLE_ON_STARTUP="bluetooth wwan"`), um Strom zu sparen. Entferne `bluetooth` aus dieser Zeile, falls der Broadcom-Adapter direkt beim Start aktiv sein soll.*

### 2. Hardware-Videobeschleunigung (VA-API / YouTube)
Die integrierte Intel HD 4000 GPU unterstützt H.264-Hardwaredekodierung über VA-API (`libva-intel-driver`).
- **Browser-Empfehlung:** Firefox mit der Erweiterung **`enhanced-h264ify`** (blockiert VP8, VP9 und AV1).
- **Effekt:** YouTube-Streams laufen in flüssigem H.264 direkt auf der GPU; die CPU-Last sinkt auf ~4–5 %, wodurch das ThinkPad lautlos und kühl (~54 °C) bleibt.

### 3. Tastatur-Optionen
- **Standard X230 Chiclet-Tastatur:** Das System ist vorkonfiguriert für die originale 6-Reihen-Tastatur (`CONFIG_KEYBOARD = n`).
- **Klassische X220 7-Reihen-Tastatur (Classic Keyboard Mod):** Falls eine klassische ThinkPad-Tastatur verbaut wird, muss `thinkpad-ec` mit `CONFIG_KEYBOARD = y` kompiliert und geflasht werden, damit alle Scancodes (Pos1, Ende, BildAuf/Ab) hardwareseitig korrekt übersetzt werden.

### 4. Fingerabdruck-Sensor (Upek TouchChip 147e:2020)
Unter Standard-Linux scheitert der verbaute Wischsensor fast immer (`verify-no-match` oder `short scan`). Ursache sind Upstream-Bugs in `libfprint` (fehlende DPI-Initialisierung, zu aggressiver Randfilter für 144px Sensoren) sowie USB-Autosuspend durch TLP.
- **Lösung:** Vollständiger Patch, PKGBUILD und TLP-Konfiguration im Ordner [`fingerprint/`](fingerprint/).
- **Ergebnis:** Zuverlässiges Entsperren beim **ersten Wisch** für Login und `sudo` (gemessene Bozorth3-Scores: `0–3` bei 6 Fremdfinger-Test-Swipes vs. `11–17` beim registrierten Finger; siehe [`fingerprint/README.de.md`](fingerprint/README.de.md) zum Komfort-/FAR-Trade-off).
- **Installation:**
  ```bash
  cd fingerprint
  ./install.sh
  ```

---

## Sicherheitshinweise & Disclaimer

> [!CAUTION]
> **Warnung zum 1vyrain Advanced Menu (RAM-Takt):**
> Versuchen Sie **niemals**, im freigeschalteten BIOS-Menü den Speichertakt (*Memory Straps*, z. B. auf 1866 MHz) manuell zu verändern! Dies führt zu einem **sofortigen Hard-Brick** (dauerhaft schwarzer Bildschirm). Ein CMOS-Reset hilft hierbei nicht; das BIOS müsste hardwareseitig mit einer externen Zange (SPI-Flasher CH341A) neu programmiert werden.
> *(1866 MHz RAM funktioniert auf Ivy Bridge ausschließlich per Plug & Play über automatische JEDEC-SPD-Profile).*

### Haftungsausschluss & Rechtliche Hinweise
Modifikationen an BIOS, Embedded Controller (EC) und Firmware bergen immer das Risiko von Datenverlust oder dauerhafter Beschädigung der Hardware (Bricks). Alle Anleitungen, Patches und Skripte in diesem Repository werden ohne jegliche Gewähr bereitgestellt. Die Nutzung erfolgt vollumfänglich auf eigene Verantwortung und eigenes Risiko.

Markennamen (z. B. ThinkPad, Lenovo, Intel, Upek) und proprietäre Firmware gehören ihren jeweiligen Rechteinhabern. Dieses Repository enthält keine proprietären Lenovo-Binärdateien; offizielle Firmware-Images werden vom Nutzer lokal bezogen und gepatcht.

- **Repository-Lizenz:** Sofern nicht anders angegeben, stehen alle eigenen Dateien in diesem Repository (Skripte, Konfigurationen, Workflows und Dokumentationen) unter der **Zero-Clause BSD License ([0BSD](LICENSE))**.
- **Drittanbieter-Referenzen:** `thinkpad-ec` ist als Git-Submodul eingebunden (**GPL-2.0**). [`fingerprint/PKGBUILD`](fingerprint/PKGBUILD) basiert auf dem offiziellen Arch-Linux-Packaging-Rezept für `libfprint` (**0BSD**). Als Quellcode-Diff gegen Upstream-`libfprint` unterliegt [`fingerprint/libfprint-upektc-fix.patch`](fingerprint/libfprint-upektc-fix.patch) der **[LGPL-2.1-or-later](LICENSES/LGPL-2.1-or-later.txt)**.

---

## Über dieses Projekt / Vibe Coding
Dieses Repository ist ein **Vibe-Coding-Projekt**: Sämtliche Reverse-Engineering-Offsets im Lenovo UEFI-Updater (`BootX64.efi`), die C-Treiber- und NIST-NBIS-Fixes in `libfprint` für den Upek `147e:2020` Fingerabdrucksensor, die automatisierten Skripte sowie die KI-freundliche Aufbereitung ([`llms.txt`](llms.txt)) wurden iterativ im Zusammenspiel zwischen Mensch und KI direkt an echter ThinkPad-X230-Hardware entwickelt, debuggt und verifiziert.

---

## Credits & Referenzen
- **[1vyrain](https://1vyra.in/) & [IVprep](https://github.com/n4ru/IVprep)** (S3-Bootscript-Exploit & Mod-BIOS für ThinkPads der xx30-Generation)
- **[thinkpad-ec](https://github.com/hamishcoleman/thinkpad-ec)** (Embedded Controller Akku- & Tastatur-Patches)
- **[libfprint & fprintd](https://gitlab.freedesktop.org/libfprint/libfprint)** (freedesktop.org, LGPL-2.1-or-later)
- **[geteltorito](https://github.com/rainer042/geteltorito)** (El-Torito Boot-Image-Extraktor, GPLv3)
