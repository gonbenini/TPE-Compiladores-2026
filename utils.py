import logging


def get_program_code(file_path='./archivo.txt'):
    archivo = file_path

    with open(archivo, "r", encoding="utf-8") as f:
        texto = f.read()
    return texto


def get_logger(fn="./log.txt"):
    # instanciar logger
    open(fn, "w").close()
    logging.basicConfig(
        filename=fn,
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s",
        force=True
    )

    _logger = logging.getLogger(__name__)
    return _logger

def save_lexer_output(tokens, TS):
    # Guarda en un archivo los tokens generados
    with open ("tokens.txt", "w") as f:
        # corregir cuando recorremos los tokens los perdemos.
        for t in tokens:
            f.write(f"{t}\n")

    # Guarda en un archivo los Identificadores reconocidos.
    with open ("TS.txt", "w") as f:
        for t in TS:
            atrs = TS[t]
            f.write(f"{t} {atrs} \n")

'''
def token_line_generator(lexer, texto):
    # utilidad para mandarle al Tokenize del lexer por linea en vez de por archivo.
    # se instancia haciendo `tokens = token_producer()` y luego se puede iterar.
    f = open("tokens.txt", "r", encoding="utf-8")
    for linea in texto.splitlines():
        for token in lexer.tokenize(linea): 
            f.write(token) 
            yield token

    close(f)
'''

def imprimir_arbol(nodo, prefijo="", es_ultimo=True, es_raiz=True):
    # Si el nodo no es una tupla (es decir, es un string o número final como 'begin' o 4)
    if not isinstance(nodo, tuple):
        marcador = "└── " if es_ultimo else "├── "
        print(prefijo + (marcador if not es_raiz else "") + str(nodo))
        return

    # Si es una tupla, el primer elemento es el nombre del nodo (ej: 'ejecutable')
    nombre_nodo = str(nodo[0])
    marcador = "└── " if es_ultimo else "├── "
    print(prefijo + (marcador if not es_raiz else "") + nombre_nodo)

    # Los siguientes elementos de la tupla son sus hijos
    hijos = nodo[1:]
    
    # Calculamos el prefijo para los hijos (para que las líneas verticales conecten bien)
    nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ") if not es_raiz else ""
    
    # Iteramos y llamamos a la función de forma recursiva
    for i, hijo in enumerate(hijos):
        imprimir_arbol(hijo, nuevo_prefijo, i == (len(hijos) - 1), False)