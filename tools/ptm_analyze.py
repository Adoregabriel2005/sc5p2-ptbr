"""
Analyze PTM texture format for Space Channel 5 Part 2
"""
import struct
import os

def analyze_psth(data, offset):
    """Analyze a single PSTH chunk."""
    magic = data[offset:offset+4]
    if magic != b'PSTH':
        return None
    
    inner_size = struct.unpack_from('<I', data, offset+4)[0]
    pal_offset = struct.unpack_from('<I', data, offset+8)[0]
    flag = struct.unpack_from('<I', data, offset+12)[0]
    width = struct.unpack_from('<H', data, offset+16)[0]
    height = struct.unpack_from('<H', data, offset+18)[0]
    bpp_flag = struct.unpack_from('<H', data, offset+20)[0]
    pal_colors = struct.unpack_from('<H', data, offset+22)[0]
    total_size = struct.unpack_from('<I', data, offset+24)[0]
    header_size = struct.unpack_from('<I', data, offset+28)[0]
    
    payload_start = offset + 8  # after magic + size
    pixel_start = payload_start + header_size
    palette_abs = payload_start + pal_offset
    
    # Determine bits per pixel
    pixel_bytes = pal_offset - header_size
    total_pixels = width * height
    if total_pixels > 0:
        calc_bpp = (pixel_bytes * 8) / total_pixels
    else:
        calc_bpp = 0
    
    # Palette size
    pal_size = inner_size - pal_offset
    if pal_size > 0:
        colors = pal_size // 4  # RGBA
    else:
        colors = 0
    
    return {
        'offset': offset,
        'inner_size': inner_size,
        'width': width,
        'height': height,
        'bpp_flag': bpp_flag,
        'pal_colors_field': pal_colors,
        'pal_offset': pal_offset,
        'header_size': header_size,
        'pixel_start': pixel_start,
        'palette_abs': palette_abs,
        'pixel_bytes': pixel_bytes,
        'calc_bpp': calc_bpp,
        'pal_size': pal_size,
        'num_colors': colors,
        'total_chunk_size': inner_size + 8,
    }


def analyze_ptm(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n=== {os.path.basename(filepath)} ({len(data):,} bytes) ===")
    
    magic = data[:4]
    if magic != b'PTMH':
        print("  Not a PTM file!")
        return
    
    hdr_size = struct.unpack_from('<I', data, 4)[0]
    groups = struct.unpack_from('<H', data, 8)[0]
    tex_count = struct.unpack_from('<H', data, 10)[0]
    
    print(f"  Header: {hdr_size} bytes, {groups} group(s), {tex_count} texture(s)")
    
    # Read texture names
    names = []
    for i in range(tex_count):
        off = 12 + i * 28
        name = data[off:off+24].split(b'\x00')[0].decode('ascii', errors='replace')
        names.append(name)
        print(f"    [{i}] {name}")
    
    # Find and analyze PSTH chunks
    pos = hdr_size + 8  # skip 8-byte padding after PTMH header
    chunk_idx = 0
    while pos < len(data):
        info = analyze_psth(data, pos)
        if info is None:
            break
        
        name = names[chunk_idx] if chunk_idx < len(names) else "?"
        print(f"\n  PSTH #{chunk_idx} '{name}' at 0x{pos:X}:")
        print(f"    Dimensions: {info['width']}x{info['height']}")
        print(f"    Calculated BPP: {info['calc_bpp']:.1f}")
        print(f"    Pixel data: {info['pixel_bytes']:,} bytes at 0x{info['pixel_start']:X}")
        print(f"    Palette: {info['pal_size']} bytes ({info['num_colors']} colors RGBA) at 0x{info['palette_abs']:X}")
        print(f"    BPP flag: 0x{info['bpp_flag']:04X}, Palette field: 0x{info['pal_colors_field']:04X}")
        
        # Show non-zero palette colors
        if info['num_colors'] > 0 and info['palette_abs'] + info['pal_size'] <= len(data):
            pal_data = data[info['palette_abs']:info['palette_abs']+info['pal_size']]
            nz_colors = []
            for ci in range(info['num_colors']):
                r, g, b_c, a = pal_data[ci*4:ci*4+4]
                if r or g or b_c or a:
                    nz_colors.append((ci, r, g, b_c, a))
            print(f"    Non-zero colors: {len(nz_colors)}")
            for ci, r, g, b_c, a in nz_colors[:8]:
                print(f"      [{ci:3d}] R={r:3d} G={g:3d} B={b_c:3d} A={a:3d}")
            if len(nz_colors) > 8:
                print(f"      ... +{len(nz_colors)-8} more")
        
        pos += info['total_chunk_size']
        chunk_idx += 1


if __name__ == '__main__':
    tex_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")
    
    # Analyze a few key textures
    for name in ['com_texto/PAUSE_I.PTM', 'com_texto/TITLE_I.PTM', 'com_texto/COSROOMI.PTM',
                 'com_texto/RESULT0I.PTM', 'com_texto/R00_I.PTM']:
        path = os.path.join(tex_dir, name)
        if os.path.exists(path):
            analyze_ptm(path)
