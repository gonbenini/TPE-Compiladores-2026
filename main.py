from utils import get_program_code, get_logger, save_lexer_output, imprimir_arbol
from lexer import TpLexer
from parser import TpParser
import sys
import pprint

### Dependencias del lexer

program_code = get_program_code(sys.argv[1]) # esperamos que el primer argumento sea la direccion del archivo
_logger = get_logger()

# Definiciones del lenguaje (ppalabras reservadas y tabbla de simbolos)

PR = ( 'if', 'else', 'end_if', 'begin', 'end', 'pout', 'ret', 'class', 'function', 'longint', 'singlef', 'class', 'from', 'to', 'by', 'repeat', 'typedef', 'tol' )

TS = {
    # 'a': {'esPalabraR': False, 'type': 'IDENTIFICADOR'}
    # ejemplo de identificador, donde los mismos usan siempre tipo IDEN.
}

### Instanciaciones

lexer = TpLexer(_logger, TS, PR)
parser = TpParser()

### Invocacion

tokens = lexer.tokenize(program_code)
result = parser.parse(tokens)
#pprint.pprint(result, width=40)
from icecream import ic

#ic(result)
imprimir_arbol(result)

#save_lexer_output(tokens, TS)
# for t in tokens:
#     print(t)
