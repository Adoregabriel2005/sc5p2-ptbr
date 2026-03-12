"""
AFS Container Parser + CTL_TEXT analyzer for Space Channel 5 Part 2
"""
import struct
import os
import sys


def parse_afs(filepath):
    """Parse an AFS file and return list of contained files."""
    data = open(filepath, 'rb').read()
    
    magic = data[0:4]
    if magic != b'AFS\x00':
        print(f"Not AFS: {magic}")
        return []
    
    count = struct.unpack('<I', data[4:8])[0]
    
    entries = []
    for i in range(count):
        off = struct.unpack('<I', data[8 + i*8:12 + i*8])[0]
        size = struct.unpack('<I', data[12 + i*8:16 + i*8])[0]
        entries.append({'index': i, 'offset': off, 'size': size})
    
    return entries, data


def extract_afs_entries(filepath, output_dir):
    """Extract all files from an AFS container."""
    entries, data = parse_afs(filepath)
    os.makedirs(output_dir, exist_ok=True)
    
    for e in entries:
        outpath = os.path.join(output_dir, f"file_{e['index']:04d}.bin")
        chunk = data[e['offset']:e['offset']+e['size']]
        with open(outpath, 'wb') as f:
            f.write(chunk)
    
    return entries


def check_dgcp_in_afs(filepath):
    """Check if AFS entries contain DGCP text data."""
    entries, data = parse_afs(filepath)
    print(f"AFS: {os.path.basename(filepath)}, {len(entries)} entries")
    
    dgcp_count = 0
    for e in entries:
        chunk = data[e['offset']:e['offset']+min(4, e['size'])]
        if chunk == b'DGCP':
            dgcp_count += 1
    
    print(f"DGCP entries: {dgcp_count}")
    
    # Show first few entries' content type
    for e in entries[:10]:
        if e['size'] == 0:
            continue
        chunk = data[e['offset']:e['offset']+min(64, e['size'])]
        magic = chunk[:4]
        # Try to read as text
        printable = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk[:60])
        print(f"  [{e['index']:3d}] off=0x{e['offset']:08X} size={e['size']:6d} magic={magic} text={printable}")
    
    # Look for any with readable text
    print("\n--- Entries with readable text ---")
    for e in entries:
        if e['size'] < 4:
            continue
        chunk = data[e['offset']:e['offset']+e['size']]
        # Check if it looks like text (high ratio of printable chars)
        printable_count = sum(1 for b in chunk if 32 <= b <= 126 or b == 10 or b == 13)
        ratio = printable_count / len(chunk) if len(chunk) > 0 else 0
        if ratio > 0.5 and e['size'] > 20:
            text = chunk.decode('latin-1', errors='replace')
            preview = text[:100].replace('\n', '\\n').replace('\r', '\\r')
            print(f"  [{e['index']:3d}] size={e['size']:6d} ratio={ratio:.2f}: {preview}")


if __name__ == '__main__':
    # Check CTL_TEXT.AFS from both CVMs
    for d in ['ch52_g', 'ch52_g50']:
        path = os.path.join(r"C:\Users\gorigamia\Desktop\game\extracted", d, "CTL_TEXT.AFS")
        if os.path.exists(path):
            check_dgcp_in_afs(path)
            print()
