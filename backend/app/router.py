import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from .models import FunctionDef
from .embeddings import build_embedder
from .settings import settings

@dataclass
class RouteResult:
    function: str
    score: float

def _split_examples(examples: list[str]) -> list[str]:
    out = []
    for ex in examples:
        ex = ex.strip()
        if not ex:
            continue
        # divide por '/' si vienen pegados
        parts = [p.strip() for p in ex.replace("|","/").split("/") if p.strip()]
        out.extend(parts)
    return out

def build_vector_store_from_db(db: Session) -> FAISS:
    embedder = build_embedder()
    rows = db.query(FunctionDef).all()

    docs: list[Document] = []
    for r in rows:
        fn = r.name
        docs.append(Document(
            page_content=f"Función {fn}. Intención: {r.business_desc}. Técnica: {r.technical_desc}",
            metadata={"name": fn, "kind": "desc"},
        ))
        examples = _split_examples(json.loads(r.query_examples))
        for ex in examples:
            docs.append(Document(
                page_content=f"Ejemplo de uso de {fn}: {ex}",
                metadata={"name": fn, "kind": "example"},
            ))

    vs = FAISS.from_documents(docs, embedder)
    # persistimos para arrancar rápido después
    vs.save_local(settings.FAISS_DIR)
    return vs

def load_vector_store() -> Optional[FAISS]:
    try:
        embedder = build_embedder()
        return FAISS.load_local(settings.FAISS_DIR, embedder, allow_dangerous_deserialization=True)
    except Exception:
        return None

def select_function(vs: FAISS, query: str, k: int = 1, k_docs: int = 12) -> List[RouteResult]:
    """Devuelve Top-k funciones por routing semántico.
    k: número de funciones a devolver (en tu práctica, k=1).
    k_docs: cuantos docs recuperar para luego agregar por función.
    """
    results = vs.similarity_search_with_score(query, k=k_docs)

    by_fn: dict[str, float] = {}
    for doc, score in results:
        # con embeddings normalizados, FAISS score suele ser distancia L2^2.
        cos_sim = 1 - (score / 2)
        fn = doc.metadata["name"]
        by_fn[fn] = max(by_fn.get(fn, -1.0), float(cos_sim))

    ranked = sorted(by_fn.items(), key=lambda x: x[1], reverse=True)
    return [RouteResult(function=fn, score=sc) for fn, sc in ranked[:k]]
