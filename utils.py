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