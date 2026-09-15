from sly import Parser
from lexer import TpLexer 


class TpParser(Parser):

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    @_('programa')
    def programa_I(self, p):
        return p

    @_(
    'program_in declaraciones BEGIN ejecutables END',

    'program_in declaraciones ejecutables END',

    'program_in declaraciones BEGIN ejecutables',

    'program_in declaraciones ejecutables',

    'declaraciones BEGIN ejecutables END',

    'declaraciones ejecutables END',

    'declaraciones ejecutables',

    'declaraciones BEGIN ejecutables'
    )
    def programa(self, p):

        if not hasattr(p, 'program_in'):
            print("Falta nombre de programa")

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

    @_('declaraciones declaracion', 'declaracion')
    def declaraciones(self, p):
        return p

    @_('declaraciones_clase declaracion_clase', 'declaracion_clase')
    def declaraciones_clase(self, p):
        return p

    @_('declaraciones_func declaracion_func', 'declaracion_func')
    def declaraciones_func(self, p):
        return p

    @_('dec_var ";"', 'funcion ";"')
    def declaracion_func(self, p):
        return p

    #manejo de falta de ";"
    @_('dec_var', 'funcion')
    def declaracion_func(self, p):
        print(f"Falta de ';' en linea {p.lineno}")


    @_('dec_var ";"', 'metodo ";"')
    def declaracion_clase(self, p):
        return p

    #manejo de falta de ";"
    @_('dec_var', 'metodo')
    def declaracion_clase(self, p):
        print(f"Falta de ';' en linea {p.lineno}")

    @_('tipo IDEN "(" parametros_f ")" BEGIN ejecutables_func END')
    def metodo(self, p):
        print('Declaracion metodo')
        return p
    
    @_('dec_var ";"', 'clase ";"', 'funcion ";"', 'tipoUsuario ";"')
    def declaracion(self, p):
        return p

    #manejo de falta de ";"
    @_('dec_var', 'clase', 'funcion', 'tipoUsuario')
    def declaracion(self, p):
        print(f"Falta de ';' en declaracion de linea {p.lineno}")

    @_('tipo id_vars')
    def dec_var(self, p):
        print('Declaracion variable')
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

    @_('tipo IDEN')
    def parametro_f(self, p):
        return p

    @_('tipo FUNCTION IDEN "(" parametros_f ")" declaraciones_func BEGIN ejecutables_func END',
       'tipo FUNCTION IDEN "(" parametros_f ")" BEGIN ejecutables_func END')
    def funcion(self, p):
        print('Declaracion funcion')
        return p

    @_('CLASS IDEN IDEN BEGIN declaraciones_clase END', 'CLASS IDEN IDEN BEGIN declaraciones_clase EXTENDS id_vars ";" END')
    def clase(self, p):
        print('Declaracion clase')
        return p

    @_('TYPEDEF IDEN ASSIGN "[" constantes "]"')
    def tipoUsuario(self, p):
        print('Declaracion tipo usuario')
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
    
    @_('asignacion', 'asignacion_linea', 'control_func', 'invocacion_funcion ";"', 'invocacion_metodo ";"', 'retorno', 'pout')
    def ejecutable_func(self, p):
            return p

    @_('ejecutables ejecutable', 'ejecutable')
    def ejecutables(self, p):
        return p

    @_('asignacion', 'asignacion_linea', 'control', 'invocacion_funcion ";"', 'invocacion_metodo ";"', 'pout')
    def ejecutable(self, p):
        return p

    @_('RET "(" expr ")" ";"')
    def retorno(self, p):
        print('Retorno')
        return p

    @_('POUT "(" asignado ")" ";"')
    def pout(self, p):
        print('print')
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
        print('Invocacion')
        return p

    @_('posicionales "," CONSTANTE_E', 'CONSTANTE_E')
    def posicionales(self, p):
        return p

    @_('asignable ASSIGN asignado ";"')
    def asignacion(self, p):
        print('asignacion')
        return p

    @_('asignable ASSIGN2P asignado_linea ";"')
    def asignacion_linea(self, p):
        print('asignacion')
        return p

    @_('asignable "." IDEN', 'IDEN')
    def asignable(self, p):
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
    
    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'TOL "(" expr ")"')
    def factor(self, p):
        return p

    @_('expr_linea', 'CADN')
    def asignado_linea (self, p):
        return p

    @_('expr_linea PLUS term_linea', 'expr_linea MINUS term_linea', 'term_linea')
    def expr_linea(self, p):
        return p
    
    @_('term_linea TIMES factor_linea', 'term_linea DIVIDE factor_linea', 'factor_linea')
    def term_linea(self, p):
        return p
    
    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'asignacion_de_linea', 'TOL "(" expr ")"')
    def factor_linea(self, p):
        return p

    @_('asignable ASSIGN IDEN', 'asignable ASSIGN CONSTANTE_E',
       'asignable ASSIGN CONSTANTE_F')
    def asignacion_de_linea(self, p):
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

    @_('expr_linea GT expr_linea', 'expr_linea LT expr_linea',
       'expr_linea GE expr_linea', 'expr_linea LE expr_linea',
       'expr_linea NE expr_linea', 'expr_linea EQ expr_linea')
    def condicion(self, p):
        return p

    @_('IF "(" condicion ")" cuerpo_control END_IF ";"',
       'IF "(" condicion ")" cuerpo_control ELSE cuerpo_control END_IF ";"')
    def seleccion(self, p):
        print('seleccion')
        return p

    @_('IF "(" condicion ")" cuerpo_control error ";"')
    def seleccion(self, p):
        print("falta de END_IF")

    @_('FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT cuerpo_control ";"')
    def iteracion(self, p):
        print('iteracion')
        return p
    
    @_('BEGIN ejecutables END ";"', 'ejecutable')
    def cuerpo_control(self, p):
        return p

    @_('IF "(" condicion ")" cuerpo_control_func END_IF ";"',
        'IF "(" condicion ")" cuerpo_control_func ELSE cuerpo_control_func END_IF ";"')
    def seleccion_func(self, p):
        print('seleccion')
        return p

    
    @_('FROM IDEN ASSIGN2P CONSTANTE_E TO CONSTANTE_E BY CONSTANTE_E REPEAT cuerpo_control_func ";"')
    def iteracion_func(self, p):
        print('iteracion')
        return p
        
    @_('BEGIN ejecutables_func END', 'ejecutable_func')
    def cuerpo_control_func(self, p):
        return p

    def error(self, p):
        if p is None:
            print("Error: falta END")