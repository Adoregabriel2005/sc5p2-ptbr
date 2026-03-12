# 🇧🇷 Space Channel 5 Part 2 — Tradução PT-BR

Tradução para **Português Brasileiro** do Space Channel 5 Part 2 (PS2 PAL Europe).

## Sobre

Este projeto traduz todos os textos do jogo de Italiano para Português Brasileiro, substituindo os arquivos `_I` (Italiano) dentro dos containers CVM do jogo.

**Cobertura:** 99.8% dos textos traduzidos (4222/4230 entradas)

### O que é traduzido

| Tipo | Arquivo | Conteúdo |
|------|---------|----------|
| CAP | `R##CAP_I.BIN` | Diálogos e legendas de cada fase (Report) |
| CAP | `TITCAP_I.BIN` | Menus, título e opções |
| CAP | `WARNCAPI.BIN` | Avisos de Memory Card/Save |
| CAP | `COSCAP_I.BIN` | Nomes e descrições de roupas/figurinos |
| VOCAP | `R##VOCAP_I.BIN` | Legendas de vozes/narração |
| SYCAP | `R#SYCAP_I.BIN` | Mensagens de sistema durante gameplay |
| MUCAP | `R62MUCAP_I.BIN`, `MAKUCAP_I.BIN` | Legendas de cutscenes e final |

## Como Usar

### Pré-requisitos
- Python 3.10+
- ISO do Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It) extraída
- [UltraISO](https://www.ultraiso.com/) para reconstruir a ISO
- [PCSX2](https://pcsx2.net/) para jogar

### Pipeline completo

```bash
# 1. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Extrair textos do jogo (gera translation.json)
python tools/translate_toolkit.py extract

# 3. Aplicar todas as traduções PT-BR
python tools/translate_all.py

# 4. Compilar arquivos traduzidos
python tools/translate_toolkit.py build

# 5. Injetar nos CVMs
python tools/translate_toolkit.py inject

# 6. Preparar arquivos para UltraISO
python tools/prepare_ultraiso.py
```

### Reconstruir ISO com UltraISO

1. Abra a ISO original no UltraISO
2. Substitua todos os arquivos pelos da pasta `iso_files/`
3. Salve como nova ISO (Standard ISO, Label: `SCES_50612`)
4. Jogue no PCSX2 com o BIOS configurado para idioma **Italiano**

## Estrutura do Projeto

```
├── translation.json          ← Banco de dados de traduções
├── tools/
│   ├── translate_toolkit.py  ← Pipeline principal (extract/build/inject/status)
│   ├── translate_all.py      ← Script com todas as traduções PT-BR
│   ├── export_text.py        ← Exportar textos em formato legível
│   ├── prepare_ultraiso.py   ← Preparar arquivos para UltraISO
│   ├── afs_parser.py         ← Parser de containers AFS
│   ├── cap_parser.py         ← Parser de arquivos DGCP
│   ├── cvm_extract.py        ← Extrator de arquivos CVM
│   └── cvm_list.py           ← Listar conteúdo de CVMs
├── build/                    ← Arquivos compilados (gerado)
├── backup/                   ← Backup dos CVMs originais (gerado)
└── iso_files/                ← Arquivos para UltraISO (gerado)
```

## Formato Técnico

- **CVM**: Container com CVMH header + ROFS + ISO 9660
- **DGCP**: Formato binário de legendas — header `DGCP` + tabela de entradas + ponteiros + strings null-terminated
- **Encoding**: Latin-1 (ISO 8859-1) — suporta acentos (ã, õ, ç, é, ê, á, í, ó, ú, â)
- **Idioma alvo**: Italiano (`_I`) é substituído por PT-BR

## Estatísticas

- **96 arquivos** de texto (48 únicos × 2 CVMs)
- **4230 strings** no total
- **3002 traduções** aplicadas
- **99.8%** de cobertura

## Licença

Projeto de fan translation sem fins lucrativos. Space Channel 5 Part 2 © SEGA.
