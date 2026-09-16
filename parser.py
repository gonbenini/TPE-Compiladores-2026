from sly import Parser
from lexer import TpLexer 

class TpParser(Parser):

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    @_('programa')
    def programa_I(self, p):
        return p

    @_('IDEN declaraciones BEGIN ejecutables END', 'IDEN BEGIN ejecutables END')
    def programa(self, p):
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

    @_('tipo IDEN')
    def parametro_f(self, p):
        return p

    @_('tipo FUNCTION IDEN "(" parametros_f ")" declaraciones_func BEGIN ejecutables_func END ";"',
       'tipo FUNCTION IDEN "(" parametros_f ")" BEGIN ejecutables_func END ";"')
    def funcion(self, p):
        return p

    @_('CLASS IDEN IDEN BEGIN declaraciones_clase END ";"', 'CLASS IDEN IDEN BEGIN declaraciones_clase EXTENDS id_vars ";" END ";"')
    def clase(self, p):
        return p

    @_('TYPEDEF IDEN ASSIGN "[" constantes "]" ";"')
    def tipoUsuario(self, p):
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

    @_('asignable ASSIGN2P asignado ";"')
    def asignacion(self, p):
        return p

    @_('asignable ASSIGN2P asignado_linea ";"')
    def asignacion_linea(self, p):
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

    @_('asignable ASSIGN IDEN', 
       'asignable ASSIGN CONSTANTE_E',
       'asignable ASSIGN CONSTANTE_F',
       'asignable ASSIGN2P IDEN', 
       'asignable ASSIGN2P CONSTANTE_E',
       'asignable ASSIGN2P CONSTANTE_F')
    def asignacion_de_linea(self, p):
        # Con este cambio puede que `factor_linea` quede deprecado
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

    @_('expr_linea GT expr_linea', 'expr_linea LT expr_linea',
       'expr_linea GE expr_linea', 'expr_linea LE expr_linea',
       'expr_linea NE expr_linea', 'expr_linea EQ expr_linea')
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