#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE="$REPO_ROOT/build/bios_2.75.img"
TARGET="${1:-}"

if [ ! -f "$IMAGE" ]; then
    echo "Error: $IMAGE not found!" >&2
    exit 1
fi

if [ -z "$TARGET" ]; then
    echo "Available block devices:"
    lsblk -d -o NAME,SIZE,TYPE,MODEL,TRAN
    echo ""
    read -rp "Enter target USB drive (e.g. /dev/sdb): " TARGET
fi

if [ ! -b "$TARGET" ]; then
    echo "Error: '$TARGET' is not a valid block device!" >&2
    exit 1
fi

if [ "$(lsblk -dn -o TYPE "$TARGET" 2>/dev/null | head -n1 || true)" != "disk" ]; then
    echo "Error: '$TARGET' is not a whole disk device (e.g. use /dev/sdb, not /dev/sdb1)!" >&2
    exit 1
fi

# Safety check 1: Refuse to touch any backing disk of '/' (handles partitions, LUKS, LVM)
TARGET_REAL="$(readlink -f "$TARGET")"
ROOT_SRC="$(findmnt -n -o SOURCE --nofsroot / 2>/dev/null || findmnt -n -o SOURCE / 2>/dev/null || true)"
ROOT_SRC="${ROOT_SRC%%\[*\]}"
if [ -n "$ROOT_SRC" ]; then
    while IFS= read -r backing_disk; do
        if [ -n "$backing_disk" ] && [ "$TARGET_REAL" = "$backing_disk" ]; then
            echo "ERROR: Target device $TARGET is an active root disk! Aborting." >&2
            exit 1
        fi
    done < <(lsblk -s -no PATH,TYPE "$ROOT_SRC" 2>/dev/null | awk '$2=="disk"{print $1}' || true)
fi

# Safety check 2: Refuse if any partition on TARGET is mounted on a system path or swap
if ! MOUNT_LIST="$(lsblk -no MOUNTPOINTS "$TARGET" 2>/dev/null)"; then
    MOUNT_LIST="$(lsblk -no MOUNTPOINT "$TARGET")"
fi
if printf '%s\n' "$MOUNT_LIST" | grep -Eq '^(/$|/boot(/|$)|/efi(/|$)|/home(/|$)|/root(/|$)|/var(/|$)|/usr(/|$)|\[SWAP\]$)'; then
    echo "ERROR: Target device $TARGET contains active system mounts! Aborting." >&2
    exit 1
fi

# Safety check 3: Warn if target does not report as a removable USB device
TRAN="$(lsblk -dn -o TRAN "$TARGET" 2>/dev/null | head -n1 || true)"
RM="$(lsblk -dn -o RM "$TARGET" 2>/dev/null | head -n1 || true)"
if [ "$TRAN" != "usb" ] && [ "$RM" != "1" ]; then
    echo "WARNING: $TARGET does not appear to be a removable USB drive (TRAN='${TRAN:-unknown}', RM='${RM:-unknown}')!" >&2
fi

echo ""
echo "Selected target device:"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS "$TARGET" 2>/dev/null || lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT "$TARGET"
echo ""
echo "WARNING: All data on $TARGET will be permanently overwritten!"
read -rp "Write BIOS downgrade image to $TARGET? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[yYjJ]$ ]]; then
    echo "Aborted by user."
    exit 0
fi

echo "==> Unmounting any mounted partitions on $TARGET..."
mapfile -t PARTS < <(lsblk -ln -o PATH "$TARGET" | tail -n +2)
for part in "${PARTS[@]}"; do
    [ -n "$part" ] || continue
    udisksctl unmount -b "$part" 2>/dev/null || sudo umount "$part" 2>/dev/null || true
done

echo "==> Writing BIOS downgrade image to $TARGET..."
sudo dd if="$IMAGE" of="$TARGET" bs=4M status=progress conv=fsync

echo ""
echo "==> SUCCESS! USB flash drive is ready for BIOS downgrade."
