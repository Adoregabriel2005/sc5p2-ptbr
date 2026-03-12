"""Apply sample PT-BR translations to test the Italian -> Portuguese pipeline."""
import json
import os

TRANSLATION_FILE = r"C:\Users\gorigamia\Desktop\game\translation.json"

with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Translate TITCAP entries (title screen text)
for key in data["files"]:
    if "TITCAP_E.BIN" in key:
        entries = data["files"][key]["entries"]
        
        # Entry 0: ULALA'S DANCE mode description
        entries[0]["translated"] = [
            "Dance numa tempestade solo.",
            "Jogue como a reporter do Canal 5, Ulala, e pare os",
            "planos diabolicos dos Rhythm Rogues!"
        ]
        
        # Entry 1: 2P mode
        entries[1]["translated"] = [
            "Ainda mais quente com dois!",
            "Jogador 1: Controla os botoes direcionais.",
            "Jogador 2: Controla os botoes de acao."
        ]
        
        # Entry 2: 100-round battle
        entries[2]["translated"] = [
            "Batalha sem parar de 100 rounds.",
            "Consiga rankings maiores",
            "para ganhar novas roupas da Ulala."
        ]
        
        print(f"  Translated: {key} (3 entries)")

# Translate WARNCAP (memory card warnings)  
for key in data["files"]:
    if "WARNCAPE.BIN" in key:
        entries = data["files"][key]["entries"]
        
        # Entry 0
        if len(entries) > 0 and entries[0]["original"]:
            entries[0]["translated"] = ["Verificando o Memory Card (PS2)..."]
        
        print(f"  Translated: {key} (1 entry)")

# Translate R01CAP (first stage captions)
for key in data["files"]:
    if "R01CAP_E.BIN" in key:
        entries = data["files"][key]["entries"]
        
        entries[0]["translated"] = ["Atingiu o Nivel 10 de Groove"]
        entries[1]["translated"] = ["Atingiu o Nivel 4 de Groove"]
        
        print(f"  Translated: {key} (2 entries)")

with open(TRANSLATION_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nDone! Sample translations applied.")
