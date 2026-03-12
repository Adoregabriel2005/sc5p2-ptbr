"""
Status Detalhado da Tradução — Space Channel 5 Part 2 Translation
Mostra progresso por arquivo, categoria e estatísticas gerais.

Uso:
    python tools/status.py               # Status geral
    python tools/status.py --detailed    # Com lista de cada arquivo
    python tools/status.py --file R01    # Status de arquivo específico
"""
import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSLATION_FILE = os.path.join(PROJECT_DIR, "translation.json")

CATEGORIES = {
    "Menus/Título":    ["TITCAP"],
    "Avisos/Sistema":  ["WARNCAP"],
    "Figurinos":       ["COSCAP"],
    "Cutscenes":       ["MAKUCAP", "MUCAP"],
    "Vozes":           ["VOCAP"],
    "Sistema Batalha": ["SYCAP"],
    "Diálogos":        ["CAP_", "CAP."],
    "Perfis (AFS)":    ["CTL_TEXT"],
}


def categorize(filename):
    fn = filename.upper()
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if pat in fn:
                return cat
    return "Outros"


def status(file_filter=None, detailed=False):
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Aggregate stats
    by_file = {}
    by_category = {}
    total_entries = 0
    total_translated = 0
    total_original_chars = 0
    total_translated_chars = 0

    for file_key, file_info in sorted(data.get("files", {}).items()):
        if "ch52_g50" in file_key:
            continue

        if file_filter and file_filter.upper() not in file_key.upper():
            continue

        fname = file_key.split("/")[-1] if "/" in file_key else file_key
        cat = categorize(fname)

        file_entries = 0
        file_translated = 0
        file_orig_chars = 0
        file_trans_chars = 0

        for entry in file_info.get("entries", []):
            orig = entry.get("original", [])
            trans = entry.get("translated", [])
            has_trans = bool(trans and any(t.strip() for t in trans))

            file_entries += 1
            orig_len = sum(len(l) for l in orig)
            file_orig_chars += orig_len

            if has_trans:
                file_translated += 1
                file_trans_chars += sum(len(l) for l in trans)

        by_file[fname] = {
            'entries': file_entries,
            'translated': file_translated,
            'orig_chars': file_orig_chars,
            'trans_chars': file_trans_chars,
            'category': cat,
        }

        if cat not in by_category:
            by_category[cat] = {'entries': 0, 'translated': 0}
        by_category[cat]['entries'] += file_entries
        by_category[cat]['translated'] += file_translated

        total_entries += file_entries
        total_translated += file_translated
        total_original_chars += file_orig_chars
        total_translated_chars += file_trans_chars

    # Display
    pct = (total_translated / total_entries * 100) if total_entries > 0 else 0

    print(f"""
╔══════════════════════════════════════════════════╗
║  Space Channel 5 Part 2 — Tradução PT-BR        ║
╠══════════════════════════════════════════════════╣
║  Entradas traduzidas: {total_translated:>5} / {total_entries:<5} ({pct:.1f}%)     ║
║  Caracteres original: {total_original_chars:>8,}                  ║
║  Caracteres tradução: {total_translated_chars:>8,}                  ║
╚══════════════════════════════════════════════════╝""")

    # By category
    print(f"\n{'Categoria':<20} {'Traduzido':>12} {'Total':>8} {'%':>7}")
    print("-" * 50)
    for cat in CATEGORIES:
        if cat in by_category:
            s = by_category[cat]
            p = (s['translated'] / s['entries'] * 100) if s['entries'] > 0 else 0
            bar = "█" * int(p / 5) + "░" * (20 - int(p / 5))
            print(f"  {cat:<18} {s['translated']:>5} / {s['entries']:<5} {p:>6.1f}% {bar}")

    if detailed:
        print(f"\n{'Arquivo':<25} {'Traduzido':>12} {'Total':>8} {'%':>7}")
        print("-" * 55)
        for fname in sorted(by_file):
            s = by_file[fname]
            p = (s['translated'] / s['entries'] * 100) if s['entries'] > 0 else 0
            marker = "✅" if p == 100 else "🔄" if p > 0 else "❌"
            print(f"  {marker} {fname:<22} {s['translated']:>4} / {s['entries']:<4} {p:>6.1f}%")

    # Show untranslated files
    untrans_files = [f for f, s in by_file.items() if s['translated'] < s['entries']]
    if untrans_files and not detailed:
        print(f"\n📋 Arquivos incompletos ({len(untrans_files)}):")
        for fname in sorted(untrans_files):
            s = by_file[fname]
            missing = s['entries'] - s['translated']
            print(f"  • {fname}: faltam {missing} de {s['entries']}")


def main():
    args = sys.argv[1:]
    file_filter = None
    detailed = False

    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            file_filter = args[i + 1]
            i += 2
        elif args[i] == "--detailed":
            detailed = True
            i += 1
        else:
            i += 1

    status(file_filter=file_filter, detailed=detailed)


if __name__ == '__main__':
    main()
