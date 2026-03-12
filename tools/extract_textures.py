"""
Extrai todas as texturas (PTM, PMV, GD, MTP, CDR) do CVM para a pasta textures/
Para contribuidores poderem editar e traduzir texturas com texto.
"""
import struct
import os
import sys

GAME_DIR = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")

# Extensions to extract (visual/texture files)
TEXTURE_EXTS = {'.PTM', '.PMV', '.GD', '.MTP'}


def parse_directory(f, iso_base, sector, size, prefix=""):
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
                sub = parse_directory(f, iso_base, extent, data_len, full_path + '/')
                entries.extend(sub)
        offset += rec_len
    return entries


def extract_textures(cvm_name):
    cvm_path = os.path.join(GAME_DIR, cvm_name)
    if not os.path.exists(cvm_path):
        print(f"ERRO: {cvm_path} nao encontrado!")
        return

    print(f"\n=== Extraindo texturas de {cvm_name} ===\n")

    with open(cvm_path, 'rb') as f:
        f.seek(0)
        search = f.read(1024 * 1024)
        pvd_off = search.find(b'\x01CD001')
        if pvd_off == -1:
            print("ERRO: PVD nao encontrado!")
            return
        iso_base = pvd_off - 16 * 2048
        pvd = search[pvd_off:pvd_off+2048]
        root_rec = pvd[156:190]
        root_loc = struct.unpack('<I', root_rec[2:6])[0]
        root_size = struct.unpack('<I', root_rec[10:14])[0]

        entries = parse_directory(f, iso_base, root_loc, root_size)

        # Filter texture files
        tex_entries = [e for e in entries if not e['is_dir']
                       and os.path.splitext(e['name'])[1].upper() in TEXTURE_EXTS]

        # Categorize
        with_lang = []
        without_lang = []
        lang_suffixes = {'_E', '_F', '_G', '_I', '_S', 'E', 'F', 'G', 'I', 'S'}

        for e in tex_entries:
            base = os.path.splitext(e['name'])[0]
            # Check if it has a language variant
            has_lang = False
            for suffix in ['_E', '_F', '_G', '_I', '_S']:
                if base.endswith(suffix):
                    has_lang = True
                    break
            # Also check single letter suffix (COSROOME, NOWLOAD0E, etc.)
            if not has_lang and len(base) > 1:
                last = base[-1]
                if last in 'EFGIS':
                    base_check = base[:-1]
                    # Make sure it's a lang variant (check if base version exists)
                    for e2 in tex_entries:
                        b2 = os.path.splitext(e2['name'])[0]
                        if b2 == base_check:
                            has_lang = True
                            break

            if has_lang:
                with_lang.append(e)
            else:
                without_lang.append(e)

        # Output dirs
        lang_dir = os.path.join(OUTPUT_DIR, "com_texto")
        general_dir = os.path.join(OUTPUT_DIR, "sem_texto")
        os.makedirs(lang_dir, exist_ok=True)
        os.makedirs(general_dir, exist_ok=True)

        count = 0
        for e in tex_entries:
            base = os.path.splitext(e['name'])[0]
            # Determine output folder
            if e in with_lang:
                out_dir = lang_dir
            else:
                out_dir = general_dir

            out_path = os.path.join(out_dir, e['name'])

            # Skip if already extracted
            if os.path.exists(out_path) and os.path.getsize(out_path) == e['size']:
                print(f"  [skip] {e['name']} (ja extraido)")
                count += 1
                continue

            # Extract
            f.seek(iso_base + e['sector'] * 2048)
            file_data = f.read(e['size'])
            with open(out_path, 'wb') as out:
                out.write(file_data)
            count += 1
            label = "COM TEXTO" if e in with_lang else "geral"
            print(f"  [{label:>9}] {e['name']} ({e['size']:,} bytes)")

        print(f"\nTotal: {count} texturas extraidas de {cvm_name}")
        print(f"  Com texto (idioma): {len(with_lang)}")
        print(f"  Gerais: {len(without_lang)}")


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    extract_textures('ch52_g.cvm')

    # Create README for textures folder
    readme = os.path.join(OUTPUT_DIR, "LEIA-ME.txt")
    with open(readme, 'w', encoding='utf-8') as f:
        f.write("""=== Texturas Extraidas - Space Channel 5 Part 2 ===

PASTAS:
  com_texto/  -> Texturas que possuem variantes por idioma (contêm texto)
                 Estas precisam ser editadas para a tradução PT-BR.
  sem_texto/  -> Texturas gerais sem variantes de idioma.

FORMATOS:
  .PTM  -> Texture Map (formato custom PS2, contém imagens com paletas)
  .PMV  -> Texture data (rostos de bosses, etc.)
  .GD   -> Font data (HANFONT = kanji, ZENFONT = fontes latinas)
  .MTP  -> Texture Pack (catálogo de figuras, etc.)

TEXTURAS COM TEXTO (precisam tradução):
  TITLE_I.PTM      -> Tela de título (italiano)
  PAUSE_I.PTM       -> Menu de pausa
  R00_I.PTM         -> Tela de intro/Report
  COSROOMI.PTM      -> Sala de figurinos
  NOWLOAD0I.PTM     -> Tela de loading (pequena)
  NOWLOAD1I.PTM     -> Tela de loading (grande)
  RESULT0I.PTM      -> Tela de resultados 1
  RESULT1I.PTM      -> Tela de resultados 2

COMO EDITAR:
  1. Os arquivos PTM são texturas PS2 em formato raw
  2. Use ferramentas como Rainbow (PS2 texture editor) ou
     scripts custom para converter PTM <-> PNG
  3. Edite o PNG com qualquer editor de imagem
  4. Converta de volta para PTM mantendo o mesmo tamanho
  5. Substitua o arquivo _I correspondente no CVM
""")
    print(f"\nCriado: {readme}")
    print(f"\nTudo salvo em: {OUTPUT_DIR}")
