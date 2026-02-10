# Grafo de funciones con Neo4j
# Muestra cómo se relacionan las funciones entre sí

from typing import Optional
from .logging_config import setup_logging

logger = setup_logging()

# Definición de las relaciones entre funciones
# Esto representa cómo el agente puede navegar entre funciones
FUNCTION_GRAPH = {
    "nodes": [
        {"id": "saludar_cortesia", "label": "Saludar/Cortesía", "tipo": "entrada"},
        {"id": "buscar_producto", "label": "Buscar Producto", "tipo": "consulta"},
        {"id": "consultar_precio_promos", "label": "Consultar Precio", "tipo": "consulta"},
        {"id": "recomendar_productos", "label": "Recomendar", "tipo": "consulta"},
        {"id": "crear_pedido", "label": "Crear Pedido", "tipo": "transaccion"},
        {"id": "actualizar_pedido", "label": "Actualizar Pedido", "tipo": "transaccion"},
        {"id": "cancelar_pedido", "label": "Cancelar Pedido", "tipo": "transaccion"},
        {"id": "consultar_estado_pedido", "label": "Estado Pedido", "tipo": "consulta"},
        {"id": "calcular_costo_envio", "label": "Costo Envío", "tipo": "consulta"},
        {"id": "registrar_cliente", "label": "Registrar Cliente", "tipo": "transaccion"},
        {"id": "consultar_horarios_ubicaciones", "label": "Horarios/Ubicación", "tipo": "consulta"},
        {"id": "responder_fuera_contexto", "label": "Fuera de Contexto", "tipo": "fallback"},
    ],
    "edges": [
        # Flujo típico de compra
        {"from": "saludar_cortesia", "to": "buscar_producto", "rel": "PUEDE_LLEVAR_A"},
        {"from": "saludar_cortesia", "to": "recomendar_productos", "rel": "PUEDE_LLEVAR_A"},
        {"from": "saludar_cortesia", "to": "consultar_horarios_ubicaciones", "rel": "PUEDE_LLEVAR_A"},
        
        # Búsqueda → Precio → Pedido
        {"from": "buscar_producto", "to": "consultar_precio_promos", "rel": "SIGUIENTE_PASO"},
        {"from": "consultar_precio_promos", "to": "crear_pedido", "rel": "SIGUIENTE_PASO"},
        {"from": "recomendar_productos", "to": "consultar_precio_promos", "rel": "SIGUIENTE_PASO"},
        
        # Flujo de pedido
        {"from": "crear_pedido", "to": "calcular_costo_envio", "rel": "REQUIERE"},
        {"from": "crear_pedido", "to": "registrar_cliente", "rel": "REQUIERE"},
        {"from": "crear_pedido", "to": "actualizar_pedido", "rel": "PUEDE_LLEVAR_A"},
        {"from": "crear_pedido", "to": "cancelar_pedido", "rel": "PUEDE_LLEVAR_A"},
        {"from": "crear_pedido", "to": "consultar_estado_pedido", "rel": "PUEDE_LLEVAR_A"},
        
        # Modificaciones de pedido
        {"from": "actualizar_pedido", "to": "consultar_estado_pedido", "rel": "SIGUIENTE_PASO"},
        {"from": "cancelar_pedido", "to": "saludar_cortesia", "rel": "REINICIA_FLUJO"},
        
        # Fallback desde cualquier lugar
        {"from": "buscar_producto", "to": "responder_fuera_contexto", "rel": "FALLBACK"},
        {"from": "consultar_precio_promos", "to": "responder_fuera_contexto", "rel": "FALLBACK"},
        {"from": "crear_pedido", "to": "responder_fuera_contexto", "rel": "FALLBACK"},
    ]
}


class FunctionGraphManager:
    """Gestiona el grafo de funciones usando Neo4j o en memoria."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.driver = None
        self.use_neo4j = False
        
        if uri and user and password:
            try:
                from neo4j import GraphDatabase
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                self.use_neo4j = True
                logger.info("[NEO4J] Conectado a Neo4j")
            except Exception as e:
                logger.warning(f"[NEO4J] No se pudo conectar: {e}. Usando grafo en memoria.")
        else:
            logger.info("[GRAPH] Usando grafo de funciones en memoria")
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def init_graph(self):
        """Inicializa el grafo con las funciones y relaciones."""
        if self.use_neo4j:
            self._init_neo4j_graph()
        logger.info(f"[GRAPH] Grafo inicializado con {len(FUNCTION_GRAPH['nodes'])} funciones y {len(FUNCTION_GRAPH['edges'])} relaciones")
    
    def _init_neo4j_graph(self):
        """Crea el grafo en Neo4j."""
        with self.driver.session() as session:
            # Limpiar grafo existente
            session.run("MATCH (n:Funcion) DETACH DELETE n")
            
            # Crear nodos
            for node in FUNCTION_GRAPH["nodes"]:
                session.run(
                    "CREATE (f:Funcion {id: $id, label: $label, tipo: $tipo})",
                    id=node["id"], label=node["label"], tipo=node["tipo"]
                )
            
            # Crear relaciones
            for edge in FUNCTION_GRAPH["edges"]:
                session.run(
                    f"MATCH (a:Funcion {{id: $from_id}}), (b:Funcion {{id: $to_id}}) "
                    f"CREATE (a)-[:{edge['rel']}]->(b)",
                    from_id=edge["from"], to_id=edge["to"]
                )
    
    def get_related_functions(self, function_id: str) -> list:
        """Obtiene funciones relacionadas a una función dada."""
        related = []
        for edge in FUNCTION_GRAPH["edges"]:
            if edge["from"] == function_id:
                related.append({"function": edge["to"], "relation": edge["rel"]})
            elif edge["to"] == function_id:
                related.append({"function": edge["from"], "relation": f"INVERSO_{edge['rel']}"})
        return related
    
    def get_next_steps(self, function_id: str) -> list:
        """Obtiene los posibles siguientes pasos desde una función."""
        next_steps = []
        for edge in FUNCTION_GRAPH["edges"]:
            if edge["from"] == function_id and edge["rel"] in ["SIGUIENTE_PASO", "PUEDE_LLEVAR_A", "REQUIERE"]:
                next_steps.append(edge["to"])
        return next_steps
    
    def get_function_path(self, from_func: str, to_func: str) -> list:
        """Encuentra el camino entre dos funciones (BFS simple)."""
        if from_func == to_func:
            return [from_func]
        
        # BFS
        visited = set()
        queue = [[from_func]]
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            
            if node == to_func:
                return path
            
            if node not in visited:
                visited.add(node)
                for edge in FUNCTION_GRAPH["edges"]:
                    if edge["from"] == node:
                        new_path = list(path)
                        new_path.append(edge["to"])
                        queue.append(new_path)
        
        return []  # No hay camino
    
    def get_mermaid_diagram(self) -> str:
        """Genera diagrama Mermaid del grafo de funciones."""
        lines = ["graph LR"]
        
        # Estilos por tipo
        styles = {
            "entrada": ":::entrada",
            "consulta": ":::consulta", 
            "transaccion": ":::transaccion",
            "fallback": ":::fallback"
        }
        
        # Nodos
        for node in FUNCTION_GRAPH["nodes"]:
            style = styles.get(node["tipo"], "")
            lines.append(f"    {node['id']}[{node['label']}]{style}")
        
        # Relaciones
        for edge in FUNCTION_GRAPH["edges"]:
            arrow = "-->" if edge["rel"] == "SIGUIENTE_PASO" else "-..->"
            lines.append(f"    {edge['from']} {arrow}|{edge['rel']}| {edge['to']}")
        
        # Definir estilos
        lines.append("    classDef entrada fill:#90EE90,stroke:#228B22")
        lines.append("    classDef consulta fill:#87CEEB,stroke:#4169E1")
        lines.append("    classDef transaccion fill:#FFD700,stroke:#FF8C00")
        lines.append("    classDef fallback fill:#FFB6C1,stroke:#DC143C")
        
        return "\n".join(lines)
    
    def get_ascii_diagram(self) -> str:
        """Genera diagrama ASCII simple del grafo."""
        lines = []
        lines.append("=" * 60)
        lines.append("GRAFO DE FUNCIONES - PANADERÍA IA")
        lines.append("=" * 60)
        lines.append("")
        
        # Agrupar por tipo
        tipos = {"entrada": [], "consulta": [], "transaccion": [], "fallback": []}
        for node in FUNCTION_GRAPH["nodes"]:
            tipos[node["tipo"]].append(node)
        
        for tipo, nodes in tipos.items():
            if nodes:
                lines.append(f"[{tipo.upper()}]")
                for node in nodes:
                    related = self.get_next_steps(node["id"])
                    if related:
                        lines.append(f"  ├── {node['label']}")
                        for i, rel in enumerate(related):
                            prefix = "  │   └──" if i == len(related) - 1 else "  │   ├──"
                            lines.append(f"{prefix} → {rel}")
                    else:
                        lines.append(f"  └── {node['label']}")
                lines.append("")
        
        return "\n".join(lines)


# Instancia global
_graph_manager: Optional[FunctionGraphManager] = None

def get_function_graph() -> FunctionGraphManager:
    """Obtiene o crea el gestor del grafo de funciones."""
    global _graph_manager
    if _graph_manager is None:
        # Intentar conectar a Neo4j si está configurado
        from .settings import settings
        _graph_manager = FunctionGraphManager(
            uri=getattr(settings, 'NEO4J_URI', None),
            user=getattr(settings, 'NEO4J_USER', None),
            password=getattr(settings, 'NEO4J_PASSWORD', None)
        )
        _graph_manager.init_graph()
    return _graph_manager
