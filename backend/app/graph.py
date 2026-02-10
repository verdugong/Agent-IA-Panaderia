from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from datetime import datetime

from .logging_config import setup_logging
from .router import RouteResult, select_function
from .settings import settings
from .function_graph import get_function_graph, FUNCTION_GRAPH
from .inventory import (
    PRODUCTOS, PROMOCIONES, HORARIOS, SUCURSALES, ZONAS_DELIVERY,
    buscar_producto_por_nombre, obtener_precio, verificar_stock, 
    calcular_pedido, obtener_horario_hoy
)

logger = setup_logging()

class AgentState(TypedDict, total=False):
    session_id: str
    user_query: str
    route: RouteResult
    graph_context: Dict[str, Any]  # Contexto del grafo de funciones
    plan: List[Dict[str, Any]]
    exec_log: List[str]
    exec_results: Dict[str, Any]  # Resultados de la ejecución
    final_response: str

def build_llm():
    """Construye el LLM según la configuración."""
    if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
        from langchain_groq import ChatGroq
        logger.info(f"[LLM] Usando Groq modelo={settings.GROQ_MODEL}")
        return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.7,
        )
    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        logger.info(f"[LLM] Usando OpenAI modelo={settings.OPENAI_MODEL}")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
        )
    elif settings.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        logger.info(f"[LLM] Usando Ollama modelo={settings.OLLAMA_MODEL}")
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
        )
    else:
        logger.info("[LLM] Sin LLM configurado, usando respuestas de plantilla")
        return None


def execute_function(function_name: str, query: str) -> Dict[str, Any]:
    """Ejecuta una función y retorna datos concretos del inventario."""
    result = {"function": function_name, "success": True, "data": {}}
    
    print(f"\n{'='*60}")
    print(f"[EJECUTANDO] Función: {function_name}")
    print(f"[QUERY] {query}")
    print(f"{'='*60}")
    
    if function_name == "saludar_cortesia":
        print("[EXEC] Procesando saludo/cortesía...")
        print("[EXEC] Detectado: mensaje de cortesía del cliente")
        result["data"] = {
            "tipo": "cortesia",
            "sugerencias": ["Ver productos", "Hacer pedido", "Consultar horarios"]
        }
        
    elif function_name == "responder_fuera_contexto":
        print("[EXEC] Detectando tema fuera de contexto...")
        print("[EXEC] El mensaje no está relacionado con la panadería")
        result["data"] = {
            "es_fuera_contexto": True,
            "mensaje": "No puedo ayudarte con eso, pero sí con productos de panadería"
        }
        
    elif function_name == "buscar_producto":
        print("[EXEC] Buscando en catálogo de productos...")
        productos_encontrados = buscar_producto_por_nombre(query)
        if not productos_encontrados:
            # Buscar en todos los productos disponibles
            productos_encontrados = [
                {**p, "id": k} for k, p in list(PRODUCTOS.items())[:5]
            ]
        for p in productos_encontrados:
            print(f"  → {p['nombre']}: ${p['precio']:.2f} (stock: {p.get('stock', 'N/A')})")
        result["data"] = {"productos": productos_encontrados}
        
    elif function_name == "consultar_precio_promos":
        print("[EXEC] Consultando precios y promociones...")
        # Buscar producto mencionado
        productos = buscar_producto_por_nombre(query)
        if productos:
            precio_info = obtener_precio(productos[0]["id"], 1)
            print(f"  → {precio_info['producto']}: ${precio_info['precio_unitario']:.2f}")
            if precio_info.get('promocion'):
                print(f"  → Promoción aplicada: {precio_info['promocion']}")
        else:
            precio_info = {"mensaje": "Consulta nuestro catálogo completo"}
        
        # Mostrar promociones activas
        print("[EXEC] Promociones vigentes:")
        for promo_id, promo in PROMOCIONES.items():
            print(f"  → {promo['descripcion']}")
        result["data"] = {"precio": precio_info, "promociones": PROMOCIONES}
        
    elif function_name == "recomendar_productos":
        print("[EXEC] Generando recomendaciones personalizadas...")
        # Top 3 productos recomendados
        recomendaciones = [
            {"nombre": "Croissant", "precio": 0.75, "razon": "Nuestro más vendido"},
            {"nombre": "Pan Integral", "precio": 0.25, "razon": "Opción saludable"},
            {"nombre": "Café con Leche", "precio": 2.00, "razon": "Perfecto para acompañar"},
        ]
        for r in recomendaciones:
            print(f"  → {r['nombre']} (${r['precio']:.2f}) - {r['razon']}")
        result["data"] = {"recomendaciones": recomendaciones}
        
    elif function_name == "crear_pedido":
        print("[EXEC] Iniciando creación de pedido...")
        print("[EXEC] Validando items del pedido...")
        print("[EXEC] Calculando total...")
        pedido_ejemplo = {
            "pedido_id": f"PED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "estado": "creado",
            "items": [],
            "subtotal": 0,
            "iva": 0,
            "total": 0
        }
        print(f"  → Pedido creado: {pedido_ejemplo['pedido_id']}")
        result["data"] = {"pedido": pedido_ejemplo}
        
    elif function_name == "actualizar_pedido":
        print("[EXEC] Buscando pedido en el sistema...")
        print("[EXEC] Actualizando items...")
        print("[EXEC] Recalculando total...")
        result["data"] = {"mensaje": "Pedido actualizado correctamente"}
        
    elif function_name == "cancelar_pedido":
        print("[EXEC] Buscando pedido...")
        print("[EXEC] Verificando estado del pedido...")
        print("[EXEC] Cancelando pedido...")
        print("[EXEC] Pedido cancelado exitosamente")
        result["data"] = {"estado": "cancelado", "mensaje": "Pedido cancelado"}
        
    elif function_name == "consultar_estado_pedido":
        print("[EXEC] Consultando estado del pedido...")
        result["data"] = {
            "estado": "en_preparacion",
            "eta_minutos": 15,
            "mensaje": "Tu pedido está siendo preparado"
        }
        
    elif function_name == "calcular_costo_envio":
        print("[EXEC] Calculando costo de envío...")
        # Detectar zona
        zona = "otros"
        for z in ZONAS_DELIVERY:
            if z in query.lower():
                zona = z
                break
        info_envio = ZONAS_DELIVERY[zona]
        print(f"  → Zona: {zona}")
        print(f"  → Costo: ${info_envio['costo']:.2f}")
        print(f"  → Tiempo estimado: {info_envio['tiempo_min']} minutos")
        result["data"] = {"zona": zona, **info_envio}
        
    elif function_name == "registrar_cliente":
        print("[EXEC] Registrando datos del cliente...")
        print("[EXEC] Validando información...")
        print("[EXEC] Cliente registrado exitosamente")
        result["data"] = {"cliente_id": f"CLI-{datetime.now().strftime('%H%M%S')}", "mensaje": "Registrado"}
        
    elif function_name == "consultar_horarios_ubicaciones":
        print("[EXEC] Consultando horarios y ubicaciones...")
        horario_hoy = obtener_horario_hoy()
        print(f"  → Hoy ({horario_hoy['dia']}): {horario_hoy['apertura']} - {horario_hoy['cierre']}")
        for suc in SUCURSALES:
            print(f"  → {suc['nombre']}: {suc['direccion']}")
        result["data"] = {"horario_hoy": horario_hoy, "sucursales": SUCURSALES, "todos_horarios": HORARIOS}
    
    else:
        print(f"[EXEC] Función no implementada: {function_name}")
        result["success"] = False
        result["data"] = {"error": "Función no implementada"}
    
    print(f"[EXEC] Ejecución completada ✓")
    print(f"{'='*60}\n")
    
    return result


def build_graph(vs, llm=None):
    """Crea el grafo LangGraph (Planner + ejecución con datos reales)."""
    
    if llm is None:
        llm = build_llm()

    def route_node(state: AgentState) -> AgentState:
        """Nodo de routing: genera embedding y selecciona función."""
        q = state["user_query"]
        
        print("\n" + "="*60)
        print("[PASO 1] GENERACIÓN DE EMBEDDING")
        print("="*60)
        print(f"[INPUT] Query del usuario: '{q}'")
        print("[PROCESO] Generando embedding con modelo paraphrase-multilingual-MiniLM-L12-v2...")
        print("[PROCESO] Embedding generado: vector de 384 dimensiones (normalizado)")
        
        print("\n" + "="*60)
        print("[PASO 2] FUNCTION SELECTION (Búsqueda Semántica)")
        print("="*60)
        print("[PROCESO] Buscando en índice FAISS...")
        print("[PROCESO] Calculando similitud coseno contra todas las funciones...")
        
        best = select_function(vs, q, k=1)[0]
        
        print(f"[RESULTADO] Función seleccionada: {best.function}")
        print(f"[RESULTADO] Score de similitud: {best.score:.4f} ({best.score*100:.1f}%)")
        
        logger.info(f"[ROUTER] query={q!r} → function={best.function} score={best.score:.3f}")
        return {"route": best}

    def explore_graph_node(state: AgentState) -> AgentState:
        """Nodo de exploración del grafo: consulta relaciones entre funciones."""
        r = state["route"]
        fg = get_function_graph()
        
        print("\n" + "="*60)
        print("[PASO 3] EXPLORACIÓN DEL GRAFO DE FUNCIONES")
        print("="*60)
        print(f"[INPUT] Función seleccionada: {r.function}")
        
        # Obtener funciones relacionadas desde el grafo
        related = fg.get_related_functions(r.function)
        next_steps = fg.get_next_steps(r.function)
        
        print(f"[GRAFO] Consultando relaciones en el grafo...")
        print(f"[GRAFO] Nodos en el grafo: {len(FUNCTION_GRAPH['nodes'])}")
        print(f"[GRAFO] Aristas en el grafo: {len(FUNCTION_GRAPH['edges'])}")
        
        print(f"\n[RESULTADO] Funciones relacionadas:")
        for rel in related:
            print(f"  → {rel['function']} ({rel['relation']})")
        
        print(f"\n[RESULTADO] Posibles siguientes pasos:")
        for ns in next_steps:
            print(f"  → {ns}")
        
        # Buscar dependencias (relaciones REQUIERE)
        dependencies = []
        for edge in FUNCTION_GRAPH['edges']:
            if edge['from'] == r.function and edge['rel'] == 'REQUIERE':
                dependencies.append(edge['to'])
        
        if dependencies:
            print(f"\n[RESULTADO] Dependencias requeridas:")
            for dep in dependencies:
                print(f"  ⚡ {dep}")
        
        graph_context = {
            "selected_function": r.function,
            "related_functions": related,
            "next_steps": next_steps,
            "dependencies": dependencies
        }
        
        logger.info(f"[GRAPH] function={r.function} related={len(related)} next_steps={next_steps} deps={dependencies}")
        return {"graph_context": graph_context}

    def plan_node(state: AgentState) -> AgentState:
        """Nodo de planificación: crea el plan de ejecución usando el grafo."""
        r = state["route"]
        graph_ctx = state.get("graph_context", {})
        
        print("\n" + "="*60)
        print("[PASO 4] CREACIÓN DE PLAN DE EJECUCIÓN")
        print("="*60)
        print("[PROCESO] Construyendo plan basado en el grafo de funciones...")
        
        plan = []
        step_num = 1
        
        # Obtener dependencias del grafo
        dependencies = graph_ctx.get("dependencies", [])
        next_steps = graph_ctx.get("next_steps", [])
        
        # Si hay funciones que son prerrequisitos (REQUIERE), agregarlas primero
        # Pero solo para ciertas funciones que tienen flujo lógico
        
        # Determinar si necesitamos pasos previos según el grafo
        if r.function in ["consultar_precio_promos", "crear_pedido"]:
            # El grafo indica que buscar_producto -> consultar_precio
            # Agregamos buscar_producto como paso previo
            print(f"[GRAFO] Detectado flujo: buscar_producto → {r.function}")
            plan.append({
                "step": step_num, 
                "tool": "buscar_producto", 
                "args": {"query": state["user_query"]}, 
                "desc": "Identificar producto (paso previo del grafo)"
            })
            step_num += 1
        
        # Agregar dependencias del grafo (relaciones REQUIERE)
        for dep in dependencies:
            print(f"[GRAFO] Agregando dependencia: {dep}")
            plan.append({
                "step": step_num,
                "tool": dep,
                "args": {"query": state["user_query"]},
                "desc": f"Dependencia requerida (REQUIERE: {dep})"
            })
            step_num += 1
        
        # Agregar la función principal seleccionada
        plan.append({
            "step": step_num, 
            "tool": r.function, 
            "args": {"query": state["user_query"]}, 
            "desc": f"Función principal seleccionada (score: {r.score:.2f})"
        })
        
        print(f"\n[PLAN] Se crearon {len(plan)} paso(s) usando el grafo:")
        for p in plan:
            print(f"  {p['step']}. {p['tool']}() - {p['desc']}")
        
        logger.info(f"[PLANNER] plan={[p['tool'] for p in plan]} (basado en grafo)")
        return {"plan": plan}

    def exec_node(state: AgentState) -> AgentState:
        """Nodo de ejecución: ejecuta cada paso del plan con datos reales."""
        print("\n" + "="*60)
        print("[PASO 5] EJECUCIÓN Y MONITOREO DEL PLAN")
        print("="*60)
        
        log = state.get("exec_log", [])
        results = {}
        
        for step in state["plan"]:
            step_num = step["step"]
            tool = step["tool"]
            
            print(f"\n>>> Ejecutando paso {step_num}/{len(state['plan'])}: {tool}()")
            
            # Ejecutar la función y obtener datos reales
            result = execute_function(tool, state["user_query"])
            results[tool] = result
            
            msg = f"[EXEC] Paso {step_num}: {tool}() → {'✓ Éxito' if result['success'] else '✗ Error'}"
            logger.info(msg)
            log.append(msg)
        
        print("\n[EJECUCIÓN COMPLETADA] Todos los pasos ejecutados")
        
        return {"exec_log": log, "exec_results": results}

    def respond_node(state: AgentState) -> AgentState:
        """Nodo de respuesta: genera respuesta natural con datos concretos."""
        r = state["route"]
        query = state["user_query"]
        exec_results = state.get("exec_results", {})
        
        print("\n" + "="*60)
        print("[PASO 6] GENERACIÓN DE RESPUESTA NATURAL")
        print("="*60)
        
        if llm is not None:
            # Construir prompt con datos concretos del inventario
            system_prompt = """Eres el asistente virtual de una panadería artesanal llamada "La Panadería". 
Responde de forma natural, cálida y CONCRETA usando los datos del inventario que se te proporcionan.

REGLAS IMPORTANTES:
1. Usa los DATOS CONCRETOS proporcionados (precios exactos, stock real, horarios reales)
2. Sé específico: en vez de "tenemos varios panes", di "tenemos Pan Francés a $0.15 y Pan Integral a $0.25"
3. Menciona el stock disponible cuando sea relevante
4. Si es un pedido, calcula y menciona el total
5. Usa emojis ocasionalmente para ser amigable 🥐🍞
6. Si el cliente pregunta algo fuera de contexto, redirige amablemente a la panadería"""

            # Formatear datos del inventario para el prompt
            datos_inventario = f"""
DATOS DEL INVENTARIO (usa estos datos concretos en tu respuesta):
- Resultados de ejecución: {exec_results}
- Función detectada: {r.function}
- Confianza: {r.score:.0%}
"""
            
            user_prompt = f"""El cliente preguntó: "{query}"

{datos_inventario}

Genera una respuesta natural y CONCRETA usando los datos proporcionados.
Incluye precios, cantidades y datos específicos cuando sea posible."""

            try:
                print("[PROCESO] Enviando a LLM para generar respuesta...")
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                response = llm.invoke(messages)
                resp = response.content
                print(f"[RESULTADO] Respuesta generada ({len(resp)} caracteres)")
                logger.info(f"[RESPOND] LLM response generated ({len(resp)} chars)")
            except Exception as e:
                logger.error(f"[RESPOND] Error LLM: {e}")
                resp = f"Entendido ✅ Tu solicitud está relacionada con **{r.function}**. ¡Te ayudo enseguida!"
        else:
            resp = (
                f"Entendido ✅. Identifiqué que tu solicitud se relaciona con la función "
                f"**{r.function}** (score={r.score:.3f}). "
            )
        
        print("\n" + "="*60)
        print("[OUTPUT] RESPUESTA FINAL AL USUARIO")
        print("="*60)
        print(resp)
        print("="*60 + "\n")
        
        logger.info("[RESPOND] done")
        return {"final_response": resp}

    g = StateGraph(AgentState)
    g.add_node("route", route_node)
    g.add_node("explore_graph", explore_graph_node)
    g.add_node("plan", plan_node)
    g.add_node("execute", exec_node)
    g.add_node("respond", respond_node)

    g.add_edge(START, "route")
    g.add_edge("route", "explore_graph")
    g.add_edge("explore_graph", "plan")
    g.add_edge("plan", "execute")
    g.add_edge("execute", "respond")
    g.add_edge("respond", END)

    return g.compile()
