from sly import Parser
from lexer import TpLexer 

class TpParser(Parser):

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    @_('programa')
    def programa_I(self, p):
        return p

    @_('IDEN declaraciones BEGIN ejecutables END')
    def programa(self, p):
        return p

    @_('IDEN BEGIN ejecutables END')
    def programa(self, p):
        return p

    @_('declaracion')
    def declaraciones(self, p):
        return p

    @_('declaraciones declaracion')
    def declaraciones(self, p):
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

    @_('tipo FUNCTION IDEN "(" parametros_f ")" declaraciones BEGIN ejecutables END ";"',
       'tipo FUNCTION IDEN "(" parametros_f ")" BEGIN ejecutables END ";"')
    def funcion(self, p):
        return p

    @_('CLASS IDEN IDEN BEGIN declaraciones END ";"')
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

    @_('ejecutables ejecutable', 'ejecutable')
    def ejecutables(self, p):
        return p

    @_('asignacion', 'control', 'invocacion_funcion ";"', 'invocacion_metodo ";"', 'retorno')
    def ejecutable(self, p):
        return p

    @_('RET "(" expr ")" ";"')
    def retorno(self, p):
        return p

    @_('IDEN "." invocacion_funcion', 'invocacion_metodo "." invocacion_funcion')
    def invocacion_metodo(self, p):
        return p

    @_('IDEN "(" parametros ")" "[" posicionales "]"', 'IDEN "(" parametros ")"')
    def invocacion_funcion(self, p):
        return p

    @_('posicionales "," CONSTANTE_E', 'CONSTANTE_E')
    def posicionales(self, p):
        return p

    @_('asignable ASSIGN asignado ";"', 'asignable ASSIGN2P asignado ";"')
    def asignacion(self, p):
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
       'asignable', 'asignacion_de_linea', 'TOL "(" expr ")"')
    def factor(self, p):
        return p

    @_('IDEN ASSIGN IDEN', 'IDEN ASSIGN CONSTANTE_E',
       'IDEN ASSIGN CONSTANTE_F')
    def asignacion_de_linea(self, p):
        return p

    @_('parametros "," expr', 'expr')
    def parametros(self, p):
        return p

    @_('seleccion', 'iteracion')
    def control(self, p):
        return p

    @_('expr GT expr', 'expr LT expr',
       'expr GE expr', 'expr LE expr',
       'expr NE expr', 'expr EQ expr')
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