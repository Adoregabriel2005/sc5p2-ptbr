"""
Busca de Texto — Space Channel 5 Part 2 Translation
Busca textos no translation.json (originais e traduzidos).

Uso:
    python tools/search_text.py "dance"          # Busca em tudo
    python tools/search_text.py "ulala" --only original    # Só nos originais
    python tools/search_text.py "dança" --only translated  # Só nos traduzidos
    python tools/search_text.py "pausa" --file TITCAP      # Filtrar por arquivo
    python tools/search_text.py --untranslated              # Mostrar não traduzidos
    python tools/search_text.py --untranslated --file R01   # Não traduzidos de R01
"""
import json
import os
import sys
import re

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSLATION_FILE = os.path.join(PROJECT_DIR, "translation.json")


def load_translations():
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def search(query=None, only=None, file_filter=None, untranslated=False, show_context=True):
    data = load_translations()
    results = []

    for file_key, file_info in data.get("files", {}).items():
        # Skip duplicates (ch52_g50)
        if "ch52_g50" in file_key:
            continue

        if file_filter and file_filter.upper() not in file_key.upper():
            continue

        for entry in file_info.get("entries", []):
            eid = entry["id"]
            orig = entry.get("original", [])
            trans = entry.get("translated", [])
            has_translation = bool(trans and any(t.strip() for t in trans))

            if untranslated:
                if has_translation:
                    continue
                results.append((file_key, eid, orig, trans))
                continue

            if query is None:
                continue

            orig_text = " ".join(orig)
            trans_text = " ".join(trans) if trans else ""

            match_orig = bool(re.search(query, orig_text, re.IGNORECASE))
            match_trans = bool(re.search(query, trans_text, re.IGNORECASE))

            if only == "original" and not match_orig:
                continue
            elif only == "translated" and not match_trans:
                continue
            elif only is None and not (match_orig or match_trans):
                continue

            results.append((file_key, eid, orig, trans))

    # Display results
    if not results:
        print("Nenhum resultado encontrado.")
        return

    print(f"\n{'='*60}")
    print(f" {len(results)} resultado(s) encontrado(s)")
    print(f"{'='*60}\n")

    for file_key, eid, orig, trans in results:
        fname = file_key.split("/")[-1] if "/" in file_key else file_key
        has_trans = bool(trans and any(t.strip() for t in trans))

        status = "✅" if has_trans else "❌"
        print(f"{status} [{fname}] entrada #{eid}")
        print(f"   Original:  {' | '.join(orig)}")
        if has_trans:
            print(f"   Tradução:  {' | '.join(trans)}")
        else:
            print(f"   Tradução:  (vazio)")
        print()


def main():
    args = sys.argv[1:]

    query = None
    only = None
    file_filter = None
    untranslated = False

    i = 0
    while i < len(args):
        if args[i] == "--only" and i + 1 < len(args):
            only = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            file_filter = args[i + 1]
            i += 2
        elif args[i] == "--untranslated":
            untranslated = True
            i += 1
        elif args[i] == "--help" or args[i] == "-h":
            print(__doc__)
            return
        else:
            query = args[i]
            i += 1

    if query is None and not untranslated:
        print("Uso: python tools/search_text.py <busca> [--only original|translated] [--file NOME]")
        print("     python tools/search_text.py --untranslated [--file NOME]")
        print("     python tools/search_text.py --help")
        return

    search(query=query, only=only, file_filter=file_filter, untranslated=untranslated)


if __name__ == '__main__':
    main()
