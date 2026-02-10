from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from .db import get_db, Base, engine
from .models import FunctionDef
from .router import load_vector_store, build_vector_store_from_db
from .graph import build_graph, AgentState
from .function_graph import get_function_graph, FUNCTION_GRAPH
from .logging_config import setup_logging

logger = setup_logging()

app = FastAPI(title="Agente IA Estocásticos")

# CORS para permitir la app móvil/web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialización BD
Base.metadata.create_all(bind=engine)

# Cargar o construir índice FAISS
_vs = load_vector_store()
_graph = None

class ChatIn(BaseModel):
    session_id: str = "default-session"
    query: str

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/functions")
def list_functions(db: Session = Depends(get_db)):
    rows = db.query(FunctionDef).all()
    return [{"name": r.name, "business_desc": r.business_desc, "technical_desc": r.technical_desc} for r in rows]

@app.get("/graph/mermaid")
def graph_mermaid():
    global _graph
    if _graph is None:
        return {"error": "Graph not initialized yet. Run /chat once or seed DB first."}
    return {"mermaid": _graph.get_graph().draw_mermaid()}

@app.get("/graph/functions/mermaid")
def function_graph_mermaid():
    """Retorna el diagrama Mermaid del grafo de relaciones entre funciones."""
    fg = get_function_graph()
    return {"mermaid": fg.get_mermaid_diagram()}

@app.get("/graph/functions/data")
def function_graph_data():
    """Retorna los datos del grafo de funciones (nodos y aristas)."""
    return FUNCTION_GRAPH

@app.get("/graph/functions", response_class=HTMLResponse)
def function_graph_view():
    """Visualización HTML del grafo de relaciones entre funciones (Neo4j style)."""
    fg = get_function_graph()
    mermaid_code = fg.get_mermaid_diagram()
    
    html = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔗 Grafo de Funciones - Panadería IA</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 30px; }
        header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        header p { opacity: 0.8; }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        .card h2 { margin-bottom: 16px; font-size: 1.3rem; }
        .mermaid { background: white; border-radius: 12px; padding: 20px; }
        .legend { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 20px; }
        .legend-item { display: flex; align-items: center; gap: 8px; }
        .legend-dot { width: 16px; height: 16px; border-radius: 4px; }
        .dot-entrada { background: #90EE90; }
        .dot-consulta { background: #87CEEB; }
        .dot-transaccion { background: #FFD700; }
        .dot-fallback { background: #FFB6C1; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 20px; }
        .info-box { background: rgba(255,255,255,0.1); padding: 16px; border-radius: 10px; text-align: center; }
        .info-box .number { font-size: 2rem; font-weight: bold; }
        .info-box .label { font-size: 0.9rem; opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔗 Grafo de Funciones</h1>
            <p>Relaciones y flujos entre las funciones del agente (estilo Neo4j)</p>
        </header>
        
        <div class="card">
            <h2>📊 Diagrama de Relaciones</h2>
            <div class="mermaid">
''' + mermaid_code + '''
            </div>
            
            <div class="legend">
                <div class="legend-item"><div class="legend-dot dot-entrada"></div> Entrada/Cortesía</div>
                <div class="legend-item"><div class="legend-dot dot-consulta"></div> Consulta</div>
                <div class="legend-item"><div class="legend-dot dot-transaccion"></div> Transacción</div>
                <div class="legend-item"><div class="legend-dot dot-fallback"></div> Fallback</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 Estadísticas del Grafo</h2>
            <div class="info-grid">
                <div class="info-box">
                    <div class="number">''' + str(len(FUNCTION_GRAPH['nodes'])) + '''</div>
                    <div class="label">Funciones (Nodos)</div>
                </div>
                <div class="info-box">
                    <div class="number">''' + str(len(FUNCTION_GRAPH['edges'])) + '''</div>
                    <div class="label">Relaciones (Aristas)</div>
                </div>
                <div class="info-box">
                    <div class="number">4</div>
                    <div class="label">Tipos de Nodo</div>
                </div>
                <div class="info-box">
                    <div class="number">4</div>
                    <div class="label">Tipos de Relación</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔄 Tipos de Relaciones</h2>
            <ul style="list-style: none; padding: 0;">
                <li style="padding: 8px 0;">➡️ <strong>SIGUIENTE_PASO</strong>: Flujo natural de la conversación</li>
                <li style="padding: 8px 0;">🔀 <strong>PUEDE_LLEVAR_A</strong>: Transición opcional</li>
                <li style="padding: 8px 0;">⚡ <strong>REQUIERE</strong>: Dependencia necesaria</li>
                <li style="padding: 8px 0;">🔙 <strong>FALLBACK</strong>: Manejo de errores/fuera de contexto</li>
            </ul>
        </div>
    </div>
    
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' }
        });
    </script>
</body>
</html>
'''
    return HTMLResponse(content=html)

@app.get("/graph", response_class=HTMLResponse)
def graph_view(db: Session = Depends(get_db)):
    """Visualización interactiva del grafo LangGraph."""
    global _vs, _graph
    
    # Inicializar grafo si no existe
    if _vs is None:
        _vs = build_vector_store_from_db(db)
    if _graph is None:
        _graph = build_graph(_vs)
    
    mermaid_code = _graph.get_graph().draw_mermaid()
    
    # Obtener las funciones disponibles
    functions = db.query(FunctionDef).all()
    functions_html = "".join([
        f'<div class="function-card"><strong>{f.name}</strong><p>{f.business_desc}</p></div>'
        for f in functions
    ])
    
    html = f'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥐 Agente IA Panadería - Grafo</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }}
        @media (max-width: 1000px) {{
            .main-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .card {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .card-header {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            padding: 16px 24px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .card-header h2 {{
            font-size: 1.2rem;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .card-body {{
            padding: 24px;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 400px;
        }}
        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}
        .function-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 12px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .function-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }}
        .function-card strong {{
            color: #333;
            font-size: 0.95rem;
            display: block;
            margin-bottom: 6px;
        }}
        .function-card p {{
            color: #666;
            font-size: 0.85rem;
            line-height: 1.4;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-box .number {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .stat-box .label {{
            font-size: 0.8rem;
            opacity: 0.9;
        }}
        .legend {{
            margin-top: 20px;
            padding: 16px;
            background: #f0f4f8;
            border-radius: 10px;
        }}
        .legend h3 {{
            font-size: 0.9rem;
            color: #333;
            margin-bottom: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            font-size: 0.85rem;
            color: #555;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .dot-start {{ background: #34C759; }}
        .dot-process {{ background: #007AFF; }}
        .dot-end {{ background: #FF3B30; }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 10px;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🥐 Agente IA Panadería</h1>
            <p>Visualización del Grafo de Estados (LangGraph)</p>
        </header>
        
        <div class="main-grid">
            <div class="card">
                <div class="card-header">
                    <h2>📊 Flujo del Agente</h2>
                </div>
                <div class="card-body">
                    <div class="mermaid">
{mermaid_code}
                    </div>
                </div>
            </div>
            
            <div>
                <div class="card" style="margin-bottom: 20px;">
                    <div class="card-header">
                        <h2>📈 Estadísticas</h2>
                    </div>
                    <div class="card-body">
                        <div class="stats">
                            <div class="stat-box">
                                <div class="number">4</div>
                                <div class="label">Nodos</div>
                            </div>
                            <div class="stat-box">
                                <div class="number">{len(functions)}</div>
                                <div class="label">Funciones</div>
                            </div>
                        </div>
                        
                        <div class="legend">
                            <h3>Leyenda del Flujo</h3>
                            <div class="legend-item">
                                <div class="legend-dot dot-start"></div>
                                <span><strong>START</strong> → Entrada del usuario</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-dot dot-process"></div>
                                <span><strong>route</strong> → Selección semántica (FAISS)</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-dot dot-process"></div>
                                <span><strong>plan</strong> → Planificación de pasos</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-dot dot-process"></div>
                                <span><strong>exec</strong> → Ejecución de herramientas</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-dot dot-process"></div>
                                <span><strong>respond</strong> → Generación con LLM</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-dot dot-end"></div>
                                <span><strong>END</strong> → Respuesta al usuario</span>
                            </div>
                        </div>
                        
                        <span class="badge badge-success">✓ Groq LLM Activo</span>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2>🛠️ Funciones Disponibles</h2>
                    </div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        {functions_html}
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="footer">
            <p>Universidad - Análisis Multivariado y Modelos Estocásticos</p>
        </footer>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                primaryColor: '#667eea',
                primaryTextColor: '#fff',
                primaryBorderColor: '#764ba2',
                lineColor: '#764ba2',
                secondaryColor: '#f0f4f8',
                tertiaryColor: '#fff'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>
'''
    return HTMLResponse(content=html)

@app.post("/chat")
def chat(payload: ChatIn, db: Session = Depends(get_db)):
    global _vs, _graph
    if _vs is None:
        logger.info("[INIT] building FAISS index from DB")
        _vs = build_vector_store_from_db(db)
    if _graph is None:
        _graph = build_graph(_vs)

    state: AgentState = {"session_id": payload.session_id, "user_query": payload.query, "exec_log": []}
    out = _graph.invoke(state)

    return {
        "session_id": payload.session_id,
        "query": payload.query,
        "selected_function": {"name": out["route"].function, "score": out["route"].score},
        "plan": out["plan"],
        "exec_log": out["exec_log"],
        "response": out["final_response"],
    }
