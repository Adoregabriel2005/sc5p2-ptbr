"""
PTM Texture Viewer/Converter — Space Channel 5 Part 2
Converte texturas PTM (PS2 PSMT4) para PNG.

Uso:
    python tools/ptm_viewer.py                          # Converte todas de textures/com_texto/
    python tools/ptm_viewer.py textures/com_texto/PAUSE_I.PTM  # Converte uma específica
    python tools/ptm_viewer.py --all                    # Converte TODAS (com e sem texto)
"""
import struct
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("ERRO: Pillow necessario! Instale com: pip install Pillow")
    sys.exit(1)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES_DIR = os.path.join(PROJECT_DIR, "textures")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "textures_png")

# PS2 GS CLUT (Color Lookup Table) unswizzle for 4-bit palettes
# PS2 stores 4-bit palette entries in a specific swizzled order
def unswizzle_ps2_clut4(palette_data, num_colors=16):
    """Read PS2 4-bit CLUT palette (RGBA32 format)."""
    colors = []
    for i in range(min(num_colors, len(palette_data) // 4)):
        r = palette_data[i * 4]
        g = palette_data[i * 4 + 1]
        b = palette_data[i * 4 + 2]
        a = palette_data[i * 4 + 3]
        # PS2 alpha is 0-128, scale to 0-255
        a = min(255, a * 2)
        colors.append((r, g, b, a))
    # Pad with transparent black if needed
    while len(colors) < 16:
        colors.append((0, 0, 0, 0))
    return colors


def unswizzle_ps2_clut8(palette_data):
    """Read PS2 8-bit CLUT palette with CSM1 unswizzle."""
    raw_colors = []
    num = min(256, len(palette_data) // 4)
    for i in range(num):
        r = palette_data[i * 4]
        g = palette_data[i * 4 + 1]
        b = palette_data[i * 4 + 2]
        a = palette_data[i * 4 + 3]
        a = min(255, a * 2)
        raw_colors.append((r, g, b, a))
    while len(raw_colors) < 256:
        raw_colors.append((0, 0, 0, 0))

    # CSM1 unswizzle
    colors = [None] * 256
    for i in range(256):
        block = (i // 32) * 32
        pos_in_block = i % 32
        row = pos_in_block // 8
        col = pos_in_block % 8
        # Swap rows 1 and 2 within each group of 4
        if row == 1:
            row = 2
        elif row == 2:
            row = 1
        new_idx = block + row * 8 + col
        if new_idx < 256:
            colors[new_idx] = raw_colors[i]
        else:
            colors[i] = raw_colors[i]
    # Fill any None entries
    for i in range(256):
        if colors[i] is None:
            colors[i] = (0, 0, 0, 0)
    return colors


def decode_psth(data, offset):
    """Decode a PSTH texture chunk to an image."""
    magic = data[offset:offset + 4]
    if magic != b'PSTH':
        return None, None, 0

    inner_size = struct.unpack_from('<I', data, offset + 4)[0]
    total_chunk = inner_size + 8

    pal_offset_rel = struct.unpack_from('<I', data, offset + 8)[0]
    width = struct.unpack_from('<H', data, offset + 16)[0]
    height = struct.unpack_from('<H', data, offset + 18)[0]
    bpp_flag = struct.unpack_from('<H', data, offset + 20)[0]

    if width == 0 or height == 0 or width > 2048 or height > 2048:
        return None, None, total_chunk

    payload_start = offset + 8
    pixel_start = payload_start  # Pixels start right after the 8-byte chunk header... 
    # Actually there's a sub-header. Let's use the sub_header_size field:
    sub_hdr_size = struct.unpack_from('<I', data, offset + 28)[0]
    pixel_start = payload_start + sub_hdr_size

    pal_abs = payload_start + pal_offset_rel
    pal_size = inner_size - pal_offset_rel

    # Determine format (lower byte is the PS2 GS pixel format)
    fmt = bpp_flag & 0xFF
    if fmt == 0x14:  # PSMT4 (4-bit indexed)
        expected_pixels = (width * height) // 2
        if pal_size >= 64:
            palette = unswizzle_ps2_clut4(data[pal_abs:pal_abs + pal_size])
        else:
            palette = [(i * 17, i * 17, i * 17, 255) for i in range(16)]

        pix_data = data[pixel_start:pixel_start + expected_pixels]
        if len(pix_data) < expected_pixels:
            pix_data += b'\x00' * (expected_pixels - len(pix_data))

        img = Image.new('RGBA', (width, height))
        pixels = []
        for byte in pix_data:
            lo = byte & 0x0F
            hi = (byte >> 4) & 0x0F
            pixels.append(palette[lo])
            pixels.append(palette[hi])
        img.putdata(pixels[:width * height])
        return img, f"{width}x{height}_4bpp", total_chunk

    elif fmt == 0x13:  # PSMT8 (8-bit indexed)
        expected_pixels = width * height
        if pal_size >= 1024:
            palette = unswizzle_ps2_clut8(data[pal_abs:pal_abs + pal_size])
        else:
            palette = [(i, i, i, 255) for i in range(256)]

        pix_data = data[pixel_start:pixel_start + expected_pixels]
        if len(pix_data) < expected_pixels:
            pix_data += b'\x00' * (expected_pixels - len(pix_data))

        img = Image.new('RGBA', (width, height))
        pixels = [palette[b] for b in pix_data]
        img.putdata(pixels[:width * height])
        return img, f"{width}x{height}_8bpp", total_chunk

    elif fmt == 0x00:  # PSMCT32 (32-bit RGBA)
        expected = width * height * 4
        pix_data = data[pixel_start:pixel_start + expected]
        img = Image.new('RGBA', (width, height))
        pixels = []
        for i in range(0, len(pix_data), 4):
            r, g, b, a = pix_data[i:i + 4]
            a = min(255, a * 2)
            pixels.append((r, g, b, a))
        img.putdata(pixels[:width * height])
        return img, f"{width}x{height}_32bpp", total_chunk

    else:
        return None, f"unknown_format_0x{bpp_flag:02X}", total_chunk


def convert_ptm(filepath, output_dir):
    """Convert a PTM file to PNG(s)."""
    with open(filepath, 'rb') as f:
        data = f.read()

    basename = os.path.splitext(os.path.basename(filepath))[0]

    if data[:4] != b'PTMH':
        print(f"  [SKIP] {os.path.basename(filepath)}: not a PTM file")
        return 0

    hdr_size = struct.unpack_from('<I', data, 4)[0]
    tex_count = struct.unpack_from('<H', data, 10)[0]

    # Read names
    names = []
    for i in range(tex_count):
        off = 12 + i * 28
        if off + 24 <= len(data):
            name = data[off:off + 24].split(b'\x00')[0].decode('ascii', errors='replace')
            names.append(name)

    # Find PSTH chunks
    pos = hdr_size + 8  # Skip padding after header
    idx = 0
    saved = 0

    while pos < len(data) - 8:
        if data[pos:pos + 4] != b'PSTH':
            pos += 4
            continue

        tex_name = names[idx] if idx < len(names) else f"tex_{idx}"
        img, info, chunk_size = decode_psth(data, pos)

        if img is not None:
            out_name = f"{basename}_{idx:02d}_{tex_name}.png"
            out_path = os.path.join(output_dir, out_name)
            img.save(out_path)
            print(f"  [{info:>18}] {out_name}")
            saved += 1
        elif info:
            print(f"  [SKIP] texture #{idx} '{tex_name}': {info}")

        pos += chunk_size
        idx += 1

    return saved


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] != '--all':
        # Convert specific file
        filepath = sys.argv[1]
        if not os.path.isabs(filepath):
            filepath = os.path.join(PROJECT_DIR, filepath)
        if os.path.exists(filepath):
            n = convert_ptm(filepath, OUTPUT_DIR)
            print(f"\n{n} texturas salvas em {OUTPUT_DIR}")
        else:
            print(f"Arquivo nao encontrado: {filepath}")
        return

    # Convert all or just com_texto
    if '--all' in sys.argv:
        dirs = [os.path.join(TEXTURES_DIR, "com_texto"), os.path.join(TEXTURES_DIR, "sem_texto")]
    else:
        dirs = [os.path.join(TEXTURES_DIR, "com_texto")]

    total = 0
    for d in dirs:
        if not os.path.isdir(d):
            continue
        ptm_files = sorted(f for f in os.listdir(d) if f.upper().endswith('.PTM'))
        print(f"\n=== {os.path.basename(d)}/ ({len(ptm_files)} arquivos) ===\n")
        for fn in ptm_files:
            total += convert_ptm(os.path.join(d, fn), OUTPUT_DIR)

    print(f"\n=== Total: {total} texturas exportadas para {OUTPUT_DIR} ===")


if __name__ == '__main__':
    main()
