import argparse
from extractores import extraer_funciones, buscar_funcion
from normalizacion import normalize
from similitud_jaccard import evaluar_similitud_funciones
import os
def main():
    # 1. Crear el objeto parser que gestionará los argumentos
    parser = argparse.ArgumentParser(
        description='Busca funciones similares en un repositorio de código.'
    )

    # 2. Definir los argumentos que esperamos recibir
    parser.add_argument(
        '--dir',
        type=str,
        required=True,
        help='Ruta al directorio del repositorio a analizar',
    )

    parser.add_argument(
        '--funcion',
        type=str,
        required=True,
        help='Función a buscar en formato archivo.py:mi_funcion',
    )

    parser.add_argument(
        '--top',
        type=int,
        default=5,
        help='Número máximo de resultados similares a mostrar (por defecto: 5)',
    )

    # 3. Leer/procesar los argumentos de la línea de comandos
    args = parser.parse_args()

    # 4. Usar los valores en tu programa
    print(f'Analizando el directorio: {args.dir}')
    print(f'Buscando similitudes para: {args.funcion}')
    print(f'Mostrando el top: {args.top}')

    # Primero extraemos las funciones utilizando el extractor de funciones
    # Obteniendo una lista de diccionarios del estilo: ["nombre"], ["archivo"], ["linea"] y ["ast"]
    funciones = extraer_funciones(args.dir)

    # Buscar función objetivo con la que comparar; si falla, que no siga
    try:
        objetivo = buscar_funcion(args.funcion, directorio_base=args.dir)
    except (ValueError, FileNotFoundError, LookupError) as error:
        parser.error(str(error))

    # Si la función estaba entre las funciones originales, quitarla de la comparacion
    funciones = [
        f for f in funciones
        if not (
            f["nombre"] == objetivo["nombre"]
            and f["linea"] == objetivo["linea"]
            and os.path.abspath(f["archivo"]) == os.path.abspath(objetivo["archivo"])
        )
    ]
    # Por cada funcion, la normalizamos
    # El normalizador modifica el arbol en memoria (referencia), por lo que quedaría normalizado en el mismo lugar ["ast"] 
    for f in funciones:
        normalize(f["ast"])
    normalize(objetivo["ast"])
    resultados = evaluar_similitud_funciones(objetivo,funciones,n_gramas = 3,top_k = args.top)
    print(f"\n{'UBICACIÓN / LÍNEA':<24} {'SIMILITUD':<14} {'DECISIÓN'}")
    print("-" * 62)
    print("\n".join(f"▸ {os.path.relpath(r['archivo:nombre'], args.dir)}\n  {'Línea ' + str(r['linea']):<22} {r['porcentaje_similitud']:>6.2f}%       {r['decision_similitud']}" for r in resultados))
    print("-" * 62)
if __name__ == '__main__':
    main()