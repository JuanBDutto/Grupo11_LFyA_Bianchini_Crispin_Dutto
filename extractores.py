
import ast
from pathlib import Path


class ExtractorFuncionesAST(ast.NodeVisitor):
    """Extrae definiciones de funciones de un árbol AST."""

    def __init__(self, archivo):
        self.archivo = str(archivo)
        self.funciones = []

    def visit_FunctionDef(self, node):
        self._registrar_funcion(node)
        # Continúa recorriendo para detectar funciones anidadas.
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._registrar_funcion(node)
        # Continúa recorriendo para detectar funciones asíncronas anidadas.
        self.generic_visit(node)

    def _registrar_funcion(self, node):
        self.funciones.append({
            "nombre": node.name,
            "archivo": self.archivo,
            "linea": node.lineno,
            "ast": node,
        })


def extraer_funciones(directorio):
    """
    Recorre recursivamente un directorio y extrae todas las funciones
    definidas en sus archivos Python.

    Args:
        directorio: Ruta del directorio raíz que se analizará.

    Returns:
        Lista de diccionarios con nombre, archivo, línea y subárbol AST.
    """
    raiz = Path(directorio)

    if not raiz.is_dir():
        raise NotADirectoryError(
            f"El directorio no existe o no es válido: {raiz}"
        )

    funciones = []

    for archivo in sorted(raiz.rglob("*.py")):
        try:
            codigo_fuente = archivo.read_text(encoding="utf-8")
            arbol = ast.parse(
                codigo_fuente,
                filename=str(archivo),
            )

            visitante = ExtractorFuncionesAST(archivo)
            visitante.visit(arbol)

            funciones.extend(visitante.funciones)

        except (SyntaxError, UnicodeDecodeError, OSError) as error:
            # Un archivo problemático no impide procesar los demás.
            print(f"Error al procesar {archivo}: {error}")

    return funciones

def _iterar_funciones_ast(nodo):
    """Recorre el AST en profundidad y emite nodos de función uno a uno."""
    for hijo in ast.iter_child_nodes(nodo):
        if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield hijo
        yield from _iterar_funciones_ast(hijo)


def _resolver_archivo(ruta_objetivo, directorio_base=None):
    """
    Busca el archivo como ruta directa (incluso fuera de directorio_base)
    o dentro de directorio_base y sus subdirectorios.
    """
    candidato = Path(ruta_objetivo)

    # 1. Ruta directa (absoluta o relativa al directorio de ejecución actual, fuera o dentro de args.dir)
    if candidato.is_file():
        return candidato.resolve()

    # 2. Si se proporciona directorio_base, buscar dentro de él
    if directorio_base is not None:
        raiz = Path(directorio_base).resolve()
        en_raiz = (raiz / candidato).resolve()
        if en_raiz.is_file():
            return en_raiz

        # Equivalente al .endswith() original sin parsear los demás archivos .py
        coincidencias = [
            p.resolve() for p in sorted(raiz.rglob(f"*{candidato.name}"))
            if p.as_posix().endswith(candidato.as_posix())
        ]
        if coincidencias:
            return coincidencias[0]

    raise FileNotFoundError(f"No existe el archivo: {ruta_objetivo}")


def buscar_funcion(referencia, directorio_base=None):
    """
    Busca una función en un archivo concreto deteniendo el recorrido
    del AST en cuanto la encuentra.
    """
    archivo_objetivo, separador, nombre_objetivo = referencia.rpartition(":")

    if not separador or not archivo_objetivo or not nombre_objetivo:
        raise ValueError("--funcion debe tener el formato archivo.py:mi_funcion")

    archivo = _resolver_archivo(archivo_objetivo, directorio_base)

    if archivo.suffix != ".py":
        raise ValueError("El archivo objetivo debe ser Python (.py)")

    codigo = archivo.read_text(encoding="utf-8")
    arbol = ast.parse(codigo, filename=str(archivo))

    # next() detiene el recorrido del AST en cuanto encuentra la primera coincidencia
    nodo_encontrado = next(
        (nodo for nodo in _iterar_funciones_ast(arbol) if nodo.name == nombre_objetivo),
        None,
    )

    if nodo_encontrado is None:
        raise LookupError(f"No se encontró la función '{nombre_objetivo}' en {archivo}")

    return {
        "nombre": nodo_encontrado.name,
        "archivo": str(archivo),
        "linea": nodo_encontrado.lineno,
        "ast": nodo_encontrado,
    }