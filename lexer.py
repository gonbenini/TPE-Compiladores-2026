from sly import Lexer
import re

class TpLexer(Lexer):

    def __init__(self, _logger, TS, PR, tokens_out):
        # Inyectamos dependencias
        self._logger = _logger
        self.TS = TS
        self.PR = PR
        self.tokens_out = tokens_out

    tokens = { 
        IDEN, PLUS, MINUS, TIMES, DIVIDE, EQ, ASSIGN2P, ASSIGN, LE, LT, GE, GT, NE, 
        CONSTANTE_E, CONSTANTE_F, CADN,
        IF, ELSE, END_IF, BEGIN, END, POUT, RET, CLASS, FUNCTION, 
        LONGINT, SINGLEF, FROM, TO, BY, REPEAT, TYPEDEF, TOL, EXTENDS, PROGRAM
    }

    ignore = ' \t'
    ignore_COMMENT = r'//.*' #los comentarios son con "//" y el punto no incluye el salto de linea, por lo que salimos del comentario con \n
    literals = { '(', ')',',', ';', '[', ']', '.' }

    PLUS    = r'\+'
    MINUS   = r'-'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    EQ      = r'=='
    ASSIGN2P = r':=|:.' # prevenimos el error aceptando que despues de : venga cualquier cosa. el punto significa lo que vvenga
    ASSIGN = r'='
    LE      = r'<='
    LT      = r'<'
    GE      = r'>='
    GT      = r'>'
    NE      = r'!='

    @_(r'"[\s\S]*?"')
    def CADN(self, t):
        trimed_token_value = re.sub(r'\s+',' ',t.value)
        if trimed_token_value != t.value:
            self._logger.warning(f"Linea {self.lineno} | Se removieron elementos de la cadena multilinea como tabulaciones o saltos de linea")
        t.value = trimed_token_value
        self.TS[t.value] = {'type': 'CADN'}
        #self.tokens_out.append(t)
        return t

    def ASSIGN2P(self,t): # Si no es exactamente la definicion pero es parecido, avisamos
        if t.value not in (':=','='): 
            self._logger.warning(f"Linea {self.lineno} | Asignacion truncada para detectar error de sintaxis")
            t.value = ':=' # aca loggeamos como warning
            
        #self.tokens_out.append(t)
        return t


    def _check_flt_range(self,t):
        num = t.value
        
        if num == 0.0:
            return True
        if -3.40282347e38 < num < -1.17549435e-38:
            return True
        if 1.17549435e-38 < num < 3.40282347e38:
            return True
        return False


    def _check_int_range(self, t, max_num = (2**31) - 1, min_num = -2**31):
        num = t.value
        if num > max_num or num < min_num:
            return False
        else:
            return True


    #analizar con TS
    @_(r'[a-zA-Z][a-zA-Z0-9_]*')
    def IDEN(self, t):

        if len(t.value) > 22:
            old_t_value = t.value
            new_t_value= t.value[:22]
            self._logger.warning(f"Linea {self.lineno} | El identificador {old_t_value} truncado a {new_t_value} por ser mayor a 22 caracteres")
            t.value = new_t_value

        is_pr = t.value.lower() in self.PR

        if is_pr: # Si es palabra reservada esta guardado si o si porque se precarga.
            t.type = t.value.upper() # cambio el tipo de identificar a la palabra reservada (token) correcto.
            t.value = t.value.lower()
            
        elif not self.TS.get(t.value): # si es un identificador que no esta guardado.
            # cuando guardamos comprobamos que sea valido.
            iden = t.value

            # chequeamos que sea minuscula
            if iden.islower():
                self.TS[t.value] = {'type': 'IDENTIFICADOR'}
            else:
                self._logger.error(f"Linea {self.lineno} | ERROR Identificador con letras mayus.")
                return # devolvemos None en vez de un token ya que ocurrio un error. Luego de loggear podemos podemos seguir obteniendo proximos tokens

        #self.tokens_out.append(t)
        return t


    @_(r'\d+\$l')
    def CONSTANTE_E(self, t):
        t.value = int(t.value[:-2]) # removemos el sufijo $l
        if not self._check_int_range(t):
            self._logger.error(f"Linea {self.lineno} | ERROR constante entera fuera de rango.")
            return # no devolvemos nada

        if not self.TS.get(t.value):
            self.TS[t.value] = {'type': 'CONSTANTE ENTERA', 'count': 1}

        else:
            self.TS[t.value]['count'] += 1

        #self.tokens_out.append(t)
        return t


    @_(r'\d*\.\d+(s[-+]?\d+)?')
    def CONSTANTE_F(self, t):
        a = t.value.split('s')
        if len(a) == 2:
            base = float(a[0])
            exp = int(a[1])
            t.value = float(f"{base}e{exp}")
        else:
            t.value = float(a[0])

        if not self._check_flt_range(t):
            self._logger.error(f"Linea {self.lineno} | ERROR constante flotante fuera de rango.")
            return # no devolvemos nada

        if not self.TS.get(t.value):
            self.TS[t.value] = {'type': 'CONSTANTE FLOTANTE', 'count': 1}

        else:
            self.TS[t.value]['count'] += 1

        #self.tokens_out.append(t)
        return t


    @_(r'\n+')
    def newline(self, t):
        self.lineno += t.value.count('\n')


    def error(self, t):
        err = "'%s'" % t.value[0]
        self._logger.error(f"Linea {self.lineno} | ERROR caracter ilegal: {err}")
        self.index += 1

    def tokenize(self, text, lineno=1, index=0):
        for t in super().tokenize(text, lineno, index):
            self.tokens_out.append(t)
            yield t
