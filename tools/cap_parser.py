"""
DGCP CAP File Parser - Analyzes the text format of Space Channel 5 Part 2 CAP files
"""
import struct
import sys
import os


def parse_dgcp(filepath):
    """Parse a DGCP CAP file and return all text entries."""
    data = open(filepath, 'rb').read()
    
    magic = data[0:4]
    if magic != b'DGCP':
        print(f"ERROR: Not a DGCP file (magic: {magic})")
        return []
    
    count = struct.unpack('<I', data[4:8])[0]
    
    # Parse entry table: each entry is 8 bytes (line_count: u32, ptr_offset: u32)
    entries = []
    for i in range(count):
        off = 16 + i * 8
        line_count = struct.unpack('<I', data[off:off+4])[0]
        ptr_offset = struct.unpack('<I', data[off+4:off+8])[0]
        entries.append((line_count, ptr_offset))
    
    # Read text strings
    results = []
    for i, (line_count, ptr_off) in enumerate(entries):
        lines = []
        for j in range(line_count):
            str_ptr_off = ptr_off + j * 4
            str_offset = struct.unpack('<I', data[str_ptr_off:str_ptr_off+4])[0]
            # Read null-terminated string
            end = data.find(b'\x00', str_offset)
            if end == -1:
                end = len(data)
            text = data[str_offset:end].decode('latin-1', errors='replace')
            lines.append({
                'text': text,
                'offset': str_offset,
                'ptr_offset': str_ptr_off,
            })
        results.append({
            'index': i,
            'line_count': line_count,
            'ptr_offset': ptr_off,
            'lines': lines,
        })
    
    return results


def display_dgcp(filepath):
    """Display all text from a DGCP file."""
    basename = os.path.basename(filepath)
    results = parse_dgcp(filepath)
    
    print(f"=== {basename} ({len(results)} entries) ===")
    for entry in results:
        print(f"--- Entry {entry['index']} ({entry['line_count']} lines) ---")
        for j, line in enumerate(entry['lines']):
            print(f"  [{j}] @0x{line['offset']:04X}: \"{line['text']}\"")
        print()


if __name__ == '__main__':
    # Analyze key files
    dirs = [
        r"C:\Users\gorigamia\Desktop\game\extracted\ch52_g",
        r"C:\Users\gorigamia\Desktop\game\extracted\ch52_g50",
    ]
    
    files_to_check = [
        'TITCAP_E.BIN',
        'R01CAP_E.BIN', 
        'R11CAP_E.BIN',
        'COSCAP_E.BIN',
        'WARNCAPE.BIN',
        'R2SYCAP_F.BIN',
    ]
    
    for fname in files_to_check:
        for d in dirs:
            path = os.path.join(d, fname)
            if os.path.exists(path):
                display_dgcp(path)
                break
