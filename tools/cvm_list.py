"""
CVM File Listing Tool for Space Channel 5 Part 2
Lists all files inside a Sega CVM container (ISO 9660 based)
"""
import struct
import sys
import os

def parse_directory(f, iso_base, sector, size, prefix=""):
    """Parse an ISO 9660 directory and return list of entries."""
    entries = []
    offset = 0
    f.seek(iso_base + sector * 2048)
    data = f.read(size)
    
    while offset < len(data):
        rec_len = data[offset]
        if rec_len == 0:
            # Move to next sector boundary
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
        
        if name_raw == b'\x00':
            name_str = '.'
        elif name_raw == b'\x01':
            name_str = '..'
        else:
            name_str = name_raw.decode('ascii', errors='replace').split(';')[0]
        
        if name_str not in ('.', '..'):
            full_path = prefix + name_str
            entries.append({
                'name': name_str,
                'path': full_path,
                'sector': extent,
                'size': data_len,
                'is_dir': is_dir,
            })
            
            if is_dir:
                sub_entries = parse_directory(f, iso_base, extent, data_len, full_path + '/')
                entries.extend(sub_entries)
        
        offset += rec_len
    
    return entries


def list_cvm(cvm_path):
    """List all files in a CVM container."""
    print(f"=== CVM: {os.path.basename(cvm_path)} ===")
    print(f"Size: {os.path.getsize(cvm_path):,} bytes")
    print()
    
    with open(cvm_path, 'rb') as f:
        # Read CVM header
        header = f.read(4)
        if header != b'CVMH':
            print("ERROR: Not a valid CVM file!")
            return []
        
        # Find ISO 9660 PVD (search for CD001)
        f.seek(0)
        search_data = f.read(1024 * 1024)
        pvd_offset = search_data.find(b'\x01CD001')
        if pvd_offset == -1:
            print("ERROR: Cannot find ISO 9660 PVD!")
            return []
        
        print(f"PVD found at offset: 0x{pvd_offset:X}")
        
        # ISO base = PVD offset - 16 * 2048
        iso_base = pvd_offset - 16 * 2048
        print(f"ISO base offset: 0x{iso_base:X}")
        
        # Parse PVD
        pvd = search_data[pvd_offset:pvd_offset+2048]
        vol_id = pvd[40:72].decode('ascii', errors='replace').strip()
        vol_space = struct.unpack('<I', pvd[80:84])[0]
        print(f"Volume ID: {vol_id}")
        print(f"Volume Space: {vol_space} sectors ({vol_space * 2048:,} bytes)")
        
        # Root directory
        root_record = pvd[156:190]
        root_loc = struct.unpack('<I', root_record[2:6])[0]
        root_size = struct.unpack('<I', root_record[10:14])[0]
        print(f"Root dir: sector {root_loc}, size {root_size}")
        print()
        
        # List all files recursively
        entries = parse_directory(f, iso_base, root_loc, root_size)
        
        print(f"{'TYPE':5} {'SIZE':>12} {'SECTOR':>8} {'PATH'}")
        print("-" * 80)
        for e in entries:
            t = "DIR" if e['is_dir'] else "FILE"
            print(f"{t:5} {e['size']:>12,} {e['sector']:>8} {e['path']}")
        
        print()
        print(f"Total entries: {len(entries)}")
        return entries


if __name__ == '__main__':
    game_dir = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
    
    for cvm_name in ['ch52_g.cvm', 'ch52_g50.cvm']:
        cvm_path = os.path.join(game_dir, cvm_name)
        if os.path.exists(cvm_path):
            entries = list_cvm(cvm_path)
            print("\n" + "=" * 80 + "\n")
