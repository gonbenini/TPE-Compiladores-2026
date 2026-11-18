import logging

def get_program_code(file_path='./archivo.txt'):
    archivo = file_path

    with open(archivo, "r", encoding="utf-8") as f:
        texto = f.read()
    return texto

def get_logger_Lex(fn="./logLex.txt"):
    # instanciar logger
    open(fn, "w").close()
    logging.basicConfig(
        filename=fn,
        level=logging.DEBUG,
        format="%(asctime)s | %(funcName)s | %(message)s",
        force=True
    )

    _logger = logging.getLogger(__name__)
    return _logger

def get_logger_Err_Parsec(fn="./logParser.txt"):
    logger = logging.getLogger("Err_Parsec")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.FileHandler(fn, mode="w")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(funcName)s | %(message)s"
        )
    )

    logger.addHandler(handler)
    logger.propagate = False

    return logger

def get_assembly(fn="./assembly.wat"):
    logger = logging.getLogger(f"Assembly_WAT_{fn}")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.FileHandler(fn, mode="w", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)
    logger.propagate = False

    return logger

def get_logger_Parsec(fn="./InfoParser.txt"):
    logger = logging.getLogger("Parsec")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.FileHandler(fn, mode="w")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(message)s"
        )
    )

    logger.addHandler(handler)
    logger.propagate = False

    return logger

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

def check_flt_range(num):
    
    if num == 0.0:
        return True
    if -3.40282347e38 < num < -1.17549435e-38:
        return True
    if 1.17549435e-38 < num < 3.40282347e38:
        return True
    return False

def check_int_range(num, max_num = (2**31) - 1, min_num = -2**31):

    if num > max_num or num < min_num:
        return False
    else:
        return True

def clean_TS(TS):
    for i in list(TS.keys()):
        if (':main' not in i) and (TS[i]['type'] != 'CADN'):
            TS.pop(i)
            continue

        aux1 = i.replace('(', '_')
        aux1 = aux1.replace(')', '_')
        TS[aux1] = TS.pop(i)
    return TS