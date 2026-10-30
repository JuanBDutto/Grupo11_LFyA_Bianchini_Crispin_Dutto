import ast
import pytest
from normalizacion import normalize
from similitud_jaccard import evaluar_similitud_funciones

# --- HELPER ---
def obtener_dict_funcion(codigo_fuente: str, nombre_func: str) -> dict:
    """
    Parsea un string de código, extrae el nodo de la función indicada,
    lo normaliza en memoria y devuelve el diccionario esperado por tu sistema.
    """
    arbol = ast.parse(codigo_fuente)
    # Buscamos la función en el AST
    nodo_func = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == nombre_func)
    
    # Normalizamos el AST de la función (modifica el nodo in-place, igual que tu main)
    normalize(nodo_func)
    
    return {
        "nombre": nombre_func,
        "archivo": "dummy.py",
        "linea": nodo_func.lineno,
        "ast": nodo_func
    }


# --- CASOS POSITIVOS (CLONES) ---

def test_clon_variables_renombradas():
    """
    Caso Positivo 1: Misma lógica, pero los parámetros y variables internas
    tienen nombres completamente distintos.
    """
    codigo_base = """
def calcular_area(base, altura):
    area = (base * altura) / 2
    return area
"""
    codigo_clon = """
def area_triangulo(b, h):
    resultado = (b * h) / 2
    return resultado
"""
    f_base = obtener_dict_funcion(codigo_base, "calcular_area")
    f_clon = obtener_dict_funcion(codigo_clon, "area_triangulo")
    
    resultados = evaluar_similitud_funciones(f_base, [f_clon])
    similitud = resultados[0]["porcentaje_similitud"]
    
    # Gracias a tu normalizador (VAR1, VAR2, LIT), deberían ser idénticas
    assert similitud == 100.0
    assert resultados[0]["decision_similitud"] == "Exactamente iguales"


def test_clon_lineas_reordenadas():
    """
    Caso Positivo 2: Misma lógica, pero se han alterado el orden de las asignaciones
    independientes.
    """
    codigo_base = """
def procesar_coordenadas(x, y):
    val_x = x * 2
    val_y = y + 5
    return val_x + val_y
"""
    # Se invierte el orden de asignación de las variables internas
    codigo_clon = """
def coords(a, b):
    val_y = b + 5
    val_x = a * 2
    return val_x + val_y
"""
    f_base = obtener_dict_funcion(codigo_base, "procesar_coordenadas")
    f_clon = obtener_dict_funcion(codigo_clon, "coords")
    
    resultados = evaluar_similitud_funciones(f_base, [f_clon])
    similitud = resultados[0]["porcentaje_similitud"]
    
    # Al reordenar líneas, el AST cambia sutilmente y el n-grama captura la diferencia,
    # pero el porcentaje seguirá siendo alto (Similares o Candidatas a clones).
    assert 50.0 <= similitud < 100.0
    assert resultados[0]["decision_similitud"] in ["Similares", "Candidatas a clones"]


# --- CASOS NEGATIVOS (DISTINTAS) ---

def test_distintas_misma_estructura_operacion_diferente():
    """
    Caso Negativo 1: Estructura idéntica pero la operación matemática base es distinta.
    (Ej: Suma vs Multiplicación). No deberían ser clones exactos.
    """
    codigo_base = """
def operacion(a, b):
    return a + b
"""
    codigo_distinto = """
def operacion(a, b):
    return a * b
"""
    f_base = obtener_dict_funcion(codigo_base, "operacion")
    f_distinta = obtener_dict_funcion(codigo_distinto, "operacion")
    
    resultados = evaluar_similitud_funciones(f_base, [f_distinta])
    similitud = resultados[0]["porcentaje_similitud"]
    
    # El nodo del AST cambia (Add vs Mult), rompiendo n-gramas.
    assert similitud < 100.0
    assert resultados[0]["decision_similitud"] != "Exactamente iguales"


def test_distintas_totalmente():
    """
    Caso Negativo 2: Funciones que resuelven problemas completamente distintos,
    con bucles y condicionales vs operaciones planas.
    """
    codigo_base = """
def sumar_lista(lista):
    total = 0
    for num in lista:
        total += num
    return total
"""
    codigo_distinto = """
def verificar_login(usuario, clave):
    if usuario == 'admin' and clave == '1234':
        return True
    return False
"""
    f_base = obtener_dict_funcion(codigo_base, "sumar_lista")
    f_distinta = obtener_dict_funcion(codigo_distinto, "verificar_login")
    
    resultados = evaluar_similitud_funciones(f_base, [f_distinta])
    similitud = resultados[0]["porcentaje_similitud"]
    
    # No deben tener casi nada en común
    assert similitud < 50.0
    assert resultados[0]["decision_similitud"] == "No similares"