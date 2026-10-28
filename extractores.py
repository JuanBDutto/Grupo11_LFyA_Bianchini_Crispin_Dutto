
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
            "ast": ast.dump(node, indent=4),
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
