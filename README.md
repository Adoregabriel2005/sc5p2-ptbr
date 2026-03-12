# 🇧🇷 Space Channel 5 Part 2 — Tradução PT-BR

> ⚠️ **Projeto em fase inicial** — Apenas textos fora de texturas foram traduzidos até o momento. Textos embutidos em imagens/texturas do jogo ainda não foram alterados.

> 🎮 **Testado apenas no PCSX2** — Não há garantia de funcionamento em console real ou outros emuladores.

Tradução para **Português Brasileiro** do Space Channel 5 Part 2 (PS2 PAL Europe).

## O Jogo

**Space Channel 5 Part 2** é um jogo musical de ritmo desenvolvido pela **United Game Artists** e publicado pela **SEGA** em 2002. Lançado originalmente para Dreamcast (apenas no Japão) e PlayStation 2 (mundial), o jogo segue a repórter **Ulala** do canal espacial 5, que precisa salvar a galáxia dançando e derrotando inimigos ao ritmo da música. Um grupo misterioso chamado Rhythm Rogues está forçando pessoas a dançar contra a vontade, e cabe a Ulala deter seus planos usando o poder da dança. O jogo nunca recebeu tradução para português.

## Sobre o Projeto

Este projeto traduz os textos do jogo de Italiano para Português Brasileiro, substituindo os arquivos `_I` (Italiano) dentro dos containers CVM do jogo. Apenas os textos armazenados em arquivos binários (DGCP) foram extraídos e traduzidos — textos que fazem parte de texturas/imagens ainda não foram abordados.

**Cobertura dos textos DGCP:** 99.8% traduzidos (4222/4230 entradas)

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
├── textures/
│   ├── com_texto/            ← Texturas com texto por idioma (precisam tradução!)
│   ├── sem_texto/            ← Texturas gerais (mapas, fontes, etc.)
│   └── LEIA-ME.txt           ← Guia sobre os formatos de textura
├── tools/
│   ├── translate_toolkit.py  ← Pipeline principal (extract/build/inject/status)
│   ├── translate_all.py      ← Script com todas as traduções PT-BR
│   ├── extract_textures.py   ← Extrator de texturas do CVM
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

## Contribua! (Open Source)

Este é um projeto **open source** e qualquer pessoa pode ajudar! Veja o que precisa ser feito:

### O que falta
- 🎨 **Texturas com texto** — As imagens do jogo (tela de título, menus de pausa, loading, resultados) ainda estão em italiano. Os arquivos estão extraídos na pasta `textures/com_texto/` prontos para edição.
- 📝 **Revisão de traduções** — Os textos já traduzidos podem ser revisados e melhorados em `translation.json`.
- 🔧 **Conversor PTM ↔ PNG** — Precisamos de uma ferramenta para converter as texturas PS2 para PNG e de volta.
- 🎮 **Testes** — Testar o jogo completo no PCSX2 e reportar bugs.

### Como começar a contribuir
1. Faça um **fork** do repositório
2. Clone e configure o ambiente (veja instruções acima)
3. Escolha uma tarefa e mãos à obra
4. Envie um **Pull Request**

Veja o guia completo em [CONTRIBUTING.md](CONTRIBUTING.md).

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

MIT License — Veja [LICENSE](LICENSE) para detalhes.

Projeto de fan translation sem fins lucrativos. Space Channel 5 Part 2 © SEGA.
