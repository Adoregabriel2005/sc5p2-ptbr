"""
CVM File Extractor for Space Channel 5 Part 2
Extracts files from Sega CVM containers (ISO 9660 based)
"""
import struct
import os
import sys


def parse_directory(f, iso_base, sector, size, prefix=""):
    """Parse an ISO 9660 directory and return list of entries."""
    entries = []
    offset = 0
    f.seek(iso_base + sector * 2048)
    data = f.read(size)

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


def get_iso_base(f):
    """Find the ISO 9660 base offset inside a CVM file."""
    f.seek(0)
    search_data = f.read(1024 * 1024)
    pvd_offset = search_data.find(b'\x01CD001')
    if pvd_offset == -1:
        raise ValueError("Cannot find ISO 9660 PVD")
    iso_base = pvd_offset - 16 * 2048
    return iso_base, pvd_offset


def get_root_info(f, pvd_offset):
    """Get root directory info from PVD."""
    f.seek(pvd_offset)
    pvd = f.read(2048)
    root_record = pvd[156:190]
    root_loc = struct.unpack('<I', root_record[2:6])[0]
    root_size = struct.unpack('<I', root_record[10:14])[0]
    return root_loc, root_size


def extract_file(f, iso_base, entry, output_path):
    """Extract a single file from the CVM."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    f.seek(iso_base + entry['sector'] * 2048)
    data = f.read(entry['size'])
    with open(output_path, 'wb') as out:
        out.write(data)


def extract_cvm(cvm_path, output_dir, filter_func=None):
    """Extract files from CVM to output directory.
    
    Args:
        cvm_path: Path to CVM file
        output_dir: Where to extract
        filter_func: Optional function(entry) -> bool to filter which files to extract
    
    Returns:
        List of extracted entries
    """
    extracted = []
    
    with open(cvm_path, 'rb') as f:
        header = f.read(4)
        if header != b'CVMH':
            raise ValueError(f"Not a valid CVM file: {cvm_path}")
        
        iso_base, pvd_offset = get_iso_base(f)
        root_loc, root_size = get_root_info(f, pvd_offset)
        entries = parse_directory(f, iso_base, root_loc, root_size)
        
        for entry in entries:
            if entry['is_dir']:
                continue
            if filter_func and not filter_func(entry):
                continue
            
            output_path = os.path.join(output_dir, entry['path'])
            extract_file(f, iso_base, entry, output_path)
            extracted.append(entry)
            print(f"  Extracted: {entry['path']} ({entry['size']:,} bytes)")
    
    return extracted


def inject_file(cvm_path, iso_base, entry, new_data):
    """Inject modified data back into a CVM file at the file's sector location.
    
    WARNING: new_data must be <= original file size to avoid corrupting the filesystem.
    """
    if len(new_data) > entry['size']:
        raise ValueError(
            f"New data ({len(new_data)} bytes) is larger than original ({entry['size']} bytes). "
            "Cannot inject without corrupting filesystem."
        )
    
    with open(cvm_path, 'r+b') as f:
        offset = iso_base + entry['sector'] * 2048
        f.seek(offset)
        # Pad with zeros to match original size
        padded = new_data + b'\x00' * (entry['size'] - len(new_data))
        f.write(padded)


if __name__ == '__main__':
    game_dir = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
    output_dir = r"C:\Users\gorigamia\Desktop\game\extracted"
    
    # Extract only text-related files (CAP, TIM, etc.)
    def text_filter(entry):
        name = entry['name'].upper()
        return (name.endswith('.BIN') and ('CAP' in name or 'TIM' in name)) or \
               name == 'CTL_TEXT.AFS'
    
    for cvm_name in ['ch52_g.cvm', 'ch52_g50.cvm']:
        cvm_path = os.path.join(game_dir, cvm_name)
        if os.path.exists(cvm_path):
            cvm_out = os.path.join(output_dir, cvm_name.replace('.cvm', ''))
            print(f"\n=== Extracting text files from {cvm_name} ===")
            entries = extract_cvm(cvm_path, cvm_out, text_filter)
            print(f"  Total: {len(entries)} files extracted")
