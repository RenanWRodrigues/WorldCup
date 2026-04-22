# ⚽ Copa do Mundo FIFA — Dashboard Interativo

Dashboard interativo para exploração dos dados históricos da Copa do Mundo FIFA (1930–2014), construído com Python, Streamlit e Plotly.

## Visão Geral

O projeto apresenta análises visuais sobre todas as edições do torneio, permitindo filtrar por período e seleção para explorar estatísticas de jogos, gols, países e artilheiros.

## Funcionalidades

- **Edições & Tendências** — gols por edição, público total, títulos por país e evolução do número de equipes
- **Análise de Partidas** — distribuição de resultados, gols por fase, média de gols por jogo e top estádios
- **Seleções** — ranking de gols e vitórias, histórico individual por seleção e tabela geral de desempenho
- **Artilheiros** — top 20 jogadores históricos, gols por seleção e distribuição por posição

## Tecnologias

| Biblioteca | Versão |
|------------|--------|
| Python     | 3.12+  |
| Streamlit  | 1.56   |
| Pandas     | 3.0    |
| Plotly     | 6.7    |

## Dados

Os dados são provenientes do [FIFA World Cup Dataset](https://www.kaggle.com/datasets/abecklas/fifa-world-cup) e cobrem todas as edições da Copa do Mundo de 1930 a 2014.

Arquivos utilizados:
- `WorldCups.csv` — uma linha por torneio (sede, campeão, público, gols)
- `WorldCupMatches.csv` — uma linha por partida (times, gols, estádio, fase)
- `WorldCupPlayers.csv` — uma linha por jogador/partida (eventos, gols marcados)

## Como Executar

**1. Clone o repositório**
```bash
git clone https://github.com/RenanWRodrigues/WorldCup.git
cd WorldCup
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Execute o dashboard**
```bash
streamlit run dashboard.py
```

O dashboard abrirá automaticamente em `http://localhost:8501`.

## Estrutura do Projeto

```
WorldCup/
├── dashboard.py          # Aplicação principal
├── requirements.txt      # Dependências do projeto
├── WorldCups.csv         # Dados por torneio
├── WorldCupMatches.csv   # Dados por partida
└── WorldCupPlayers.csv   # Dados por jogador
```
