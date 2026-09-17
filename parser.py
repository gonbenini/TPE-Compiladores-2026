from math import nan

from sly import Parser
from lexer import TpLexer 

class TpParser(Parser):

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    @_('programa')
    def programa_I(self, p):
        return p

    @_(
    'program_in declaraciones BEGIN ejecutables END', 'program_in declaraciones ejecutables END',
    'program_in declaraciones BEGIN ejecutables', 'program_in declaraciones ejecutables',
    'declaraciones BEGIN ejecutables END', 'declaraciones ejecutables END',
    'declaraciones ejecutables', 'declaraciones BEGIN ejecutables'
    )
    def programa(self, p):

        if not hasattr(p, 'program_in'):
            print(f"Falta nombre de programa")

        if not hasattr(p, 'declaraciones'):
            print("Falta de declaraciones")

        if not hasattr(p, 'BEGIN'):
            print("Falta de BEGIN")

        if not hasattr(p, 'ejecutables'):
            print("Falta de ejecutables")

        if not hasattr(p, 'END'):
            print("Falta END")

        return p

    @_('PROGRAM IDEN')
    def program_in(self, p):
        return p

    @_('declaracion', 'declaraciones declaracion')
    def declaraciones(self, p):
        return p

    @_('declaraciones_clase declaracion_clase', 'declaracion_clase')
    def declaraciones_clase(self, p):
        return p

    @_('declaraciones_func declaracion_func', 'declaracion_func')
    def declaraciones_func(self, p):
        return p

    @_('dec_var ";"', 'funcion')
    def declaracion_func(self, p):
        return p

    @_('dec_var ";"', 'metodo')
    def declaracion_clase(self, p):
        return p

    @_('tipo IDEN "(" parametros_f ")" BEGIN ejecutables_func END ";"',)
    def metodo(self, p):
        return p
    
    @_('dec_var ";"', 'clase', 'funcion', 'tipoUsuario')
    def declaracion(self, p):
        return p

    @_('tipo id_vars')
    def dec_var(self, p):
        return p

    @_('SINGLEF', 'LONGINT', 'IDEN')
    def tipo(self, p):
        return p

    @_('id_vars "," IDEN', 'IDEN')
    def id_vars(self, p):
        return p

    @_('parametros_f "," parametro_f', 'parametro_f')
    def parametros_f(self, p):
        return p

    #error 6 y 7
    @_('tipo IDEN', 'tipo')
    def parametro_f(self, p):
        if len(p) == 1:
            print(f"Falta tipo o nombre de parametro formal en linea {p.lineno}")
        
        return p

    @_('tipo FUNCTION IDEN "(" parametros_f ")" declaraciones_func BEGIN ejecutables_func END ";"',
       'tipo FUNCTION IDEN "(" parametros_f ")" BEGIN ejecutables_func END ";"')
    def funcion(self, p):
        return p

    #error 4
    @_('funcion : tipo FUNCTION "(" parametros_f ")" declaraciones_func BEGIN ejecutables_func END ";"',
       'funcion : tipo FUNCTION "(" parametros_f ")" BEGIN ejecutables_func END ";"')
    def funcion_error(self, p):
        print(f"Falta de nombre de funcion en linea {p.lineno}")

    @_('CLASS IDEN IDEN BEGIN declaraciones_clase END ";"', 'CLASS IDEN IDEN BEGIN declaraciones_clase EXTENDS id_vars ";" END ";"',
       'CLASS IDEN BEGIN declaraciones_clase END ";"', 'CLASS IDEN BEGIN declaraciones_clase EXTENDS id_vars ";" END ";"',
       'CLASS IDEN IDEN BEGIN declaraciones_clase EXTENDS ";" END ";"', 'CLASS IDEN BEGIN declaraciones_clase EXTENDS ";" END ";"')
    def clase(self, p):
        if p._slice[2].type == 'BEGIN':
            print(f"Línea {p.lineno} | ERROR COD(17): Ausencia del código en la declaración de una clase.")
            return
        if p._slice[-4].type == 'EXTENDS':
            print(f"Línea {p.lineno} | ERROR COD(18): Ausencia de nombre o lista de clases después de extends.")
            return
        return p

    @_('TYPEDEF IDEN ASSIGN "[" constantes "]" ";"', 'TYPEDEF IDEN ASSIGN "[" "]" ";"')
    def tipoUsuario(self, p):
        if len(p) == 6:
            print(f"Línea {p.lineno} | ERROR COD(16): Ausencia de valores para la enumeración.")
            return
        return p

    @_('constantes "," constante', 'constante')
    def constantes(self, p):
        return p

    @_('CONSTANTE_E', 'CONSTANTE_F')
    def constante(self, p):
        return p

    #asignaciones

    @_('ejecutables_func ejecutable_func', 'ejecutable_func')
    def ejecutables_func(self, p):
            return p
    
    @_('asignacion_linea', 'asignacion', 'control_func', 'invocacion_funcion ";"', 'invocacion_metodo ";"', 'retorno', 'pout')
    def ejecutable_func(self, p):
            return p

    @_('ejecutables ejecutable', 'ejecutable')
    def ejecutables(self, p):
        return p

    @_('asignacion_linea', 'asignacion', 'control', 'invocacion_funcion ";"', 'invocacion_metodo ";"', 'pout')
    def ejecutable(self, p):
        return p

    @_('RET "(" expr ")" ";"')
    def retorno(self, p):
        return p

    @_('POUT "(" asignado ")" ";"', 'POUT "("  ")" ";"')
    def pout(self, p):
        if len(p) == 4: # atrapamos el error de invoicacion a pout sin argumentos
            print(f"Línea {p.lineno} | ERROR COD(10): Falta argumento en sentencia pout.")
            return
        return p

    #desambiguamos la gramatica ya que sino cuando venia un IDEN y un ".", la gramatica no sabia si reducir el IDEN
    #a "asignable" o consumirlo para que luego viniera una invocacion a metodo y reducirlo a invocacion_metodo.
    #a si, siempre que viene un IDEN lo convierte en asignable y opera a partir de ahi.
    #ademas, ahora gracias a esto podemos invocar metodos de atributos de objetos, por ejemplo a.b.c.d();
    @_('asignable "." invocacion_funcion', 'invocacion_metodo "." invocacion_funcion')
    def invocacion_metodo(self, p):
        return p

    @_('IDEN "(" parametros ")" "[" posicionales "]"', 'IDEN "(" parametros ")"')
    def invocacion_funcion(self, p):
        return p

    @_('posicionales "," CONSTANTE_E', 'CONSTANTE_E')
    def posicionales(self, p):
        return p

    @_('asignable ASSIGN2P asignado_linea ";"')
    def asignacion_linea(self, p):
        return p

    @_('asignable ASSIGN asignado ";"')
    def asignacion(self, p):
        return p

    @_('asignable "." IDEN', 'IDEN')
    def asignable(self, p):
        return p

    @_('expr', 'expr_linea')
    def expr_mixto(self, p):
        return p

    @_('term', 'term_linea')
    def term_mixto(self, p):
        return p

    @_('factor', 'factor_linea')
    def factor_mixto(self, p):
        return p

    @_('expr', 'CADN')
    def asignado(self, p):
        return p

    @_('expr PLUS term', 'expr MINUS term', 'term')
    def expr(self, p):
        return p
    
    @_('term TIMES factor', 'term DIVIDE factor', 'factor')
    def term(self, p):
        return p
    
    @_('constante', 'invocacion_funcion', 'invocacion_metodo',  'asignable', 'TOL "(" expr ")"')
    def factor(self, p):
        return p

    @_('expr_linea', 'CADN')
    def asignado_linea(self, p):
        return p

    @_('expr_linea PLUS term_mixto', 'expr_linea MINUS term_mixto', # al menos tenemos una asignacion de linea del lado izquierdo.
       'expr PLUS term_linea', 'expr MINUS term_linea', # al menos tenemos una asignacion de linea del lado derecho
       'term_linea'
    )
    def expr_linea(self, p):
        return p
    
    @_('term_linea TIMES factor_mixto', 'term_linea DIVIDE factor_mixto', # al menos tenemos una asignacion de linea del lado izquierdo.
       'term TIMES factor_linea', 'term DIVIDE factor_linea', # al menos tenemos una asignacion de linea del lado derecho
       'factor_linea'
    )
    def term_linea(self, p):
        return p
    
    @_('asignable ASSIGN IDEN', 'asignable ASSIGN CONSTANTE_E',
       'asignable ASSIGN CONSTANTE_F', 'asignable ASSIGN2P IDEN',
       'asignable ASSIGN2P CONSTANTE_E', 'asignable ASSIGN2P CONSTANTE_F'
    )
    def factor_linea(self, p):
        if p._slice[1].type == 'ASSIGN2P':
            print(f"Línea {p.lineno} | ERROR COD(15): Uso del símbolo ':=' donde debe usarse '='.")
        return p

    @_('parametros "," expr', 'expr')
    def parametros(self, p):
        return p

    @_('seleccion', 'iteracion')
    def control(self, p):
        return p

    @_('seleccion_func', 'iteracion_func')
    def control_func(self, p):
        return p

    @_('expr_mixto GT expr_mixto', 'expr_mixto LT expr_mixto',
       'expr_mixto GE expr_mixto', 'expr_mixto LE expr_mixto',
       'expr_mixto NE expr_mixto', 'expr_mixto EQ expr_mixto')
    def condicion(self, p):
        return p

    @_('IF "(" condicion ")" cuerpo_control END_IF ";"',
       'IF "(" condicion ")" cuerpo_control ELSE cuerpo_control END_IF ";"')
    def seleccion(self, p):
        return p

    @_('FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT cuerpo_control ";"')
    def iteracion(self, p):
        return p
    
    @_('BEGIN ejecutables END', 'ejecutable')
    def cuerpo_control(self, p):
        return p

    @_('IF "(" condicion ")" cuerpo_control_func END_IF ";"',
        'IF "(" condicion ")" cuerpo_control_func ELSE cuerpo_control_func END_IF ";"')
    def seleccion_func(self, p):
            return p
    
    @_('FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT cuerpo_control_func ";"')
    def iteracion_func(self, p):
        return p
        
    @_('BEGIN ejecutables_func END', 'ejecutable_func')
    def cuerpo_control_func(self, p):
        return p

    def error(self, p):
        print(f"Error sintactico en linea {p.lineno} cerca de '{p.value}'")
        if not p:
            print("End of File!")
            return
        
        while True:
            tok = next(self.tokens, None)
            if not tok or tok.type == ';':
                break
        self.restart()