"""
Validação de Traduções — Space Channel 5 Part 2 Translation
Verifica se as traduções são válidas e cabem no espaço disponível.

Uso:
    python tools/validate.py              # Validar tudo
    python tools/validate.py --file R01   # Validar arquivo específico
    python tools/validate.py --verbose    # Mostrar detalhes de cada entrada
"""
import json
import os
import sys
import struct

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSLATION_FILE = os.path.join(PROJECT_DIR, "translation.json")

# Caracteres válidos em Latin-1 que o jogo suporta
LATIN1_SAFE = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100))


def validate_encoding(text):
    """Verifica se o texto pode ser codificado em Latin-1."""
    issues = []
    for i, ch in enumerate(text):
        try:
            ch.encode('latin-1')
        except UnicodeEncodeError:
            issues.append((i, ch, f"U+{ord(ch):04X}"))
    return issues


def estimate_dgcp_size(entries):
    """Estima o tamanho do arquivo DGCP compilado."""
    # DGCP header: 4(magic) + 4(count) + 8(padding) = 16
    # Entry table: count * 8 (line_count + ptr_offset)
    # For each entry: pointer array (line_count * 4)
    # Then: null-terminated strings
    size = 16  # header
    size += len(entries) * 8  # entry table

    for entry in entries:
        lines = entry.get("translated", []) or entry.get("original", [])
        size += len(lines) * 4  # pointer array
        for line in lines:
            size += len(line.encode('latin-1', errors='replace')) + 1  # string + null

    return size


def validate(file_filter=None, verbose=False):
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_issues = 0
    files_checked = 0
    entries_ok = 0
    entries_warn = 0
    entries_error = 0

    for file_key, file_info in sorted(data.get("files", {}).items()):
        if "ch52_g50" in file_key:
            continue

        if file_filter and file_filter.upper() not in file_key.upper():
            continue

        fname = file_key.split("/")[-1] if "/" in file_key else file_key
        files_checked += 1
        file_issues = []

        for entry in file_info.get("entries", []):
            eid = entry["id"]
            orig = entry.get("original", [])
            trans = entry.get("translated", [])

            if not trans or not any(t.strip() for t in trans):
                continue  # Not translated, skip

            # Check encoding
            for li, line in enumerate(trans):
                enc_issues = validate_encoding(line)
                for pos, ch, code in enc_issues:
                    file_issues.append(
                        f"  ❌ #{eid} linha {li}: caractere '{ch}' ({code}) nao suportado em Latin-1")
                    entries_error += 1

            # Check line count mismatch
            if len(trans) != len(orig) and len(trans) > 0:
                file_issues.append(
                    f"  ⚠️  #{eid}: {len(orig)} linhas original vs {len(trans)} linhas traduzido")
                entries_warn += 1

            # Check if translation is much longer than original
            orig_len = sum(len(l.encode('latin-1', errors='replace')) for l in orig)
            trans_len = sum(len(l.encode('latin-1', errors='replace')) for l in trans)
            if trans_len > orig_len * 1.5 and trans_len > orig_len + 20:
                file_issues.append(
                    f"  ⚠️  #{eid}: tradução muito longa ({trans_len} bytes vs {orig_len} original)")
                entries_warn += 1

            # Check empty translation lines
            for li, line in enumerate(trans):
                if not line.strip() and orig[li].strip() if li < len(orig) else False:
                    file_issues.append(
                        f"  ⚠️  #{eid} linha {li}: tradução vazia mas original tem texto")
                    entries_warn += 1

            if verbose and not file_issues:
                entries_ok += 1

        if file_issues:
            print(f"\n📄 {fname}:")
            for issue in file_issues:
                print(issue)
            total_issues += len(file_issues)

    # Summary
    print(f"\n{'='*50}")
    print(f" Validação completa")
    print(f"{'='*50}")
    print(f"  Arquivos verificados: {files_checked}")
    print(f"  Erros (encoding):     {entries_error}")
    print(f"  Avisos (tamanho/etc): {entries_warn}")
    print(f"  Total de problemas:   {total_issues}")

    if total_issues == 0:
        print("\n  ✅ Tudo OK! Nenhum problema encontrado.")
    else:
        print(f"\n  ⚠️  {total_issues} problema(s) para revisar.")

    return total_issues


def main():
    args = sys.argv[1:]
    file_filter = None
    verbose = False

    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            file_filter = args[i + 1]
            i += 2
        elif args[i] == "--verbose":
            verbose = True
            i += 1
        else:
            i += 1

    validate(file_filter=file_filter, verbose=verbose)


if __name__ == '__main__':
    main()
