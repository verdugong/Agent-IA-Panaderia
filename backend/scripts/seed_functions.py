import os, json
from sqlalchemy.orm import Session

from app.db import Base, engine, SessionLocal
from app.models import FunctionDef
from app.embeddings import build_embedder
from app.router import build_vector_store_from_db
from app.logging_config import setup_logging

logger = setup_logging()

def ensure_dirs():
    os.makedirs("./data", exist_ok=True)

def make_functions():
    # 12 funciones (panadería) incluyendo cortesía y fuera de contexto
    return [
        # ============ FUNCIONES DE ENTRADA/CORTESIA ============
        dict(
            name="saludar_cortesia",
            business_desc="Responder saludos, preguntas de cortesía como '¿cómo estás?', despedidas y conversación amigable inicial con el cliente.",
            technical_desc="Intent recognition para saludos y cortesía: detecta saludos, despedidas, preguntas personales al bot y responde amablemente.",
            input_schema={"mensaje": "string"},
            output_schema={"respuesta": "string", "sugerencia": "string?"},
            enums={"tipo": ["saludo", "despedida", "cortesia", "agradecimiento"]},
            query_examples=[
                "Hola",
                "Buenos días",
                "¿Cómo estás?",
                "¿Qué tal?",
                "Buenas tardes",
                "Gracias",
                "Muchas gracias por tu ayuda",
                "Hasta luego",
                "Chao",
                "Adiós"
            ],
        ),
        # ============ FUNCIONES DE FALLBACK ============
        dict(
            name="responder_fuera_contexto",
            business_desc="Responder cuando el cliente pregunta algo que no tiene relación con la panadería, como política, deportes, matemáticas, u otros temas.",
            technical_desc="Fallback handler: detecta preguntas fuera del dominio de panadería y redirige amablemente al cliente.",
            input_schema={"mensaje": "string"},
            output_schema={"respuesta": "string", "redireccion": "string"},
            enums={},
            query_examples=[
                "¿Cuánto es 2+2?",
                "¿Quién ganó el partido de ayer?",
                "¿Cuál es la capital de Francia?",
                "Háblame de política",
                "¿Qué opinas del presidente?",
                "Cuéntame un chiste",
                "¿Cómo está el clima?",
                "¿Puedes ayudarme con mi tarea de matemáticas?",
                "¿Qué me recomiendas para invertir?",
                "¿Cuál es el sentido de la vida?"
            ],
        ),
        # ============ FUNCIONES DE CONSULTA ============
        dict(
            name="buscar_producto",
            business_desc="Buscar productos del catálogo (disponibilidad, stock, categoría, restricciones como sin gluten).",
            technical_desc="Retrieval sobre catálogo: búsqueda por nombre/tags y filtros (restricciones, rango de precio, disponibilidad).",
            input_schema={"q":"string","categoria":"string?","tags":["string"],"restricciones":["string"],"max_precio":"number?"},
            output_schema={"results":[{"id":"string","nombre":"string","precio":"number","stock":"int","tags":["string"]}]},
            enums={"categorias":["pan","pasteleria","bebidas","salado"],"restricciones":["sin_gluten","sin_azucar","vegano"],"tags":["integral","dulce","salado","artesanal"]},
            query_examples=[
                "¿Tienes pan integral?",
                "Busco algo sin gluten",
                "¿Qué postres hay hoy?",
                "¿Tienen pan de masa madre?",
                "Necesito pan sin azúcar"
            ],
        ),
        dict(
            name="consultar_precio_promos",
            business_desc="Consultar precios unitarios, promociones 2x1, combos con descuento y ofertas vigentes de productos específicos.",
            technical_desc="Pricing lookup + reglas promocionales: aplica combos/descuentos y retorna precio final.",
            input_schema={"producto":"string?","categoria":"string?","cantidad":"number?"},
            output_schema={"precios":[{"producto":"string","precio_unit":"number","promo":"string?","precio_final":"number"}]},
            enums={"promos":["2x1","combo_desayuno","descuento_docena","happy_hour"]},
            query_examples=[
                "¿Cuánto cuesta la empanada?",
                "¿Cuál es el precio del pan francés?",
                "¿Cuánto sale una docena de croissants?",
                "¿Tienen promoción 2x1 hoy?",
                "¿Hay algún descuento si compro por docena?",
                "¿Precio del combo desayuno?",
                "¿Cuánto vale el café con leche?",
                "¿Hay ofertas en pastelería?"
            ],
        ),
        dict(
            name="recomendar_productos",
            business_desc="Recomendar productos según ocasión, gustos personales, presupuesto y restricciones alimentarias. Sugerir opciones.",
            technical_desc="Recommender basado en intención + restricciones: ranking de ítems por contexto (café, cumpleaños, etc.).",
            input_schema={"ocasion":"string?","preferencia":"string?","presupuesto":"number?","restricciones":["string"]},
            output_schema={"recomendaciones":[{"nombre":"string","razon":"string","precio":"number"}]},
            enums={"ocasion":["desayuno","cafe","cumpleanos","reunion"],"restricciones":["sin_gluten","sin_azucar","vegano"]},
            query_examples=[
                "Recomiéndame algo dulce",
                "¿Qué me sugieres para acompañar el café?",
                "Sugiereme algo para un cumpleaños",
                "¿Qué me recomiendas si tengo 10 dólares?",
                "Dame opciones para una reunión de trabajo",
                "¿Qué postre me recomiendas?",
                "Necesito ideas para un desayuno especial",
                "¿Qué me sugieres sin gluten?"
            ],
        ),
        dict(
            name="crear_pedido",
            business_desc="Crear un pedido con ítems y tipo de entrega (retiro/delivery).",
            technical_desc="Order creation: valida items, calcula total, crea registro y retorna pedido_id + ETA.",
            input_schema={"items":[{"producto":"string","cantidad":"number","unidad":"string"}],"entrega":"string","hora":"string?","cliente":{"nombre":"string?","telefono":"string?"},"direccion":"string?"},
            output_schema={"pedido_id":"string","total":"number","estado":"string","eta_min":"int"},
            enums={"entrega":["retiro","delivery"],"unidad":["unidad","docena"],"estado":["creado","en_preparacion","listo","entregado"]},
            query_examples=[
                "Quiero 2 cafés y 4 empanadas para retirar a las 6",
                "Envíame una docena de pan a mi casa",
                "Hazme un pedido de 3 panes integrales",
                "Pido 1 torta para mañana a las 5",
                "Quiero delivery de 2 donuts"
            ],
        ),
        dict(
            name="actualizar_pedido",
            business_desc="Actualizar un pedido: agregar/quitar productos o cambiar cantidades.",
            technical_desc="Order update: patch de items (add/remove/update) con validación de estado y recálculo de total.",
            input_schema={"pedido_id":"string","cambios":{"add":[{"producto":"string","cantidad":"number"}],"remove":[{"producto":"string"}],"update":[{"producto":"string","cantidad":"number"}]},"hora":"string?","entrega":"string?"},
            output_schema={"pedido_id":"string","total_actualizado":"number","estado":"string"},
            enums={"entrega":["retiro","delivery"]},
            query_examples=[
                "Del pedido 200 quita el café",
                "Agrega 2 donuts al pedido 200",
                "Cambia el pedido 15 a delivery",
                "Aumenta a 6 empanadas en mi pedido",
                "Quita las empanadas del pedido 88"
            ],
        ),
        dict(
            name="cancelar_pedido",
            business_desc="Cancelar un pedido por ID.",
            technical_desc="Order cancellation: cambia estado a cancelado, registra motivo y emite confirmación.",
            input_schema={"pedido_id":"string","motivo":"string?"},
            output_schema={"pedido_id":"string","estado":"string","mensaje":"string"},
            enums={"estado":["cancelado"],"motivo":["cliente","sin_stock","error","tiempo"]},
            query_examples=[
                "Anula mi pedido 200 por favor",
                "Ya no lo quiero, cancélalo",
                "Cancela el pedido 55",
                "Me equivoqué, anula mi pedido",
                "Por favor, elimina mi orden"
            ],
        ),
        dict(
            name="consultar_estado_pedido",
            business_desc="Consultar el estado de un pedido (en preparación, listo, entregado).",
            technical_desc="Order tracking: consulta estado + ETA y devuelve detalle de progreso.",
            input_schema={"pedido_id":"string"},
            output_schema={"pedido_id":"string","estado":"string","eta_min":"int","detalle":"string"},
            enums={"estado":["creado","en_preparacion","listo","entregado","cancelado"]},
            query_examples=[
                "Mi pedido 55 ya está listo?",
                "En qué estado está el pedido 55?",
                "Ya sale mi pedido?",
                "Cuánto falta para el pedido 12?",
                "Mi orden está en preparación?"
            ],
        ),
        dict(
            name="calcular_costo_envio",
            business_desc="Calcular costo y tiempo de delivery según zona o dirección.",
            technical_desc="Delivery pricing: estima ETA y costo por zona/horario y verifica cobertura.",
            input_schema={"direccion":"string","zona":"string?","hora":"string?"},
            output_schema={"costo_envio":"number","eta_min":"int","cobertura":"boolean"},
            enums={"zona":["cerca","media","lejos"]},
            query_examples=[
                "Cuánto cuesta el envío a Totoracocha?",
                "Haces delivery a mi dirección?",
                "Tiempo de entrega a mi barrio?",
                "Cuánto sale el delivery?",
                "Envían al centro?"
            ],
        ),
        dict(
            name="registrar_cliente",
            business_desc="Registrar datos de cliente (nombre, teléfono, correo opcional).",
            technical_desc="Customer upsert: crea o actualiza cliente para notificaciones y futuros pedidos.",
            input_schema={"nombre":"string","telefono":"string","correo":"string?"},
            output_schema={"cliente_id":"string","mensaje":"string"},
            enums={},
            query_examples=[
                "Regístrame como cliente, soy Ana 09xxxx",
                "Guarda mis datos, mi número es 09...",
                "Mi nombre es Luis, teléfono 09...",
                "Registra mi correo también",
                "Crea mi perfil de cliente"
            ],
        ),
        dict(
            name="consultar_horarios_ubicaciones",
            business_desc="Consultar horarios de atención y ubicaciones/sucursales.",
            technical_desc="Store info lookup: horarios por día/sucursal y direcciones.",
            input_schema={"dia":"string?","sucursal":"string?"},
            output_schema={"sucursales":[{"nombre":"string","direccion":"string","horario":"string","abierto":"boolean"}]},
            enums={"dia":["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]},
            query_examples=[
                "A qué hora abren?",
                "Dónde quedan sus sucursales?",
                "Están abiertos hoy domingo?",
                "Dirección de la sucursal del centro",
                "Horario del sábado"
            ],
        ),
    ]

def make_profile(f):
    # Perfil para embeddings: poco ruido, mucha intención + ejemplos.
    examples = " | ".join(f["query_examples"][:6])
    return (
        f"FUNCION: {f['name']}\n"
        f"INTENCION_NEGOCIO: {f['business_desc']}\n"
        f"DESCRIPCION_TECNICA: {f['technical_desc']}\n"
        f"EJEMPLOS: {examples}\n"
        f"KEYWORDS: pedido, precio, promo, horario, sucursal, delivery, cancelar, estado, registrar, recomendacion"
    )

def main():
    ensure_dirs()
    Base.metadata.create_all(bind=engine)

    embedder = build_embedder()

    with SessionLocal() as db:
        # limpiar y volver a sembrar
        db.query(FunctionDef).delete()
        db.commit()

        funcs = make_functions()
        for f in funcs:
            profile = make_profile(f)
            emb = embedder.embed_query(profile)

            row = FunctionDef(
                name=f["name"],
                business_desc=f["business_desc"],
                technical_desc=f["technical_desc"],
                input_schema=json.dumps(f["input_schema"], ensure_ascii=False),
                output_schema=json.dumps(f["output_schema"], ensure_ascii=False),
                enums=json.dumps(f["enums"], ensure_ascii=False),
                query_examples=json.dumps(f["query_examples"], ensure_ascii=False),
                profile_text=profile,
                embedding_json=json.dumps(emb),
            )
            db.add(row)

        db.commit()
        logger.info(f"✅ BD sembrada con {len(funcs)} funciones (incluye embeddings).")

        # construir y guardar índice
        build_vector_store_from_db(db)
        logger.info("✅ Índice FAISS guardado en ./data/faiss_index")

if __name__ == "__main__":
    main()
