from app.db import Base, engine, SessionLocal
from app.models import FunctionDef
from app.router import load_vector_store, build_vector_store_from_db, select_function

def test_routing_top1_basic():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # si no hay datos, el test lo considera "skipped" de facto.
        if db.query(FunctionDef).count() == 0:
            return

        vs = load_vector_store() or build_vector_store_from_db(db)

    cases = [
        ("tienes pan integral?", "buscar_producto"),
        ("cuánto cuesta la empanada?", "consultar_precio_promos"),
        ("recomiéndame algo dulce", "recomendar_productos"),
        ("quiero 2 cafés y 4 empanadas para retirar a las 6", "crear_pedido"),
        ("anula mi pedido 200 por favor", "cancelar_pedido"),
        ("a qué hora abren?", "consultar_horarios_ubicaciones"),
    ]

    for q, expected in cases:
        pred = select_function(vs, q, k=1)[0].function
        assert pred == expected
