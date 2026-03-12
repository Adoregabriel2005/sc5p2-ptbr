"""
Prepare a clean folder with all game files (modified CVMs included)
ready for UltraISO to rebuild the PS2 ISO.
"""
import os
import shutil

GAME_DIR = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
OUTPUT_DIR = r"C:\Users\gorigamia\Desktop\game\iso_files"


def prepare():
    print("=== Preparando pasta para UltraISO ===\n")

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copy all files preserving structure
    for item in sorted(os.listdir(GAME_DIR)):
        src = os.path.join(GAME_DIR, item)
        dst = os.path.join(OUTPUT_DIR, item)

        if os.path.isdir(src):
            print(f"  Copiando pasta: {item}/")
            shutil.copytree(src, dst)
        else:
            size = os.path.getsize(src)
            print(f"  Copiando: {item} ({size:,} bytes)")
            shutil.copy2(src, dst)

    print(f"\n=== Pronto! ===")
    print(f"Pasta: {OUTPUT_DIR}")
    print(f"\nConteudo:")
    for item in sorted(os.listdir(OUTPUT_DIR)):
        full = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(full):
            count = len(os.listdir(full))
            print(f"  [DIR] {item}/ ({count} arquivos)")
        else:
            print(f"  [ARQ] {item} ({os.path.getsize(full):,} bytes)")


if __name__ == '__main__':
    prepare()
