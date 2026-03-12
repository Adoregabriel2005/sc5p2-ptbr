# Como Contribuir

Obrigado por querer ajudar na tradução PT-BR do Space Channel 5 Part 2! 🎶

## O que precisa de ajuda

### 🎨 Texturas com texto (prioridade!)
As texturas na pasta `textures/com_texto/` contêm texto em imagens que precisam ser editadas manualmente. Os arquivos com sufixo `I` (italiano) são os que o jogo carrega:

| Arquivo | Conteúdo |
|---------|----------|
| `TITLE_I.PTM` | Tela de título |
| `PAUSE_I.PTM` | Menu de pausa |
| `R00_I.PTM` | Tela de intro/Report |
| `COSROOMI.PTM` | Sala de figurinos |
| `NOWLOAD0I.PTM` | Tela de loading |
| `NOWLOAD1I.PTM` | Tela de loading (detalhada) |
| `RESULT0I.PTM` | Tela de resultados |
| `RESULT1I.PTM` | Tela de resultados |

**Formato:** Os arquivos `.PTM` são texturas PS2 em formato raw. É necessário fazer engenharia reversa do formato ou usar ferramentas como Rainbow para converter para PNG, editar e converter de volta.

### 📝 Revisão de traduções de texto
O arquivo `translation.json` contém todas as traduções. Revise e melhore as traduções existentes.

### 🔧 Ferramentas
Melhore as ferramentas em `tools/` — por exemplo, criar um conversor PTM ↔ PNG.

## Como começar

### 1. Clone o repositório
```bash
git clone https://github.com/Adoregabriel2005/sc5p2-ptbr.git
cd sc5p2-ptbr
```

### 2. Configure o ambiente
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# ou: source .venv/bin/activate  # Linux/Mac
```

### 3. Obtenha a ISO do jogo
Você precisa da ISO do **Space Channel 5 Part 2 (Europe) (En,Fr,De,Es,It)** extraída em uma pasta. Atualize o caminho em `tools/translate_toolkit.py`:
```python
GAME_DIR = Path("seu/caminho/para/a/iso/extraida")
```

### 4. Extraia os textos
```bash
python tools/translate_toolkit.py extract
```

### 5. Faça suas alterações
- **Textos:** Edite `translation.json`
- **Texturas:** Edite os arquivos em `textures/com_texto/`

### 6. Teste
```bash
python tools/translate_toolkit.py build
python tools/translate_toolkit.py inject
python tools/prepare_ultraiso.py
```
Reconstrua a ISO com UltraISO e teste no PCSX2.

### 7. Envie um Pull Request
```bash
git checkout -b minha-contribuicao
git add -A
git commit -m "Descrição da sua contribuição"
git push origin minha-contribuicao
```
Abra um PR no GitHub descrevendo o que você fez.

## Regras

- Mantenha as traduções naturais em PT-BR (não traduções literais)
- Respeite o limite de caracteres — textos muito longos podem não caber na tela
- Teste no PCSX2 antes de enviar um PR
- Não inclua a ISO ou arquivos CVM no repositório
