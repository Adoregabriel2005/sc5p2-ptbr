"""
Build a PS2-compatible ISO 9660 image from game files.
Pure Python - no external dependencies.
Produces a clean ISO 9660 Level 1 disc readable by PS2 IOP cdvdman.
"""
import os
import sys
import struct

SECTOR = 2048
GAME_DIR = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
OUTPUT_ISO = r"C:\Users\gorigamia\Desktop\game\build\SC5P2_PTBR.iso"


# ── Encoding helpers ──────────────────────────────────────────────

def both16(v):
    return struct.pack('<H', v) + struct.pack('>H', v)

def both32(v):
    return struct.pack('<I', v) + struct.pack('>I', v)

def pad_str(s, n):
    return s.encode('ascii')[:n].ljust(n, b'\x20')

def dir_dt():
    """7-byte directory record datetime."""
    return bytes([126, 3, 12, 0, 0, 0, 0])  # 2026-03-12 00:00:00 GMT

def pvd_dt():
    """17-byte PVD datetime."""
    return b'2026031200000000\x00'

def sectors_for(size):
    return max(1, (size + SECTOR - 1) // SECTOR)


# ── Directory Record ──────────────────────────────────────────────

def dir_rec(ident, lba, size, is_dir):
    """Build one ISO 9660 directory record."""
    if isinstance(ident, str):
        ident = ident.encode('ascii')
    n = len(ident)
    rec_len = 33 + n
    if rec_len % 2:
        rec_len += 1
    r = bytearray(rec_len)
    r[0] = rec_len
    struct.pack_into('<I', r, 2, lba)
    struct.pack_into('>I', r, 6, lba)
    struct.pack_into('<I', r, 10, size)
    struct.pack_into('>I', r, 14, size)
    r[18:25] = dir_dt()
    r[25] = 0x02 if is_dir else 0x00
    struct.pack_into('<H', r, 28, 1)
    struct.pack_into('>H', r, 30, 1)
    r[32] = n
    r[33:33 + n] = ident
    return bytes(r)


# ── Directory Builder ─────────────────────────────────────────────

def build_dir(self_lba, self_size, parent_lba, parent_size, entries):
    """
    Build directory sector data.
    entries: sorted list of (ident_bytes, lba, size, is_dir)
    """
    data = bytearray()
    data += dir_rec(b'\x00', self_lba, self_size, True)
    data += dir_rec(b'\x01', parent_lba, parent_size, True)
    for ident, lba, sz, is_d in entries:
        rec = dir_rec(ident, lba, sz, is_d)
        off = len(data) % SECTOR
        if off + len(rec) > SECTOR:
            data += b'\x00' * (SECTOR - off)
        data += rec
    rem = len(data) % SECTOR
    if rem:
        data += b'\x00' * (SECTOR - rem)
    return bytes(data)


# ── Path Table ────────────────────────────────────────────────────

def build_path_table(dirs, big_endian=False):
    """dirs: list of (name_bytes, lba, parent_1based)"""
    data = bytearray()
    for name, lba, parent in dirs:
        n = len(name)
        data += struct.pack('B', n)
        data += struct.pack('B', 0)
        if big_endian:
            data += struct.pack('>I', lba)
            data += struct.pack('>H', parent)
        else:
            data += struct.pack('<I', lba)
            data += struct.pack('<H', parent)
        data += name
        if n % 2:
            data += b'\x00'
    return bytes(data)


# ── PVD / VDST ────────────────────────────────────────────────────

def build_pvd(vol_sectors, root_lba, root_size, pt_size, pt_l_lba, pt_m_lba):
    p = bytearray(SECTOR)
    p[0] = 1
    p[1:6] = b'CD001'
    p[6] = 1
    p[8:40] = pad_str('PLAYSTATION', 32)
    p[40:72] = pad_str('SCES_50612', 32)
    p[80:88] = both32(vol_sectors)
    p[120:124] = both16(1)
    p[124:128] = both16(1)
    p[128:132] = both16(SECTOR)
    p[132:140] = both32(pt_size)
    struct.pack_into('<I', p, 140, pt_l_lba)
    struct.pack_into('<I', p, 144, 0)
    struct.pack_into('>I', p, 148, pt_m_lba)
    struct.pack_into('>I', p, 152, 0)
    p[156:190] = dir_rec(b'\x00', root_lba, root_size, True)[:34]
    p[574:702] = pad_str('PLAYSTATION', 128)
    p[813:830] = pvd_dt()
    p[830:847] = pvd_dt()
    p[847:864] = b'0000000000000000\x00'
    p[864:881] = pvd_dt()
    p[881] = 1
    return bytes(p)

def build_vdst():
    v = bytearray(SECTOR)
    v[0] = 255
    v[1:6] = b'CD001'
    v[6] = 1
    return bytes(v)


# ── Main ──────────────────────────────────────────────────────────

def build_iso():
    print("=== Building PS2 ISO (pure ISO 9660) ===")
    print(f"Source: {GAME_DIR}")
    print(f"Output: {OUTPUT_ISO}\n")

    # Collect files
    root_files = []
    drv_files = []
    for item in sorted(os.listdir(GAME_DIR)):
        full = os.path.join(GAME_DIR, item)
        if os.path.isfile(full):
            root_files.append((item.upper(), full, os.path.getsize(full)))
        elif os.path.isdir(full) and item.lower() == 'drivers':
            for f in sorted(os.listdir(full)):
                fp = os.path.join(full, f)
                if os.path.isfile(fp):
                    drv_files.append((f.upper(), fp, os.path.getsize(fp)))

    root_files.sort(key=lambda x: x[0])
    drv_files.sort(key=lambda x: x[0])

    # Layout plan
    # 0-15  : System Area
    # 16    : PVD
    # 17    : VDST
    # 18    : L-Path Table
    # 19    : M-Path Table
    # 20-21 : Root directory  (2 sectors)
    # 22-23 : drivers/ dir    (2 sectors)
    # 24+   : File data

    ROOT_DIR_LBA = 20
    ROOT_DIR_SEC = 2
    DRV_DIR_LBA = 22
    DRV_DIR_SEC = 2
    next_lba = 24

    root_dir_size = ROOT_DIR_SEC * SECTOR
    drv_dir_size = DRV_DIR_SEC * SECTOR

    # Assign LBAs
    file_map = {}  # full_path -> (lba, size)
    for name, path, size in root_files:
        file_map[path] = (next_lba, size)
        s = sectors_for(size)
        print(f"  {name}: LBA {next_lba}, {size:,} bytes ({s} sectors)")
        next_lba += s

    for name, path, size in drv_files:
        file_map[path] = (next_lba, size)
        s = sectors_for(size)
        print(f"  DRIVERS/{name}: LBA {next_lba}, {size:,} bytes ({s} sectors)")
        next_lba += s

    total_sectors = next_lba
    print(f"\nTotal: {total_sectors} sectors ({total_sectors * SECTOR / (1024**3):.2f} GB)")

    # Build root directory entries
    root_entries = []
    root_entries.append((b'DRIVERS', DRV_DIR_LBA, drv_dir_size, True))
    for name, path, size in root_files:
        root_entries.append(((name + ';1').encode('ascii'), file_map[path][0], size, False))
    root_entries.sort(key=lambda x: x[0])

    root_dir_data = build_dir(ROOT_DIR_LBA, root_dir_size, ROOT_DIR_LBA, root_dir_size, root_entries)
    if len(root_dir_data) > root_dir_size:
        print(f"ERROR: Root dir needs {len(root_dir_data)} bytes, only {root_dir_size} allocated")
        sys.exit(1)
    root_dir_data = root_dir_data[:root_dir_size]

    # Build drivers directory entries
    drv_entries = []
    for name, path, size in drv_files:
        drv_entries.append(((name + ';1').encode('ascii'), file_map[path][0], size, False))
    drv_entries.sort(key=lambda x: x[0])

    drv_dir_data = build_dir(DRV_DIR_LBA, drv_dir_size, ROOT_DIR_LBA, root_dir_size, drv_entries)
    if len(drv_dir_data) > drv_dir_size:
        print(f"ERROR: Drivers dir needs {len(drv_dir_data)} bytes, only {drv_dir_size} allocated")
        sys.exit(1)
    drv_dir_data = drv_dir_data[:drv_dir_size]

    # Path table
    pt_dirs = [
        (b'\x01', ROOT_DIR_LBA, 1),
        (b'DRIVERS', DRV_DIR_LBA, 1),
    ]
    pt_l = build_path_table(pt_dirs, big_endian=False)
    pt_m = build_path_table(pt_dirs, big_endian=True)

    pvd = build_pvd(total_sectors, ROOT_DIR_LBA, root_dir_size, len(pt_l), 18, 19)
    vdst = build_vdst()

    # Write ISO
    os.makedirs(os.path.dirname(OUTPUT_ISO), exist_ok=True)
    print(f"\nWriting ISO...")

    with open(OUTPUT_ISO, 'wb') as f:
        # System area (16 sectors of zeros)
        f.write(b'\x00' * (16 * SECTOR))
        # PVD
        f.write(pvd)
        # VDST
        f.write(vdst)
        # Path tables
        f.write(pt_l.ljust(SECTOR, b'\x00'))
        f.write(pt_m.ljust(SECTOR, b'\x00'))
        # Root directory
        f.write(root_dir_data)
        # Drivers directory
        f.write(drv_dir_data)

        # File data
        for name, path, size in root_files:
            lba = file_map[path][0]
            f.seek(lba * SECTOR)
            with open(path, 'rb') as src:
                rem = size
                while rem > 0:
                    chunk = src.read(min(rem, 1024 * 1024))
                    if not chunk:
                        break
                    f.write(chunk)
                    rem -= len(chunk)
            pad = (SECTOR - size % SECTOR) % SECTOR
            if pad:
                f.write(b'\x00' * pad)

        for name, path, size in drv_files:
            lba = file_map[path][0]
            f.seek(lba * SECTOR)
            with open(path, 'rb') as src:
                rem = size
                while rem > 0:
                    chunk = src.read(min(rem, 1024 * 1024))
                    if not chunk:
                        break
                    f.write(chunk)
                    rem -= len(chunk)
            pad = (SECTOR - size % SECTOR) % SECTOR
            if pad:
                f.write(b'\x00' * pad)

        # Ensure correct final size
        f.seek(total_sectors * SECTOR - 1)
        f.write(b'\x00')

    final = os.path.getsize(OUTPUT_ISO)
    print(f"ISO created: {final:,} bytes ({final / (1024**3):.2f} GB)")
    print("Done!")


if __name__ == '__main__':
    build_iso()
