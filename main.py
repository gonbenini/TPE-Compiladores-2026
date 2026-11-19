from utils import get_logger, get_program_code, clean_TS, save_lexer_output
from lexer import TpLexer
from parser import TpParser
import sys
from assembly import GetAssembly

### Dependencias del lexer

program_code = get_program_code(sys.argv[1]) # esperamos que el primer argumento sea la direccion del archivo
_logger = get_logger()


# Definiciones del lenguaje (ppalabras reservadas y tabbla de simbolos)

PR = ( 'if', 'else', 'end_if', 'begin', 'end', 'pout', 'ret', 'class', 'function', 'longint', 'singlef', 'class', 'from', 'to', 'by', 'repeat', 'typedef', 'tol', 'extends', 'program' )

TS = {
    # 'a': {'type': 'IDENTIFICADOR'}
    # ejemplo de identificador, donde los mismos usan siempre tipo IDEN.
}

AS = []
arboles = {}

### Instanciaciones

tokens_out = []
lexer = TpLexer(_logger, TS, PR, tokens_out)
parser = TpParser(TS, _logger, arboles)

### Invocacion

tokens = lexer.tokenize(program_code)
result = parser.parse(tokens)
TS = clean_TS(TS) #limpieza de la TS antes de generar el assembler.
save_lexer_output(TS)
GetAssembly(result, TS, arboles)
