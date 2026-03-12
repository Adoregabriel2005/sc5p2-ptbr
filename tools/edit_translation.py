"""
Editor Rápido de Tradução — Space Channel 5 Part 2 Translation
Edita uma tradução diretamente pela linha de comando.

Uso:
    python tools/edit_translation.py TITCAP 0 "Novo Jogo" "Continuar"
        → Edita entrada #0 do TITCAP com 2 linhas

    python tools/edit_translation.py TITCAP 0 --show
        → Mostra o conteúdo atual da entrada #0

    python tools/edit_translation.py TITCAP --list
        → Lista todas as entradas do arquivo
"""
import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSLATION_FILE = os.path.join(PROJECT_DIR, "translation.json")


def load():
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(data):
    with open(TRANSLATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_file_key(data, pattern):
    """Find file key matching pattern (skip ch52_g50 duplicates)."""
    pattern_upper = pattern.upper()
    matches = []
    for key in data.get("files", {}):
        if "ch52_g50" in key:
            continue
        if pattern_upper in key.upper():
            matches.append(key)
    return matches


def list_entries(data, file_key):
    """List all entries in a file."""
    file_info = data["files"][file_key]
    fname = file_key.split("/")[-1] if "/" in file_key else file_key
    print(f"\n📄 {fname} ({len(file_info['entries'])} entradas)\n")

    for entry in file_info["entries"]:
        eid = entry["id"]
        orig = entry.get("original", [])
        trans = entry.get("translated", [])
        has_trans = bool(trans and any(t.strip() for t in trans))
        status = "✅" if has_trans else "❌"

        orig_preview = " | ".join(orig)[:60]
        print(f"  {status} #{eid:>3}: {orig_preview}")


def show_entry(data, file_key, entry_id):
    """Show details of a specific entry."""
    file_info = data["files"][file_key]
    for entry in file_info["entries"]:
        if entry["id"] == entry_id:
            fname = file_key.split("/")[-1]
            print(f"\n📄 {fname} — Entrada #{entry_id}\n")
            print("Original:")
            for i, line in enumerate(entry.get("original", [])):
                print(f"  [{i}] {line}")
            print("\nTradução:")
            trans = entry.get("translated", [])
            if trans and any(t.strip() for t in trans):
                for i, line in enumerate(trans):
                    print(f"  [{i}] {line}")
            else:
                print("  (vazio)")
            return
    print(f"Entrada #{entry_id} não encontrada!")


def edit_entry(data, file_key, entry_id, new_lines):
    """Edit translation for an entry."""
    # Edit in both ch52_g and ch52_g50
    base_path = file_key.split("/")[-1]
    edited = 0

    for key, file_info in data["files"].items():
        if base_path not in key:
            continue
        for entry in file_info["entries"]:
            if entry["id"] == entry_id:
                old_trans = entry.get("translated", [])
                entry["translated"] = new_lines
                edited += 1
                break

    if edited > 0:
        save(data)
        print(f"\n✅ Entrada #{entry_id} atualizada em {edited} arquivo(s)!")
        print(f"   Nova tradução: {' | '.join(new_lines)}")
    else:
        print(f"Entrada #{entry_id} não encontrada!")


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        print(__doc__)
        return

    data = load()

    file_pattern = args[0]
    matches = find_file_key(data, file_pattern)

    if not matches:
        print(f"Nenhum arquivo encontrado com '{file_pattern}'")
        print("Arquivos disponíveis:")
        for key in sorted(data.get("files", {})):
            if "ch52_g50" not in key:
                print(f"  {key}")
        return

    if len(matches) > 1:
        print(f"Múltiplos arquivos encontrados:")
        for m in matches:
            print(f"  {m}")
        print("Seja mais específico.")
        return

    file_key = matches[0]

    if len(args) >= 2 and args[1] == "--list":
        list_entries(data, file_key)
        return

    if len(args) < 2:
        list_entries(data, file_key)
        return

    try:
        entry_id = int(args[1])
    except ValueError:
        print(f"ID inválido: {args[1]}")
        return

    if len(args) >= 3 and args[2] == "--show":
        show_entry(data, file_key, entry_id)
        return

    if len(args) < 3:
        show_entry(data, file_key, entry_id)
        return

    # Remaining args are translation lines
    new_lines = args[2:]
    edit_entry(data, file_key, entry_id, new_lines)


if __name__ == '__main__':
    main()
