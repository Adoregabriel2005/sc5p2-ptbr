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

## Fluxo Visual do Projeto

<div align="center">
	<img src="docs/fluxo_projeto_sc5p2.png" alt="Fluxo do Projeto Space Channel 5 PT-BR" width="420"/>
</div>

**Como funciona:**
- A ISO original é o ponto de partida.
- Os textos e texturas são extraídos e editados usando as ferramentas do projeto.
- As traduções e texturas editadas podem ser aplicadas de duas formas: criando uma nova ISO traduzida ou usando o patch de texturas HD no PCSX2.
- O usuário pode escolher o caminho mais fácil para jogar ou contribuir.

> *O diagrama acima foi inspirado no visual da capa do álbum, com fundo azul, linhas curvas e setas conectando as etapas para facilitar o entendimento de quem está começando.*

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
│   ├── ptm_viewer.py         ← Conversor PTM → PNG (texturas PS2)
│   ├── search_text.py        ← Busca em textos originais e traduzidos
│   ├── validate.py           ← Validação de traduções (encoding, tamanho)
│   ├── status.py             ← Dashboard de progresso detalhado
│   ├── edit_translation.py   ← Editor rápido de traduções via CLI
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

## Ferramentas para Contribuidores

### 🔍 Busca de texto
```bash
python tools/search_text.py "ulala"                    # Busca em tudo
python tools/search_text.py "dança" --only translated  # Só nas traduções
python tools/search_text.py --untranslated --file R01  # Ver o que falta
```

### 📊 Status do progresso
```bash
python tools/status.py               # Resumo com barra de progresso
python tools/status.py --detailed    # Lista cada arquivo
```

### ✅ Validação
```bash
python tools/validate.py             # Verifica encoding e tamanho
python tools/validate.py --file R01  # Validar arquivo específico
```

### ✏️ Editor rápido
```bash
python tools/edit_translation.py TITCAP --list       # Listar entradas
python tools/edit_translation.py TITCAP 0 --show     # Ver entrada
python tools/edit_translation.py TITCAP 0 "Novo Jogo" "Continuar"  # Editar
```

### 🖼️ Visualizar texturas
```bash
pip install Pillow
python tools/ptm_viewer.py                            # Converte texturas com texto → PNG
python tools/ptm_viewer.py --all                      # Converte TODAS as texturas
python tools/ptm_viewer.py textures/com_texto/TITLE_I.PTM  # Uma específica
```
Os PNGs são salvos em `textures_png/`.

## Patch de Texturas HD no PCSX2 (sem mexer na ISO)

O PCSX2 (v1.7+) permite usar texturas HD facilmente: basta ativar "Texture Replacement" e colocar PNGs editados na pasta:
- Windows: `%UserProfile%/Documents/PCSX2/textures/SCES-50612/`
- Linux: `~/.config/PCSX2/textures/SCES-50612/`

**Como criar um pack HD:**
1. Extraia as texturas PTM para PNG com `python tools/ptm_viewer.py --all` (salva em `textures_png/`).
2. Edite os PNGs mantendo o nome original.
3. Coloque os PNGs editados na pasta acima e jogue normalmente — o PCSX2 troca as texturas na hora.

**Resolução máxima recomendada:** até 4x a original (ex: 256x256 → 1024x1024). Acima disso pode causar bugs ou não carregar.

**Ferramentas úteis para tratar texturas:**
- Edição: GIMP, Photoshop, Photopea (online)
- Upscale: waifu2x, ESRGAN
- Otimização PNG: PNGGauntlet, pngquant

Assim, qualquer um pode criar, testar e compartilhar texturas HD sem precisar modificar a ISO!

## Contribua! (Open Source)

Este é um projeto **open source** e qualquer pessoa pode ajudar! Veja o que precisa ser feito:

### O que falta
- 🎨 **Texturas com texto** — As imagens do jogo (tela de título, menus de pausa, loading, resultados) ainda estão em italiano. Os arquivos estão extraídos na pasta `textures/com_texto/` e podem ser visualizados como PNG com `ptm_viewer.py`.
- 📝 **Revisão de traduções** — Os textos já traduzidos podem ser revisados e melhorados (use `search_text.py` e `validate.py` para encontrar problemas).
- 🔧 **Conversor PNG → PTM** — O `ptm_viewer.py` converte PTM→PNG, mas falta o caminho inverso para reinjetar texturas editadas.
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
