# Datos de inventario y precios concretos de la panadería
# Esto simula la base de datos del negocio

PRODUCTOS = {
    "pan_frances": {"nombre": "Pan Francés", "precio": 0.15, "stock": 150, "categoria": "pan"},
    "pan_integral": {"nombre": "Pan Integral", "precio": 0.25, "stock": 80, "categoria": "pan"},
    "croissant": {"nombre": "Croissant", "precio": 0.75, "stock": 45, "categoria": "pan"},
    "empanada_pollo": {"nombre": "Empanada de Pollo", "precio": 1.25, "stock": 30, "categoria": "salado"},
    "empanada_carne": {"nombre": "Empanada de Carne", "precio": 1.25, "stock": 25, "categoria": "salado"},
    "torta_chocolate": {"nombre": "Torta de Chocolate", "precio": 15.00, "stock": 3, "categoria": "pasteleria"},
    "torta_vainilla": {"nombre": "Torta de Vainilla", "precio": 14.00, "stock": 2, "categoria": "pasteleria"},
    "donut": {"nombre": "Donut Glaseado", "precio": 0.80, "stock": 24, "categoria": "pasteleria"},
    "cafe": {"nombre": "Café Americano", "precio": 1.50, "stock": 100, "categoria": "bebidas"},
    "cafe_leche": {"nombre": "Café con Leche", "precio": 2.00, "stock": 100, "categoria": "bebidas"},
    "jugo_naranja": {"nombre": "Jugo de Naranja", "precio": 2.50, "stock": 20, "categoria": "bebidas"},
    "pan_sin_gluten": {"nombre": "Pan Sin Gluten", "precio": 0.50, "stock": 15, "categoria": "pan"},
    "galletas": {"nombre": "Galletas de Avena", "precio": 0.30, "stock": 60, "categoria": "pasteleria"},
    "brownie": {"nombre": "Brownie", "precio": 1.00, "stock": 18, "categoria": "pasteleria"},
}

PROMOCIONES = {
    "2x1_cafe": {"productos": ["cafe", "cafe_leche"], "descuento": 0.50, "descripcion": "2x1 en cafés (paga 1, lleva 2)"},
    "docena_pan": {"productos": ["pan_frances", "pan_integral"], "descuento": 0.20, "descripcion": "20% descuento en docena de pan"},
    "combo_desayuno": {"productos": ["cafe_leche", "croissant"], "precio_combo": 2.50, "descripcion": "Café + Croissant por $2.50"},
}

HORARIOS = {
    "lunes": {"apertura": "07:00", "cierre": "20:00", "abierto": True},
    "martes": {"apertura": "07:00", "cierre": "20:00", "abierto": True},
    "miercoles": {"apertura": "07:00", "cierre": "20:00", "abierto": True},
    "jueves": {"apertura": "07:00", "cierre": "20:00", "abierto": True},
    "viernes": {"apertura": "07:00", "cierre": "21:00", "abierto": True},
    "sabado": {"apertura": "08:00", "cierre": "18:00", "abierto": True},
    "domingo": {"apertura": "09:00", "cierre": "14:00", "abierto": True},
}

SUCURSALES = [
    {"nombre": "Sucursal Centro", "direccion": "Av. Principal 123", "telefono": "07-1234567"},
    {"nombre": "Sucursal Norte", "direccion": "Calle Norte 456", "telefono": "07-2345678"},
]

ZONAS_DELIVERY = {
    "centro": {"costo": 1.50, "tiempo_min": 15},
    "norte": {"costo": 2.00, "tiempo_min": 20},
    "sur": {"costo": 2.50, "tiempo_min": 25},
    "totoracocha": {"costo": 2.00, "tiempo_min": 20},
    "otros": {"costo": 3.50, "tiempo_min": 35},
}


def buscar_producto_por_nombre(query: str) -> list:
    """Busca productos que coincidan con la query."""
    query_lower = query.lower()
    resultados = []
    for key, prod in PRODUCTOS.items():
        if query_lower in prod["nombre"].lower() or query_lower in key:
            resultados.append({**prod, "id": key})
    return resultados


def obtener_precio(producto_id: str, cantidad: int = 1) -> dict:
    """Obtiene precio de un producto con promociones aplicadas."""
    if producto_id not in PRODUCTOS:
        return {"error": f"Producto '{producto_id}' no encontrado"}
    
    prod = PRODUCTOS[producto_id]
    precio_unit = prod["precio"]
    precio_total = precio_unit * cantidad
    promo_aplicada = None
    
    # Verificar promociones
    if cantidad >= 12 and producto_id in ["pan_frances", "pan_integral"]:
        precio_total = precio_total * 0.80  # 20% descuento
        promo_aplicada = "docena_pan"
    
    return {
        "producto": prod["nombre"],
        "precio_unitario": precio_unit,
        "cantidad": cantidad,
        "precio_total": round(precio_total, 2),
        "promocion": promo_aplicada,
        "stock_disponible": prod["stock"]
    }


def verificar_stock(producto_id: str, cantidad: int = 1) -> dict:
    """Verifica si hay stock suficiente."""
    if producto_id not in PRODUCTOS:
        return {"disponible": False, "mensaje": "Producto no encontrado"}
    
    prod = PRODUCTOS[producto_id]
    disponible = prod["stock"] >= cantidad
    return {
        "producto": prod["nombre"],
        "stock_actual": prod["stock"],
        "cantidad_solicitada": cantidad,
        "disponible": disponible,
        "mensaje": f"{'Sí' if disponible else 'No'} hay stock suficiente"
    }


def calcular_pedido(items: list) -> dict:
    """Calcula el total de un pedido con varios items."""
    total = 0
    detalle = []
    
    for item in items:
        prod_id = item.get("producto_id", "")
        cantidad = item.get("cantidad", 1)
        
        if prod_id in PRODUCTOS:
            prod = PRODUCTOS[prod_id]
            subtotal = prod["precio"] * cantidad
            total += subtotal
            detalle.append({
                "producto": prod["nombre"],
                "cantidad": cantidad,
                "precio_unit": prod["precio"],
                "subtotal": round(subtotal, 2)
            })
    
    return {
        "items": detalle,
        "subtotal": round(total, 2),
        "iva": round(total * 0.12, 2),
        "total": round(total * 1.12, 2)
    }


def obtener_horario_hoy() -> dict:
    """Obtiene el horario de hoy."""
    from datetime import datetime
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    hoy = dias[datetime.now().weekday()]
    return {"dia": hoy, **HORARIOS[hoy]}
