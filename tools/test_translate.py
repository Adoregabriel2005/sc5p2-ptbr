"""Quick test: translate TITCAP and R01CAP, build, and verify"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from translate_toolkit import parse_dgcp, build_dgcp

TRANSLATION_FILE = r"C:\Users\gorigamia\Desktop\game\translation.json"

# Load translation file
with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Sample translation for TITCAP (Title Screen) ===
# These are the menu descriptions visible on the title screen
titcap_translations = {
    0: [  # Story Mode Solo
        "Dance numa tempestade solo.",
        "Jogue como a repórter do Canal 5, Ulala, e pare os",
        "planos diabólicos dos Rhythm Rogues!"
    ],
    1: [  # Story Mode 2P
        "Ainda mais quente com dois!",
        "Jogador 1: Controla os botões direcionais.",
        "Jogador 2: Controla os botões de ação."
    ],
    2: [  # Ulala's Dance (Solo)
        "Batalha sem parar de 100 rounds.",
        "Consiga rankings maiores",
        "para ganhar novas roupas da Ulala."
    ],
    3: [  # Ulala's Dance (2P)
        "Enfrente todos os 100 rounds com um parceiro!",
        "Jogador 1: Controla os botões direcionais.",
        "Jogador 2: Controla os botões de ação."
    ],
    4: [  # Character Profiles
        "Veja os perfis da grande",
        "variedade de personagens",
        "*Você também vai encontrar dicas sobre",
        "estratégia e comandos secretos!"
    ],
    5: [  # Costume Change
        "Mude a roupa da Ulala.",
        "Selecione suas roupas favoritas",
        "e itens encontrados durante o jogo!",
        ""
    ],
}

# Apply sample translations
for file_key in ['ch52_g/TITCAP_E.BIN', 'ch52_g50/TITCAP_E.BIN']:
    if file_key not in data['files']:
        continue
    entries = data['files'][file_key]['entries']
    for entry in entries:
        idx = entry['id']
        if idx in titcap_translations:
            trans = titcap_translations[idx]
            # Pad to match original line count
            while len(trans) < len(entry['original']):
                trans.append("")
            entry['translated'] = trans[:len(entry['original'])]

# === Sample translation for WARNCAPE (Memory Card warnings) ===
warn_translations = {
    0: ["Verificando memory card (PS2) ou controle."],
    1: [
        "Nenhum memory card (PS2) inserido.",
        "Para salvar é necessário pelo menos 161KB.",
        "Se você continuar sem um",
        "memory card (PS2) não será possível",
        "salvar. Tudo bem?"
    ],
    5: ["Carregamento completo."],
}

for file_key in ['ch52_g/WARNCAPE.BIN', 'ch52_g50/WARNCAPE.BIN']:
    if file_key not in data['files']:
        continue
    entries = data['files'][file_key]['entries']
    for entry in entries:
        idx = entry['id']
        if idx in warn_translations:
            trans = warn_translations[idx]
            while len(trans) < len(entry['original']):
                trans.append("")
            entry['translated'] = trans[:len(entry['original'])]

# Save updated translation file
with open(TRANSLATION_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Sample translations applied!")
print("Now testing build...")

# Test building a DGCP file
test_entries = titcap_translations
entries_for_build = []
file_data = data['files']['ch52_g/TITCAP_E.BIN']
for entry in file_data['entries']:
    lines = []
    for i, orig in enumerate(entry['original']):
        trans = entry['translated'][i] if i < len(entry['translated']) else ""
        lines.append(trans.strip() if trans.strip() else orig)
    entries_for_build.append(lines)

new_data = build_dgcp(entries_for_build)
print(f"Built DGCP: {len(new_data)} bytes")

# Verify by re-parsing
parsed = parse_dgcp(new_data)
print(f"Re-parsed: {len(parsed)} entries")
for i, lines in enumerate(parsed[:6]):
    print(f"  Entry {i}:")
    for j, line in enumerate(lines):
        print(f"    [{j}] {line}")
