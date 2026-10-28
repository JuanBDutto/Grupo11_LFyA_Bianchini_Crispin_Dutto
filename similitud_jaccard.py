import ast
from typing import Any, Dict, List, Set, Tuple, Union


def ast_a_tokens(nodo_funcion: Union[Dict[str, Any], ast.AST]) -> List[str]:
    """
    Recibe el diccionario de la función (con clave 'ast') o directamente el nodo ast.AST
    normalizado, y emite [tipo_de_nodo, tokens_normalizados...] en recorrido pre-order.
    """
    raiz = nodo_funcion["ast"] if isinstance(nodo_funcion, dict) and "ast" in nodo_funcion else nodo_funcion
    tokens: List[str] = []

    def preorden(n: ast.AST) -> None:
        if n is None:
            return

        # 1. Emitir el tipo de nodo (ej. 'FunctionDef', 'BinOp', 'Name')
        tokens.append(type(n).__name__)

        # 2. Separar tokens normalizados (valores hoja) de los nodos hijos
        hijos: List[ast.AST] = []
        for _, valor in ast.iter_fields(n):
            if isinstance(valor, ast.AST):
                hijos.append(valor)
            elif isinstance(valor, list):
                for item in valor:
                    if isinstance(item, ast.AST):
                        hijos.append(item)
                    elif isinstance(item, (str, int, float, bool)) and item is not None:
                        tokens.append(str(item))
            elif isinstance(valor, (str, int, float, bool)) and valor is not None:
                tokens.append(str(valor))

        # 3. Recorrer recursivamente los hijos en orden
        for hijo in hijos:
            preorden(hijo)

    preorden(raiz)
    return tokens

def generar_ngramas(tokens: List[str], n: int = 3) -> Set[Tuple[str, ...]]:
    """
    Genera el conjunto de n-gramas a partir de una secuencia lineal de tokens.
    Si la secuencia tiene menos de `n` elementos pero no está vacía,
    emite una única tupla con los tokens disponibles.
    """
    if not tokens:
        return set()
    if len(tokens) < n:
        return {tuple(tokens)}
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def calcular_jaccard(
    ngramas_base: Set[Tuple[str, ...]], ngramas_comp: Set[Tuple[str, ...]]
) -> float:
    """
    Calcula el porcentaje de similitud de Jaccard (0.0 a 100.0) entre dos conjuntos de n-gramas.
    """
    if not ngramas_base and not ngramas_comp:
        return 100.0
    if not ngramas_base or not ngramas_comp:
        return 0.0

    interseccion = len(ngramas_base.intersection(ngramas_comp))
    union = len(ngramas_base.union(ngramas_comp))
    return (interseccion / union) * 100.0


def clasificar_similitud(porcentaje: float) -> str:
    """
    Determina la decisión de similitud según los umbrales definidos.
    """
    if round(porcentaje, 2) == 100.0:
        return "Exactamente iguales"
    elif porcentaje >= 75.0:
        return "Candidatas a clones"
    elif porcentaje >= 50.0:
        return "Similares"
    else:
        return "No similares"


def evaluar_similitud_funciones(
    funcion_base: Dict[str, Any],
    lista_funciones: List[Dict[str, Any]],
    n_gramas: int = 3,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Compara una función base contra una lista de funciones utilizando
    similitud de Jaccard sobre 3-gramas del AST serializado en pre-order.

    Parámetros:
        funcion_base: dict con claves ["nombre"], ["linea"], ["ast"], ["archivo"]
        lista_funciones: lista de dicts con claves ["nombre"], ["linea"], ["ast"], ["archivo"]
        n: tamaño del n-grama (por defecto 3)
        top_k: cantidad de resultados máximos a devolver (por defecto None, devuelve todos)

    Retorna:
        Lista de diccionarios con el top K de similitudes ordenadas descendentemente:
        - "archivo:nombre": str
        - "linea": int
        - "porcentaje_similitud": float
        - "decision_similitud": str
    """
    tokens_base = ast_a_tokens(funcion_base["ast"])
    ngramas_base = generar_ngramas(tokens_base, n=n_gramas)

    resultados = []

    for func in lista_funciones:
        tokens_comp = ast_a_tokens(func["ast"])
        ngramas_comp = generar_ngramas(tokens_comp, n=n_gramas)

        porcentaje = round(calcular_jaccard(ngramas_base, ngramas_comp), 2)
        decision = clasificar_similitud(porcentaje)

        resultados.append(
            {
                "archivo:nombre": f"{func['archivo']}:{func['nombre']}",
                "linea": func["linea"],
                "porcentaje_similitud": porcentaje,
                "decision_similitud": decision,
            }
        )

    # Ordenar las funciones por porcentaje de similitud de manera descendente
    resultados.sort(key=lambda x: x["porcentaje_similitud"], reverse=True)

    # Limitarlo al k configurado, siempre que sea posible
    if top_k is not None and top_k > 0:
        resultados = resultados[:top_k]
    return resultados