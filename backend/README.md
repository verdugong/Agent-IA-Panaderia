# Backend — Fase 1→Fase 3 (routing + grafo + API)

## Requisitos
- Python 3.10+ (recomendado 3.11)
- VS Code

## Instalación
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# mac/linux:
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt
```

## 1) Crear BD + sembrar funciones (incluye embeddings)
```bash
python -m scripts.seed_functions
```

Genera:
- `./data/agent.db` (SQLite)
- `./data/faiss_index/` (índice vectorial local)

## 2) Correr tests de routing
```bash
pytest -q
```

## 3) Levantar API
```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints:
- `GET /health`
- `GET /functions`
- `POST /chat` (query → routing → (stub planner/exec) → respuesta)
- `GET /graph/mermaid` (código Mermaid del grafo LangGraph)
