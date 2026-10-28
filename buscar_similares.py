import argparse
from extractores import extraer_funciones

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

  # Aquí iría tu lógica principal...
  funciones = extraer_funciones(args.dir)


if __name__ == '__main__':
  main()