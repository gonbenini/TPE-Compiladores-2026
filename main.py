from utils import get_logger_Lex, get_logger_Parsec, get_program_code, save_lexer_output, get_logger_Err_Parsec, clean_TS
from lexer import TpLexer
from parser import TpParser
import sys
from assembly import GetAssembly

### Dependencias del lexer

program_code = get_program_code(sys.argv[1]) # esperamos que el primer argumento sea la direccion del archivo
_loggerLex = get_logger_Lex()
_InfoParsec = get_logger_Parsec()
_loggerParsec = get_logger_Err_Parsec()


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
lexer = TpLexer(_loggerLex, TS, PR, tokens_out)
parser = TpParser(TS, AS, _InfoParsec, _loggerParsec, arboles)

### Invocacion

tokens = lexer.tokenize(program_code)
result = parser.parse(tokens)
TS = clean_TS(TS) #limpieza de la TS antes de generar el assembler.
save_lexer_output(tokens_out, TS)
GetAssembly(result, TS, arboles)
