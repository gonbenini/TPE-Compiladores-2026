from sly import Lexer
import re

class TpLexer(Lexer):

    def __init__(self, _logger, TS, PR):
        # Inyectamos dependencias
        self._logger = _logger
        self.TS = TS
        self.PR = PR


    tokens = { IDEN, PLUS, MINUS, TIMES, DIVIDE, EQ, ASSIGN, LE, LT, GE, GT, NE, CONSTANTE_E, CONSTANTE_F, CADN}
    ignore = ' \t'
    ignore_COMMENT = r'//.*' #los comentarios son con "//"
    literals = { '(', ')',',', ';' }

    PLUS    = r'\+'
    MINUS   = r'-'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    EQ      = r'=='
    # la regla :. ya incluye :=, esto lo podemos minimizar
    ASSIGN  = r'=|:=|:.' # prevenimos el error aceptando que despues de : venga cualquier cosa. el punto significa lo que vvenga
    LE      = r'<='
    LT      = r'<'
    GE      = r'>='
    GT      = r'>'
    NE      = r'!='

    @_(r'"[\s\S]*?"')
    def CADN(self, t):
        t.value = t.value.replace('\n', '')
        t.value = re.sub('\s+',' ',t.value)
        self._logger.warning('Se removieron las tabulaciones de la cadena multilinea')
        #TS[t.value] = {'type': 'CONSTANTE CADENA', 'lineno': t.lineno, 'index': t.index, 'end': t.end} # [t.value]
        return t
        

    def ASSIGN(self,t): # Si no es exactamente la definicion pero es parecido, avisamos
        if t.value not in (':=','='): 
            self._logger.warning('Asignacion truncada para detectar error de sintaxis')
            t.value = ':=' # aca loggeamos como warning
        return t

    def _check_flt_range(self,t):
        num = t.value
        
        if num == 0.0:
            return True
        if -3.40282347e38 < num < -1.17549435e-38:  # loggear que truncamos
            return True
        if 1.17549435e-38 < num < 3.40282347e38:  # loggear que truncamos
            return True
        return False

    def _fix_flt_range(self, t):
            #print(t.value)
            if -1.17549435e-38 <= t.value <= 1.17549435e-38:
                t.value = 0.0
            elif t.value >= 3.40282347e38:
                t.value = 3.40282346e38
            else:
                t.value = -3.40282346e38

    def _range_constraint(self, num, max_num = (2**31) - 1, min_num = -2**31):
            if num > max_num:
                num = max_num
                self._logger.warning('Numero truncado a uno mas chico')
            elif num < min_num:
                num = min_num
                self._logger.warning('Numero truncado a uno mas grande')
            else:
                return num
            return num

    #analizar con TS
    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def IDEN(self, t):

        if len(t.value) > 22:
            t.value = t.value[:22] # aca loggeamos como warning
            self._logger.warning('Identificador truncado por ser mayor a 22 caracteres')

        # stored = PR.get(t.value.lower()) #convertimos t.value aca para buscar palabras reservadas en mismo formato.


        is_pr = t.value.lower() in self.PR


        if is_pr: # Si es palabra reservada esta guardado si o si porque se precarga.
            t.type = 'PR' # Cambiamos el tipo de token
            t.value = t.value.lower()
            
        
        elif not self.TS.get(t.value): # si es un identificador que no esta guardado.
            # cuando guardamos comprabmos que sea valido.
            iden = t.value

            #r'[a-z][a-z0-9_]*'
            # chequear que sea minuscula
            if iden.islower():
                self.TS[t.value] = {'type': 'IDENTIFICADOR', 'lineno': t.lineno, 'index': t.index, 'end': t.end}
            else:
                self._logger.error("ERROR Identificador con letras mayus.")#testear
                t.type = 'ERROR' #lo tiene que devolver o no?
                return # no devolvemos nada
            
        return t

    @_(r'\d+\$l')
    def CONSTANTE_E(self, t):
        t.value = int(t.value[:-2]) # removemos el sufijo $l
        t.value = self._range_constraint(t.value)
        self.TS[t.value] = {'type': 'CONSTANTE ENTERA', 'lineno': t.lineno, 'index': t.index, 'end': t.end}
        return t


    @_(r'\d*\.\d+(s[-+]?\d+)?')
    def CONSTANTE_F(self, t):
        a = t.value.split('s')
        if len(a) == 2:
            base = float(a[0])
            exp = int(a[1])
            # t.value = base**exp
            t.value = float(f"{base}e{exp}")
            #print(t.value, base, exp)
        else:
            t.value = float(a[0])

        if not self._check_flt_range(t):
            self._fix_flt_range(t)

        self.TS[t.value] = {'type': 'CONSTANTE FLOTANTE', 'lineno': t.lineno, 'index': t.index, 'end': t.end}
        return t


    @_(r'\n+')
    def newline(self, t):
        self.lineno += t.value.count('\n')


    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1
