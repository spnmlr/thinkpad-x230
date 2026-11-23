#!/usr/bin/env python3
"""
patch_battery_bypass.py - ThinkPad X230 BIOS & EC Flash Battery, Platform & Force-Flash Patcher

DESCRIPTION:
    Lenovo's official BIOS update tools (both the 64-bit UEFI bootloader BootX64.efi
    and legacy DOS tools) strictly refuse to flash when:
      1. No battery is detected,
      2. The battery is deeply discharged (voltage below threshold),
      3. An unauthenticated third-party / aftermarket battery is installed,
      4. Downgrading to an older BIOS that does not recognize newer SMBIOS platform
         revisions ("The system program file is not correct for this system"),
      5. Flashing the patched Embedded Controller (thinkpad-ec) when the EC version
         on the USB drive (1.14) matches the already installed EC version (1.14).

    This creates a classic chicken-and-egg deadlock: you need to flash the BIOS/EC
    so an aftermarket battery can charge, but the flasher refuses to run because
    the aftermarket battery is not charged!

SUPPORTED TARGETS:
    This script patches standalone binaries (`BootX64.efi`, `DOSFLASH.EXE`,
    `TPCHKS.EXE`, `UPDTFLSH.EXE`) as well as complete 32 MB El Torito boot images
    (`bios_2.75.img` or `patched.x230.img`) directly in-place without mounting!

TECHNICAL PATCH OFFSETS IN BOOTX64.EFI (Version 2.75 / G2ETB5WW / g2uj31us.iso):
    1. Offset 0x911D1: AC Adapter / Power Check
       - Original:  55 48 89  [push rbp; mov rbp, rsp]  (Function prologue)
       - Patched:   31 c0 c3  [xor eax, eax; ret]        (Immediately returns 0 = EFI_SUCCESS)

    2. Offset 0xE3FBC: Primary Battery Charge Check
       - Original:  48 8b c4  [mov rax, rsp]             (Function prologue)
       - Patched:   31 c0 c3  [xor eax, eax; ret]        (Reports battery sufficiently charged)

    3. Offset 0x12D0E7: Battery Status Validation Check
       - Original:  e8 dc ff  [call ...]                 (Calls internal ACPI/EC status check)
       - Patched:   31 c0 c3  [xor eax, eax; ret]        (Bypasses EC check and returns success)

    4. Offset 0xD98CF: Platform Bitmask Check (Default Mode / BIOS Downgrade 2.75 & 2.60)
       - Original:  74 07     [je +7]                    (Conditional jump: aborts with exit code 0x6 on mismatch)
       - Patched:   eb 07     [jmp +7]                   (Unconditional jump: always bypasses platform lock)

    5. Additional Patches in `--ec-only` Mode (for Step 2: thinkpad-ec `patched.x230.img`):
       - Offset 0xD74FA: `25` -> `35` (`mov [rip-0xd1916], r14b` sets BIOS flash flag = 0 -> flashes EC only)
       - Offset 0xD9BCB: `66 3b ce` -> `eb 13 90` (`jmp +0x13; nop` -> forces EC flash despite identical version 1.14)

    6. PE Header & Authenticode Cleanup (UEFI BootX64.efi):
       - Offset 0x170..0x177: Zeroes the PE `IMAGE_DIRECTORY_ENTRY_SECURITY` entry
         so UEFI firmware does not reject the modified binary due to signature mismatch.
       - Offset 0x120..0x123: Recalculates the PE header `CheckSum` field.

USAGE:
    # 1. Patch complete BIOS downgrade image in-place (Step 1):
    python3 scripts/patch_battery_bypass.py build/bios_2.75.img

    # 2. Patch complete thinkpad-ec image in-place (Step 2, EC force-flash mode):
    python3 scripts/patch_battery_bypass.py --ec-only thinkpad-ec/patched.x230.img

    # 3. Inject IVprep BIOS 2.60 (X230.FL1) into downgrade image (Step 3a):
    python3 scripts/patch_battery_bypass.py --inject-bios build/X230.FL1 build/bios_2.75.img

    # 4. Patch standalone BootX64.efi binary:
    python3 scripts/patch_battery_bypass.py BootX64.efi [output_file]
"""

import sys
import os
import stat
import struct
import hashlib
import argparse
import tempfile

# Candidate file offsets inside the 32 MB El Torito FAT16 image (g2uj31us.iso and thinkpad-ec)
IMG_FILE_OFFSETS = {
    "BootX64.efi": ([0x1C2600], 1252016),
    "DOSFLASH.EXE": ([0x90600, 0xE0E00], 328192),
    "TPCHKS.EXE": ([0x16C600, 0x16F600, 0x15DE00], 4550),
    "UPDTFLSH.EXE": ([0x131600], 43964),
    "$01D3000.FL1": ([0x2F4600], 8388688),
}

# Base patches for BootX64.efi (AC & battery bypass)
UEFI_BASE_PATCHES = [
    {
        "name": "Power / AC Adapter Check",
        "offset": 0x911D1,
        "expected": bytes.fromhex("554889"),
        "replacement": bytes.fromhex("31c0c3"),
        "desc": "push rbp -> xor eax, eax; ret (Forces return value EFI_SUCCESS)",
    },
    {
        "name": "Primary Battery Charge Check",
        "offset": 0xE3FBC,
        "expected": bytes.fromhex("488bc4"),
        "replacement": bytes.fromhex("31c0c3"),
        "desc": "mov rax, rsp -> xor eax, eax; ret (Reports sufficient battery charge)",
    },
    {
        "name": "Battery Status Validation",
        "offset": 0x12D0E7,
        "expected": bytes.fromhex("e8dcff"),
        "replacement": bytes.fromhex("31c0c3"),
        "desc": "call ... -> xor eax, eax; ret (Bypasses battery presence validation)",
    },
]

# Platform bitmask bypass for BIOS downgrades (Step 1 & Step 3a)
UEFI_DOWNGRADE_PATCHES = [
    {
        "name": "Platform Bitmask Check (Anti-Mismatch Lock)",
        "offset": 0xD98CF,
        "expected": bytes.fromhex("7407"),
        "replacement": bytes.fromhex("eb07"),
        "desc": "je +7 -> jmp +7 (Bypasses 'system program file not correct' error)",
    },
]

# EC-Only Force-Flash patches (Step 2: thinkpad-ec update on BIOS 2.75 / EC 1.14)
UEFI_EC_ONLY_PATCHES = [
    {
        "name": "Disable BIOS Flash (EC-Only Mode)",
        "offset": 0xD74FA,
        "expected": bytes.fromhex("25"),
        "replacement": bytes.fromhex("35"),
        "desc": "Sets BIOS update flag to 0 (only EC is flashed)",
    },
    {
        "name": "Bypass EC Version Equality Check (Force-Flash)",
        "offset": 0xD9BCB,
        "expected": bytes.fromhex("663bce"),
        "replacement": bytes.fromhex("eb1390"),
        "desc": "cmp cx, si -> jmp +0x13; nop (Forces EC flash despite identical version 1.14)",
    },
]

# Patches for Legacy DOS flash utilities (DOSFLASH.EXE, TPCHKS.EXE, UPDTFLSH.EXE)
DOS_PATCHES = {
    "DOSFLASH.EXE": [
        {
            "name": "DOSFLASH Power Check Bypass",
            "offset": 0x2B902,
            "expected": bytes.fromhex("5589e5"),
            "replacement": bytes.fromhex("31c0c3"),
            "desc": "push ebp -> xor eax, eax; ret",
        }
    ],
    "TPCHKS.EXE": [
        {
            "name": "TPCHKS Battery Status Return 0",
            "offset": 0x1060,
            "expected": bytes.fromhex("8be88cc005"),
            "replacement": bytes.fromhex("b8004ccd21"),
            "desc": "mov ax, 0x4c00; int 0x21 (Immediate exit code 0 = OK)",
        }
    ],
    "UPDTFLSH.EXE": [
        {
            "name": "UPDTFLSH Jump Table Redirect 1",
            "offset": 0x1242,
            "expected": bytes.fromhex("c40ed80e"),
            "replacement": bytes.fromhex("cc10cc10"),
            "desc": "Jump table redirect to success branch",
        },
        {
            "name": "UPDTFLSH Jump Table Redirect 2",
            "offset": 0x1250,
            "expected": bytes.fromhex("140f"),
            "replacement": bytes.fromhex("cc10"),
            "desc": "Jump table redirect to success branch",
        },
    ],
}


def sha256_of(data: bytes) -> str:
    """Computes the SHA-256 hex digest of a byte buffer."""
    return hashlib.sha256(data).hexdigest()


def update_pe_header_and_checksum(pe_data: bytearray) -> None:
    """
    Clears the Authenticode security directory entry in the PE32+ header
    and recalculates the PE Optional Header CheckSum field dynamically via e_lfanew.
    """
    if len(pe_data) < 0x40 or pe_data[:2] != b"MZ":
        raise ValueError("Invalid DOS header (missing MZ signature)")
    e_lfanew = struct.unpack_from("<I", pe_data, 0x3C)[0]
    if e_lfanew + 24 + 152 > len(pe_data):
        raise ValueError(f"Invalid e_lfanew offset (0x{e_lfanew:X}) for file size {len(pe_data)}")
    if pe_data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise ValueError("Invalid PE header signature")
    opt_magic = struct.unpack_from("<H", pe_data, e_lfanew + 24)[0]
    if opt_magic != 0x020B:
        raise ValueError(f"Expected PE32+ (0x020B), found 0x{opt_magic:04X}")

    checksum_offset = e_lfanew + 24 + 64       # OptionalHeader.CheckSum (0x120 when e_lfanew=0xC8)
    security_dir_offset = e_lfanew + 24 + 144  # DataDirectory[4] Security (0x170 when e_lfanew=0xC8)

    pe_data[security_dir_offset : security_dir_offset + 8] = b"\x00" * 8
    pe_data[checksum_offset : checksum_offset + 4] = b"\x00\x00\x00\x00"
    csum = 0
    length = len(pe_data)
    for i in range(0, length, 2):
        val = pe_data[i] + (pe_data[i + 1] << 8) if i + 1 < length else pe_data[i]
        csum += val
        csum = (csum & 0xFFFF) + (csum >> 16)
    csum = (csum & 0xFFFF) + (csum >> 16)
    csum += length
    struct.pack_into("<I", pe_data, checksum_offset, csum)


def apply_patch_list(buf: bytearray, base_offset: int, patches: list) -> tuple[bool, int]:
    """Verifies and applies a list of binary patches relative to base_offset."""
    for p in patches:
        off = base_offset + p["offset"]
        length = len(p["expected"])
        actual = bytes(buf[off : off + length])
        if actual == p["replacement"]:
            print(f"  [i] '{p['name']}' (0x{p['offset']:X}) is ALREADY patched.")
        elif actual == p["expected"]:
            print(f"  [+] Checkpoint '{p['name']}' (0x{p['offset']:X}): OK")
        else:
            print(f"  [!] ERROR at offset 0x{p['offset']:X} ('{p['name']}'):")
            print(f"      Expected: {p['expected'].hex()} | Found: {actual.hex()}")
            return False, 0

    applied = 0
    for p in patches:
        off = base_offset + p["offset"]
        length = len(p["expected"])
        if buf[off : off + length] == p["expected"]:
            buf[off : off + length] = p["replacement"]
            applied += 1
            print(f"  [✓] Patched: 0x{p['offset']:X} -> {p['replacement'].hex()} ({p['desc']})")
    return True, applied


def patch_file(
    input_path: str,
    output_path: str | None = None,
    ec_only: bool = False,
    inject_bios_path: str | None = None,
) -> bool:
    """
    Automatically detects whether the input is a 32 MB El Torito boot image (.img),
    a UEFI bootloader (.efi), or a DOS flash utility (.exe), and applies all relevant patches.
    Optionally replaces the embedded $01D3000.FL1 in-place when inject_bios_path is provided.
    """
    if not os.path.isfile(input_path):
        print(f"[!] ERROR: File not found: {input_path}")
        return False

    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    filename = os.path.basename(input_path).upper()
    uefi_patches = UEFI_BASE_PATCHES + (UEFI_EC_ONLY_PATCHES if ec_only else UEFI_DOWNGRADE_PATCHES)
    mode_str = "EC-Only Force-Flash + Battery Bypass" if ec_only else "BIOS Downgrade + Battery Bypass"

    print(f"[*] File: {input_path} ({len(data):,} bytes)")
    print(f"[*] Mode: {mode_str}")
    print(f"[*] Original SHA-256: {sha256_of(data)}")
    print("-" * 70)

    total_applied = 0

    # Case 1: Complete 32 MB El Torito Boot Image (.img)
    if len(data) == 33554432 or filename.endswith(".IMG"):
        print("[*] Detected type: 32 MB Bootable El Torito FAT16 Image (.img)")
        efi_bases, efi_len = IMG_FILE_OFFSETS["BootX64.efi"]
        efi_base = efi_bases[0]

        if len(data) < efi_base + efi_len:
            print(f"[!] ERROR: Image too small ({len(data):,} bytes) for embedded BootX64.efi.")
            return False

        if data[efi_base : efi_base + 2] == b"MZ":
            print(f"\n==> Patching embedded EFI/Boot/BootX64.efi (at image offset 0x{efi_base:X}):")
            ok, count = apply_patch_list(data, efi_base, uefi_patches)
            if not ok:
                return False
            total_applied += count
            efi_slice = bytearray(data[efi_base : efi_base + efi_len])
            update_pe_header_and_checksum(efi_slice)
            data[efi_base : efi_base + efi_len] = efi_slice
            print("  [✓] UEFI PE header Security Directory cleared & CheckSum updated.")
        else:
            print("[!] ERROR: BootX64.efi not found at standard image offset 0x1C2600.")
            return False

        for dos_name, patches in DOS_PATCHES.items():
            dos_bases, _ = IMG_FILE_OFFSETS[dos_name]
            first_patch = patches[0]
            for cand_base in dos_bases:
                chk_off = cand_base + first_patch["offset"]
                chk_len = len(first_patch["expected"])
                if data[cand_base : cand_base + 2] == b"MZ" and data[chk_off : chk_off + chk_len] in (
                    first_patch["expected"],
                    first_patch["replacement"],
                ):
                    print(f"\n==> Patching embedded FLASH/{dos_name} (at image offset 0x{cand_base:X}):")
                    ok, count = apply_patch_list(data, cand_base, patches)
                    if not ok:
                        return False
                    total_applied += count
                    break

        if inject_bios_path:
            if not os.path.isfile(inject_bios_path):
                print(f"[!] ERROR: BIOS file to inject not found: {inject_bios_path}")
                return False
            with open(inject_bios_path, "rb") as bf:
                bios_data = bf.read()
            fl1_bases, fl1_len = IMG_FILE_OFFSETS["$01D3000.FL1"]
            fl1_base = fl1_bases[0]
            if len(bios_data) != fl1_len:
                print(f"[!] ERROR: Invalid FL1 file size ({len(bios_data)} instead of {fl1_len} bytes).")
                return False
            data[fl1_base : fl1_base + fl1_len] = bios_data
            total_applied += 1
            print(f"\n==> Injecting BIOS file '{inject_bios_path}' into FLASH/G2ETB5WW/$01D3000.FL1 (0x{fl1_base:X}):")
            print(f"  [✓] {fl1_len:,} bytes replaced in-place (SHA-256: {sha256_of(bios_data)[:16]}...).")

    # Case 2: Standalone DOS flash utility (.exe)
    elif filename in DOS_PATCHES:
        if inject_bios_path:
            print("[!] ERROR: --inject-bios is only supported for 32 MB .img files.")
            return False
        print(f"[*] Detected type: Legacy DOS Flash Utility ({filename})")
        ok, total_applied = apply_patch_list(data, 0, DOS_PATCHES[filename])
        if not ok:
            return False

    # Case 3: Standalone UEFI BootX64.efi binary
    elif filename.endswith(".EFI") or len(data) in (1252016, 1250368):
        if inject_bios_path:
            print("[!] ERROR: --inject-bios is only supported for 32 MB .img files.")
            return False
        print("[*] Detected type: 64-bit UEFI Bootloader (BootX64.efi)")
        ok, total_applied = apply_patch_list(data, 0, uefi_patches)
        if not ok:
            return False
        if len(data) == 1252016:
            del data[1250368:]
        update_pe_header_and_checksum(data)
        print("  [✓] UEFI PE header Security Directory cleared & CheckSum updated.")

    else:
        print(f"[!] ERROR: Unknown file type or unexpected file size ({len(data)} bytes).")
        return False

    print("-" * 70)
    print(f"[*] Total of {total_applied} patch(es) applied.")
    print(f"[*] New SHA-256: {sha256_of(data)}")

    target_path = input_path if (output_path is None or output_path == input_path) else output_path
    target_dir = os.path.dirname(os.path.abspath(target_path)) or "."
    src_mode = stat.S_IMODE(os.stat(input_path).st_mode)
    fd, tmp_path = tempfile.mkstemp(prefix=".patch_tmp_", dir=target_dir)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, src_mode)
        os.replace(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"[✓] Successfully saved to: {target_path}\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="ThinkPad X230 BIOS/EC Battery Bypass & Force-Flash Patcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input_file",
        help="Path to bios_2.75.img, patched.x230.img, BootX64.efi, or DOS .EXE",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default=None,
        help="Optional output path (default: overwrites input_file in-place)",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--ec-only",
        action="store_true",
        help="Enable EC-Only Force-Flash mode (for Step 2: thinkpad-ec)",
    )
    mode_group.add_argument(
        "--inject-bios",
        metavar="FL1_FILE",
        default=None,
        help="Replace the embedded $01D3000.FL1 inside a 32 MB .img with the specified BIOS file (e.g. build/X230.FL1 for Step 3a)",
    )

    args = parser.parse_args()
    success = patch_file(
        args.input_file,
        args.output_file,
        ec_only=args.ec_only,
        inject_bios_path=args.inject_bios,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
