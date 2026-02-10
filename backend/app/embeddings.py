from langchain_community.embeddings import HuggingFaceEmbeddings
from .settings import settings

def build_embedder():
    # normalize_embeddings=True para que L2 ~ coseno
    return HuggingFaceEmbeddings(
        model_name=settings.EMB_MODEL_NAME,
        encode_kwargs={"normalize_embeddings": True},
    )
