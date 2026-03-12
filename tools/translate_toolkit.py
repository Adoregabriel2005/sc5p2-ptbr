"""
Space Channel 5 Part 2 — Complete Translation Toolkit
=====================================================
Extracts ALL game text (DGCP CAP files + CTL_TEXT.AFS) into a single JSON file
for easy translation. Supports rebuilding modified files and injecting back into CVM.

Usage:
  python translate_toolkit.py extract   - Extract all text to translation JSON
  python translate_toolkit.py build     - Build translated BIN files from JSON
  python translate_toolkit.py inject    - Inject translated files back into CVM
  python translate_toolkit.py status    - Show translation progress
"""
import struct
import json
import os
import sys
import shutil
import datetime

# === CONFIGURATION ===
GAME_DIR = r"D:\ROMS\ps2\Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)"
PROJECT_DIR = r"C:\Users\gorigamia\Desktop\game"
EXTRACTED_DIR = os.path.join(PROJECT_DIR, "extracted")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
BACKUP_DIR = os.path.join(PROJECT_DIR, "backup")
TRANSLATION_FILE = os.path.join(PROJECT_DIR, "translation.json")
LOG_FILE = os.path.join(PROJECT_DIR, "translation_log.txt")

# Language suffixes in the game files
# We'll read English (_E) as source, and replace Italian (_I) with Portuguese
SOURCE_LANG = "_E"    # English
TARGET_LANG = "_I"    # Italian -> will become Portuguese

CVM_FILES = ['ch52_g.cvm', 'ch52_g50.cvm']


def log(message):
    """Write to both console and log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


# ============================================================
# DGCP FORMAT PARSER / BUILDER
# ============================================================

def parse_dgcp(data):
    """Parse DGCP binary data into a list of text entries."""
    if data[:4] != b'DGCP':
        return None
    
    count = struct.unpack('<I', data[4:8])[0]
    entries = []
    
    for i in range(count):
        off = 16 + i * 8
        line_count = struct.unpack('<I', data[off:off+4])[0]
        ptr_offset = struct.unpack('<I', data[off+4:off+8])[0]
        
        lines = []
        for j in range(line_count):
            str_ptr_off = ptr_offset + j * 4
            str_offset = struct.unpack('<I', data[str_ptr_off:str_ptr_off+4])[0]
            end = data.find(b'\x00', str_offset)
            if end == -1:
                end = len(data)
            text = data[str_offset:end].decode('latin-1', errors='replace')
            lines.append(text)
        
        entries.append(lines)
    
    return entries


def build_dgcp(entries):
    """Build DGCP binary data from a list of text entries.
    
    entries: list of lists of strings
    Returns: bytes
    """
    count = len(entries)
    
    # Calculate layout
    # Header: 16 bytes (magic + count + padding)
    # Entry table: count * 8 bytes
    # String pointer arrays: sum of line_counts * 4 bytes
    # Strings: null-terminated strings
    
    header_size = 16
    entry_table_size = count * 8
    
    # Calculate total pointer array size
    ptr_array_offset = header_size + entry_table_size
    total_ptrs = sum(len(e) for e in entries)
    ptr_array_size = total_ptrs * 4
    
    strings_start = ptr_array_offset + ptr_array_size
    
    # Encode all strings and calculate their offsets
    encoded_strings = []
    string_offsets = []
    current_string_offset = strings_start
    
    for entry in entries:
        entry_offsets = []
        for text in entry:
            encoded = text.encode('latin-1', errors='replace') + b'\x00'
            entry_offsets.append(current_string_offset)
            encoded_strings.append(encoded)
            current_string_offset += len(encoded)
        string_offsets.append(entry_offsets)
    
    # Build binary
    result = bytearray()
    
    # Header
    result.extend(b'DGCP')
    result.extend(struct.pack('<I', count))
    result.extend(b'\x00' * 8)
    
    # Entry table + pointer arrays
    current_ptr_offset = ptr_array_offset
    for i, entry in enumerate(entries):
        line_count = len(entry)
        result.extend(struct.pack('<I', line_count))
        result.extend(struct.pack('<I', current_ptr_offset))
        current_ptr_offset += line_count * 4
    
    # Pointer arrays (string offsets)
    for i, entry in enumerate(entries):
        for offset in string_offsets[i]:
            result.extend(struct.pack('<I', offset))
    
    # Strings
    for encoded in encoded_strings:
        result.extend(encoded)
    
    return bytes(result)


# ============================================================
# CTL_TEXT.AFS FORMAT PARSER / BUILDER
# ============================================================

def parse_afs(data):
    """Parse AFS container, return list of (offset, size, content)."""
    if data[:4] != b'AFS\x00':
        return None
    
    count = struct.unpack('<I', data[4:8])[0]
    entries = []
    
    for i in range(count):
        off = struct.unpack('<I', data[8 + i*8:12 + i*8])[0]
        size = struct.unpack('<I', data[12 + i*8:16 + i*8])[0]
        content = data[off:off+size]
        entries.append({
            'index': i,
            'offset': off,
            'size': size,
            'content': content,
        })
    
    return entries


def parse_ctl_text_entry(content):
    """Parse a single CTL_TEXT entry (plain text format)."""
    text = content.decode('latin-1', errors='replace')
    return text


# ============================================================
# CVM FILESYSTEM
# ============================================================

def get_cvm_info(cvm_path):
    """Get ISO base offset and file entries from CVM."""
    with open(cvm_path, 'rb') as f:
        f.seek(0)
        search_data = f.read(1024 * 1024)
        pvd_offset = search_data.find(b'\x01CD001')
        if pvd_offset == -1:
            raise ValueError("Cannot find ISO 9660 PVD")
        
        iso_base = pvd_offset - 16 * 2048
        
        # Parse PVD for root directory
        pvd = search_data[pvd_offset:pvd_offset+2048]
        root_record = pvd[156:190]
        root_loc = struct.unpack('<I', root_record[2:6])[0]
        root_size = struct.unpack('<I', root_record[10:14])[0]
        
        # Parse directory
        entries = parse_iso_directory(f, iso_base, root_loc, root_size)
    
    return iso_base, entries


def parse_iso_directory(f, iso_base, sector, size, prefix=""):
    """Parse ISO 9660 directory entries."""
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
                sub = parse_iso_directory(f, iso_base, extent, data_len, full_path + '/')
                entries.extend(sub)
        
        offset += rec_len
    
    return entries


# ============================================================
# EXTRACT COMMAND
# ============================================================

def cmd_extract():
    """Extract all game text into translation.json"""
    log("=" * 60)
    log("EXTRACT: Starting text extraction")
    
    translation = {
        "_meta": {
            "game": "Space Channel 5 Part 2 (PS2 PAL)",
            "source_language": "English",
            "target_language": "Português (BR)",
            "source_suffix": SOURCE_LANG,
            "target_suffix": TARGET_LANG,
            "created": datetime.datetime.now().isoformat(),
        },
        "files": {}
    }
    
    total_strings = 0
    
    for cvm_name in CVM_FILES:
        cvm_path = os.path.join(GAME_DIR, cvm_name)
        if not os.path.exists(cvm_path):
            log(f"  WARNING: {cvm_name} not found, skipping")
            continue
        
        log(f"  Processing {cvm_name}...")
        iso_base, entries = get_cvm_info(cvm_path)
        cvm_label = cvm_name.replace('.cvm', '')
        
        with open(cvm_path, 'rb') as f:
            # Process DGCP CAP files (English _E versions as source)
            cap_files = [e for e in entries if not e['is_dir'] and 
                        e['name'].upper().endswith('.BIN') and
                        ('CAP' in e['name'].upper())]
            
            # Group by base name (without language suffix)
            for entry in cap_files:
                name = entry['name']
                name_upper = name.upper()
                
                # Only process English source files
                if SOURCE_LANG.upper() not in name_upper:
                    continue
                
                # Read file data
                f.seek(iso_base + entry['sector'] * 2048)
                data = f.read(entry['size'])
                
                # Parse DGCP
                text_entries = parse_dgcp(data)
                if text_entries is None:
                    log(f"    WARNING: {name} is not DGCP format, skipping")
                    continue
                
                # Determine the corresponding target file name
                base_name = name.upper().replace(SOURCE_LANG.upper() + '.BIN', '')
                # Find the target language file
                target_name = None
                for te in entries:
                    tn = te['name'].upper()
                    if tn.startswith(base_name) and TARGET_LANG.upper() in tn and tn.endswith('.BIN'):
                        target_name = te['name']
                        break
                
                if target_name is None:
                    # Some files like WARNCAPE.BIN have different naming
                    # Try to find the Italian equivalent
                    if name_upper.startswith('WARNCAP'):
                        target_name = name_upper.replace('WARNCAPE', 'WARNCAPI')
                    else:
                        log(f"    WARNING: No target file found for {name}")
                        continue
                
                file_key = f"{cvm_label}/{name}"
                target_key = f"{cvm_label}/{target_name}"
                
                file_data = {
                    "source_file": name,
                    "target_file": target_name,
                    "cvm": cvm_name,
                    "type": "DGCP",
                    "entries": []
                }
                
                for idx, lines in enumerate(text_entries):
                    entry_data = {
                        "id": idx,
                        "original": lines,
                        "translated": [""] * len(lines),
                    }
                    file_data["entries"].append(entry_data)
                    total_strings += len(lines)
                
                translation["files"][file_key] = file_data
                log(f"    {name} -> {target_name}: {len(text_entries)} entries")
            
            # Process CTL_TEXT.AFS
            ctl_entries = [e for e in entries if e['name'] == 'CTL_TEXT.AFS']
            for ctl_entry in ctl_entries:
                f.seek(iso_base + ctl_entry['sector'] * 2048)
                afs_data = f.read(ctl_entry['size'])
                afs_entries = parse_afs(afs_data)
                
                if afs_entries:
                    file_key = f"{cvm_label}/CTL_TEXT.AFS"
                    file_data = {
                        "source_file": "CTL_TEXT.AFS",
                        "target_file": "CTL_TEXT.AFS",
                        "cvm": cvm_name,
                        "type": "AFS_TEXT",
                        "entries": []
                    }
                    
                    for ae in afs_entries:
                        if ae['size'] > 0:
                            text = parse_ctl_text_entry(ae['content'])
                            entry_data = {
                                "id": ae['index'],
                                "original": [text],
                                "translated": [""],
                            }
                            file_data["entries"].append(entry_data)
                            total_strings += 1
                    
                    translation["files"][file_key] = file_data
                    log(f"    CTL_TEXT.AFS: {len(afs_entries)} entries")
    
    # Process WARNCAP files (special naming: WARNCAPE.BIN -> WARNCAPS.BIN)
    for cvm_name in CVM_FILES:
        cvm_path = os.path.join(GAME_DIR, cvm_name)
        if not os.path.exists(cvm_path):
            continue
        iso_base, entries = get_cvm_info(cvm_path)
        cvm_label = cvm_name.replace('.cvm', '')
        
        with open(cvm_path, 'rb') as f:
            warn_e = [e for e in entries if e['name'].upper().startswith('WARNCAP') and 'E.' in e['name'].upper()]
            for entry in warn_e:
                name = entry['name']
                file_key = f"{cvm_label}/{name}"
                if file_key in translation["files"]:
                    continue
                
                f.seek(iso_base + entry['sector'] * 2048)
                data = f.read(entry['size'])
                text_entries = parse_dgcp(data)
                if text_entries is None:
                    continue
                
                target_name = name.replace('E.', 'I.')
                target_exists = any(e['name'] == target_name for e in entries)
                if not target_exists:
                    continue
                
                file_data = {
                    "source_file": name,
                    "target_file": target_name,
                    "cvm": cvm_name,
                    "type": "DGCP",
                    "entries": []
                }
                
                for idx, lines in enumerate(text_entries):
                    entry_data = {
                        "id": idx,
                        "original": lines,
                        "translated": [""] * len(lines),
                    }
                    file_data["entries"].append(entry_data)
                    total_strings += len(lines)
                
                translation["files"][file_key] = file_data
                log(f"    {name} -> {target_name}: {len(text_entries)} entries")
    
    # Process VOCAP, SYCAP, MUCAP, MAKUCAP files
    # These only have _F, _G, _I, _S versions (no English _E)
    # We use the Spanish _S as source (since PT-BR will replace it)
    # and also read English equivalent from _F for reference context
    vocap_patterns = ['VOCAP', 'SYCAP', 'MUCAP', 'MAKUCAP']
    
    for cvm_name in CVM_FILES:
        cvm_path = os.path.join(GAME_DIR, cvm_name)
        if not os.path.exists(cvm_path):
            continue
        iso_base, entries = get_cvm_info(cvm_path)
        cvm_label = cvm_name.replace('.cvm', '')
        
        with open(cvm_path, 'rb') as f:
            for entry in entries:
                if entry['is_dir']:
                    continue
                name = entry['name']
                name_upper = name.upper()
                
                # Only process Italian _I versions of these file types
                if not name_upper.endswith('_I.BIN'):
                    continue
                if not any(p in name_upper for p in vocap_patterns):
                    continue
                
                file_key = f"{cvm_label}/{name}"
                if file_key in translation["files"]:
                    continue
                
                f.seek(iso_base + entry['sector'] * 2048)
                data = f.read(entry['size'])
                text_entries = parse_dgcp(data)
                if text_entries is None:
                    continue
                
                file_data = {
                    "source_file": name,
                    "target_file": name,  # Same file (overwrite Spanish)
                    "cvm": cvm_name,
                    "type": "DGCP",
                    "source_lang_note": "Italian (original _I file)",
                    "entries": []
                }
                
                for idx, lines in enumerate(text_entries):
                    entry_data = {
                        "id": idx,
                        "original": lines,
                        "translated": [""] * len(lines),
                    }
                    file_data["entries"].append(entry_data)
                    total_strings += len(lines)
                
                translation["files"][file_key] = file_data
                log(f"    {name} (IT->PT): {len(text_entries)} entries")
    
    # Save translation file
    with open(TRANSLATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(translation, f, ensure_ascii=False, indent=2)
    
    log(f"  Total files: {len(translation['files'])}")
    log(f"  Total strings: {total_strings}")
    log(f"  Saved to: {TRANSLATION_FILE}")
    log("EXTRACT: Complete")


# ============================================================
# BUILD COMMAND
# ============================================================

def cmd_build():
    """Build translated BIN files from translation.json"""
    log("=" * 60)
    log("BUILD: Starting build process")
    
    if not os.path.exists(TRANSLATION_FILE):
        log("ERROR: translation.json not found. Run 'extract' first.")
        return
    
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        translation = json.load(f)
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    built_count = 0
    
    for file_key, file_data in translation["files"].items():
        file_type = file_data["type"]
        target_file = file_data["target_file"]
        cvm_name = file_data["cvm"]
        cvm_label = cvm_name.replace('.cvm', '')
        
        # Check if any translations exist
        has_translations = False
        for entry in file_data["entries"]:
            if any(t.strip() for t in entry["translated"]):
                has_translations = True
                break
        
        if not has_translations:
            continue
        
        if file_type == "DGCP":
            # Build new DGCP file
            entries = []
            for entry in file_data["entries"]:
                # Use translated text if available, fallback to original
                lines = []
                for i, orig in enumerate(entry["original"]):
                    trans = entry["translated"][i] if i < len(entry["translated"]) else ""
                    lines.append(trans.strip() if trans.strip() else orig)
                entries.append(lines)
            
            new_data = build_dgcp(entries)
            
            out_dir = os.path.join(BUILD_DIR, cvm_label)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, target_file)
            
            with open(out_path, 'wb') as f:
                f.write(new_data)
            
            built_count += 1
            log(f"  Built: {cvm_label}/{target_file} ({len(new_data)} bytes)")
        
        elif file_type == "AFS_TEXT":
            # For AFS, we need to rebuild the entire AFS container
            # This is more complex - we'll handle it separately
            log(f"  SKIP (AFS rebuild not yet implemented): {file_key}")
    
    log(f"BUILD: Complete. {built_count} files built.")


# ============================================================
# INJECT COMMAND
# ============================================================

def cmd_inject():
    """Inject translated files back into CVM containers."""
    log("=" * 60)
    log("INJECT: Starting injection process")
    
    if not os.path.exists(TRANSLATION_FILE):
        log("ERROR: translation.json not found.")
        return
    
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        translation = json.load(f)
    
    # Create backup of CVM files first
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    for cvm_name in CVM_FILES:
        cvm_path = os.path.join(GAME_DIR, cvm_name)
        backup_path = os.path.join(BACKUP_DIR, cvm_name)
        
        if not os.path.exists(backup_path):
            log(f"  Creating backup: {cvm_name}")
            shutil.copy2(cvm_path, backup_path)
            log(f"  Backup saved to: {backup_path}")
        else:
            log(f"  Backup already exists: {cvm_name}")
    
    injected_count = 0
    
    for cvm_name in CVM_FILES:
        cvm_path = os.path.join(GAME_DIR, cvm_name)
        cvm_label = cvm_name.replace('.cvm', '')
        
        iso_base, cvm_entries = get_cvm_info(cvm_path)
        
        # Find built files for this CVM
        build_subdir = os.path.join(BUILD_DIR, cvm_label)
        if not os.path.exists(build_subdir):
            continue
        
        for built_file in os.listdir(build_subdir):
            built_path = os.path.join(build_subdir, built_file)
            new_data = open(built_path, 'rb').read()
            
            # Find matching entry in CVM
            target_entry = None
            for e in cvm_entries:
                if e['name'] == built_file:
                    target_entry = e
                    break
            
            if target_entry is None:
                log(f"  WARNING: {built_file} not found in {cvm_name}")
                continue
            
            original_size = target_entry['size']
            new_size = len(new_data)
            
            if new_size > original_size:
                log(f"  WARNING: {built_file} is {new_size - original_size} bytes larger than original!")
                log(f"           Original: {original_size}, New: {new_size}")
                log(f"           Checking if padding allows it...")
                
                # Check if there's enough sector-aligned space
                # Files are stored at sector boundaries (2048 bytes)
                original_sectors = (original_size + 2047) // 2048
                new_sectors = (new_size + 2047) // 2048
                
                if new_sectors > original_sectors:
                    log(f"  ERROR: {built_file} exceeds sector allocation! Skipping.")
                    log(f"         Original sectors: {original_sectors}, Need: {new_sectors}")
                    continue
                else:
                    log(f"           OK - fits within sector allocation ({original_sectors} sectors)")
            
            # Write to CVM
            with open(cvm_path, 'r+b') as f:
                offset = iso_base + target_entry['sector'] * 2048
                f.seek(offset)
                f.write(new_data)
                # Pad with zeros to fill original size
                if new_size < original_size:
                    f.write(b'\x00' * (original_size - new_size))
            
            # Update the file size in the ISO directory record
            _update_iso_dir_size(cvm_path, iso_base, cvm_entries, built_file, new_size)
            
            injected_count += 1
            log(f"  Injected: {built_file} into {cvm_name} ({new_size} bytes)")
    
    log(f"INJECT: Complete. {injected_count} files injected.")


def _update_iso_dir_size(cvm_path, iso_base, entries, filename, new_size):
    """Update the file size in the ISO 9660 directory record.
    
    This is needed when the translated file has a different size from the original.
    We need to find the directory record and update the data length field.
    """
    with open(cvm_path, 'r+b') as f:
        # We need to find the directory entry for this file
        # Re-read the PVD to get root directory location
        f.seek(0)
        search_data = f.read(1024 * 1024)
        pvd_offset = search_data.find(b'\x01CD001')
        pvd = search_data[pvd_offset:pvd_offset+2048]
        root_record = pvd[156:190]
        root_loc = struct.unpack('<I', root_record[2:6])[0]
        root_size = struct.unpack('<I', root_record[10:14])[0]
        
        # Scan root directory for the file
        f.seek(iso_base + root_loc * 2048)
        dir_data = bytearray(f.read(root_size))
        
        offset = 0
        while offset < len(dir_data):
            rec_len = dir_data[offset]
            if rec_len == 0:
                offset = ((offset // 2048) + 1) * 2048
                if offset >= len(dir_data):
                    break
                continue
            
            name_len = dir_data[offset + 32]
            name_raw = dir_data[offset+33:offset+33+name_len]
            
            if name_raw not in (b'\x00', b'\x01'):
                name_str = name_raw.decode('ascii', errors='replace').split(';')[0]
                if name_str == filename:
                    # Update both LE and BE size fields
                    # Data length LE at offset+10, BE at offset+14
                    struct.pack_into('<I', dir_data, offset+10, new_size)
                    struct.pack_into('>I', dir_data, offset+14, new_size)
                    
                    # Write back
                    f.seek(iso_base + root_loc * 2048)
                    f.write(bytes(dir_data))
                    return True
            
            offset += rec_len
    
    return False


# ============================================================
# STATUS COMMAND
# ============================================================

def cmd_status():
    """Show translation progress."""
    if not os.path.exists(TRANSLATION_FILE):
        print("No translation.json found. Run 'extract' first.")
        return
    
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        translation = json.load(f)
    
    print("=" * 60)
    print("TRANSLATION PROGRESS")
    print("=" * 60)
    
    total_strings = 0
    translated_strings = 0
    
    for file_key, file_data in translation["files"].items():
        file_total = 0
        file_translated = 0
        
        for entry in file_data["entries"]:
            for i, orig in enumerate(entry["original"]):
                file_total += 1
                total_strings += 1
                trans = entry["translated"][i] if i < len(entry["translated"]) else ""
                if trans.strip():
                    file_translated += 1
                    translated_strings += 1
        
        pct = (file_translated / file_total * 100) if file_total > 0 else 0
        status = "DONE" if file_translated == file_total else f"{pct:.0f}%"
        
        if file_translated > 0 or True:  # Show all files
            print(f"  {file_key:50s} {file_translated:4d}/{file_total:4d} [{status}]")
    
    print()
    pct = (translated_strings / total_strings * 100) if total_strings > 0 else 0
    print(f"  TOTAL: {translated_strings}/{total_strings} strings ({pct:.1f}%)")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'extract':
        cmd_extract()
    elif command == 'build':
        cmd_build()
    elif command == 'inject':
        cmd_inject()
    elif command == 'status':
        cmd_status()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
