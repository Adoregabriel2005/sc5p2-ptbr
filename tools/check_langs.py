"""Check all CAP files in the CVM and read samples from each language."""
import struct
import os

GAME_DIR = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
cvm_path = os.path.join(GAME_DIR, "ch52_g.cvm")


def parse_dir(f, iso_base, sector, size, prefix=""):
    entries = []
    f.seek(iso_base + sector * 2048)
    data = f.read(size)
    offset = 0
    while offset < len(data):
        rec_len = data[offset]
        if rec_len == 0:
            offset = ((offset // 2048) + 1) * 2048
            if offset >= len(data):
                break
            continue
        extent = struct.unpack('<I', data[offset+2:offset+6])[0]
        data_len = struct.unpack('<I', data[offset+10:offset+14])[0]
        flags = data[offset + 25]
        name_len = data[offset + 32]
        name_raw = data[offset+33:offset+33+name_len]
        is_dir = bool(flags & 0x02)
        if name_raw not in (b'\x00', b'\x01'):
            name_str = name_raw.decode('ascii', errors='replace').split(';')[0]
            full_path = prefix + name_str
            entries.append({
                'name': name_str, 'path': full_path,
                'sector': extent, 'size': data_len, 'is_dir': is_dir
            })
            if is_dir:
                sub = parse_dir(f, iso_base, extent, data_len, full_path + '/')
                entries.extend(sub)
        offset += rec_len
    return entries


def parse_dgcp(data):
    if data[:4] != b'DGCP':
        return None
    count = struct.unpack('<I', data[4:8])[0]
    entries = []
    for i in range(count):
        off = 16 + i * 8
        line_count = struct.unpack('<I', data[off:off+4])[0]
        ptr_offset = struct.unpack('<I', data[off+4:off+8])[0]
        lines = []
        for j in range(line_count):
            str_ptr_off = ptr_offset + j * 4
            str_offset = struct.unpack('<I', data[str_ptr_off:str_ptr_off+4])[0]
            end = data.find(b'\x00', str_offset)
            if end == -1:
                end = len(data)
            text = data[str_offset:end].decode('latin-1', errors='replace')
            lines.append(text)
        entries.append(lines)
    return entries


with open(cvm_path, 'rb') as f:
    f.seek(0)
    search_data = f.read(1024 * 1024)
    pvd_offset = search_data.find(b'\x01CD001')
    iso_base = pvd_offset - 16 * 2048
    pvd = search_data[pvd_offset:pvd_offset + 2048]
    root_record = pvd[156:190]
    root_loc = struct.unpack('<I', root_record[2:6])[0]
    root_size = struct.unpack('<I', root_record[10:14])[0]

    entries = parse_dir(f, iso_base, root_loc, root_size)

    # List ALL CAP files
    cap_files = [e for e in entries if 'CAP' in e['name'].upper() and e['name'].upper().endswith('.BIN')]
    cap_files.sort(key=lambda x: x['name'])

    print("=== ALL CAP files in ch52_g.cvm ===")
    for e in cap_files:
        print(f"  {e['name']:25s}  sector={e['sector']:8d}  size={e['size']:8d}")
    print(f"\nTotal CAP files: {len(cap_files)}")

    # Now read the FIRST entry from TITCAP in each language to compare
    print("\n=== TITCAP content comparison ===")
    titcap_files = [e for e in cap_files if 'TITCAP' in e['name'].upper()]
    for tc in sorted(titcap_files, key=lambda x: x['name']):
        f.seek(iso_base + tc['sector'] * 2048)
        data = f.read(tc['size'])
        parsed = parse_dgcp(data)
        if parsed:
            first_lines = parsed[0] if parsed else ["(empty)"]
            print(f"\n  {tc['name']}:")
            for i, entry in enumerate(parsed[:3]):
                for line in entry:
                    print(f"    [{i}] {line}")

    # Check R01CAP files too
    print("\n=== R01CAP content comparison ===")
    r01cap_files = [e for e in cap_files if 'R01CAP' in e['name'].upper()]
    for rc in sorted(r01cap_files, key=lambda x: x['name']):
        f.seek(iso_base + rc['sector'] * 2048)
        data = f.read(rc['size'])
        parsed = parse_dgcp(data)
        if parsed:
            print(f"\n  {rc['name']}:")
            for i, entry in enumerate(parsed[:2]):
                for line in entry:
                    print(f"    [{i}] {line}")

    # Non-CAP BIN files
    print("\n=== Non-CAP BIN files ===")
    other_bins = [e for e in entries if e['name'].upper().endswith('.BIN') and 'CAP' not in e['name'].upper() and not e['is_dir']]
    for e in sorted(other_bins, key=lambda x: x['name']):
        print(f"  {e['name']:25s}  size={e['size']:8d}")

    # All non-dir files
    print("\n=== ALL files in CVM ===")
    all_files = [e for e in entries if not e['is_dir']]
    for e in sorted(all_files, key=lambda x: x['name']):
        print(f"  {e['name']:30s}  size={e['size']:10d}")
