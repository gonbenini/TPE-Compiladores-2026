from hmac import new

from sly import Parser
from lexer import TpLexer
from utils import check_flt_range, check_int_range

class TpParser(Parser):

    def __init__(self, TS, _info, _logger, ambito):
        # Inyectamos dependencias
        self.TS = TS
        self._InfoLogger = _info
        self._logger = _logger
        self.ambito = ambito
        self.arboles={}

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    precedence = (
        ('right', 'error'),
        ('right', 'END', ';'),
    )

    class NodoUnario:
        def __init__(self, op, son='NIL'):
            self.op = op
            self.son = son

    class NodoBinario:
        def __init__(self, op, left='NIL', right='NIL'):
            self.op = op
            self.left = left
            self.right = right    

    class NodoHoja:
        def __init__(self, tipo, operando) -> None:
            self.tipo=tipo
            self.operando=operando


    def imprimir_arbol(self, nodo, nivel=0, relacion="Raíz"):
        sangria = "    " * nivel
        
        # Si el nodo es 'NIL' o None, no hacemos nada
        if nodo == 'NIL' or nodo is None:
            return

        # Verificamos si es un objeto de tipo Nodo (tiene el atributo 'op')
        if hasattr(nodo, 'op'):
            print(f"{sangria}[{relacion}] -> {nodo.op}")
            
            # Llamada recursiva para el hijo izquierdo
            if hasattr(nodo, 'left'):
                self.imprimir_arbol(nodo.left, nivel + 1, "Hijo izq")
                
            # Llamada recursiva para el hijo derecho
            if hasattr(nodo, 'right'):
                self.imprimir_arbol(nodo.right, nivel + 1, "Hijo der")

            if hasattr(nodo, 'son'):
                self.imprimir_arbol(nodo.son, nivel + 1, "Hijo")
        else:
            # Si no es un nodo (es un string o número final), entra acá
            print(f"{sangria}[{relacion}] -> {nodo}")

    def alcance(self, name):
        ambito_aux = self.ambito
        encontrado = False
        search_name = name + ':' + ambito_aux
        while ambito_aux != 'main':
            search_name = name + ':' + ambito_aux
            if search_name in self.TS:
                encontrado = True
                break
            ambito_aux = ambito_aux.rsplit(":", 1)[0]

        if ambito_aux == 'main' and not encontrado:
            if (name + ':' + 'main') in self.TS:
                print(f"Variable {search_name} encontrada")
                return True

            else:
                print(f"Variable {name} no declarada o no alcanzable")
                return False
            
        elif encontrado:
            print(f"Variable {search_name} encontrada")
            return True

        else: 
            print(f"Variable {name} no declarada o no alcanzable")
            return False

    def atributo_valido(self, p):
        check = (p.asignable.operando).split(".")[-1]

        if (check + ':' + 'main:(' + p.asignable.tipo + ')') in self.TS:
            clase = self.TS[check + ':' + 'main:(' + p.asignable.tipo + ')']['type']
            #aca habia un problema si una var se llamaba igual que un atributo de una clase
            #asique priorizamos la busqueda de atributos/metodos
            #print(check + ':' + 'main:(' + p.asignable.tipo + ')')
        else:
            clase = self.TS[check + ':' + self.ambito]['type']
            #print(check + ':' + self.ambito)

        #print(clase)
        if self.TS[clase + ':' + 'main']['type'] == 'CLASS':
            if (p.IDEN + ':' + 'main' + ':(' + clase + ')') in self.TS:
                print('valido')
            else:
                print('no valido')
        else: print('xd')

    #----------------------------ESTRUCTURA PRINCIPAL---------------------------------------------

    @_('programa')
    def programa_I(self, p):
        return p

    @_('program_in declaraciones cuerpo_ejecutable')
    def programa(self, p):
        self.imprimir_arbol(p.cuerpo_ejecutable)
        print(self.arboles)
        return p

    @_('PROGRAM IDEN')
    def program_in(self, p):
        self.TS[p.IDEN]['uso'] = 'Nombre de programa'
        return p

    #----------------------------DECLARACIONES---------------------------------------------

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

    @_('ambito_metodo parametros_f ")" cuerpo_ejecutable')
    def metodo(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de metodo")
        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        new_name = p.ambito_metodo['name'] + ':' + self.ambito
        self.arboles[new_name] = {'nodo': p.cuerpo_ejecutable} #guardamos arbol sintactico de la funcion
        self.TS[new_name] = self.TS.pop(p.ambito_metodo['name'])
        self.TS[new_name]['type'] = p.ambito_metodo['tipo']
        self.TS[new_name]['uso'] = 'Nombre de metodo'

        return p

    @_('tipo IDEN "("')
    def ambito_metodo(self, p):
        self.ambito = self.ambito + ':' + p.IDEN
        return {'tipo': p.tipo, 'name': p.IDEN}

    @_('BEGIN ejecutables END ";"')
    def cuerpo_ejecutable(self, p):
        return p.ejecutables
    
    @_('dec_var ";"', 'clase', 'funcion', 'tipoUsuario')
    def declaracion(self, p):
        return p
    
    @_('tipo id_vars')
    def dec_var(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de variable/s")
        for i in p.id_vars:
            new_name = i + ':' + self.ambito
            self.TS[new_name] = self.TS.pop(i)
            self.TS[new_name]['type'] = p.tipo
            self.TS[new_name]['uso'] = 'Nombre de variable'
        return p

    @_('SINGLEF', 'LONGINT', 'IDEN')
    def tipo(self, p):
        return p[0]

    @_('id_vars "," IDEN', 'IDEN')
    def id_vars(self, p):
        if len(p) == 1:
            return [p.IDEN]
        else:
            arr = p.id_vars.split(',')
            arr.append(p.IDEN)
            return arr

    @_('parametros_f "," parametro_f', 'parametro_f')
    def parametros_f(self, p):
        return p

    @_('tipo IDEN')
    def parametro_f(self, p):
        new_name = p.IDEN + ':' + self.ambito
        self.TS[new_name] = self.TS.pop(p.IDEN)
        self.TS[new_name]['type'] = p.tipo
        self.TS[new_name]['uso'] = 'Nombre de variable'
        return p

    @_('ambito_func "(" parametros_f ")" declaraciones_func cuerpo_ejecutable',
       'ambito_func "(" parametros_f ")" cuerpo_ejecutable')
    def funcion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de funcion")
        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        new_name = p.ambito_func['name'] + ':' + self.ambito
        self.arboles[new_name] = {'nodo': p.cuerpo_ejecutable} #guardamos arbol sintactico de la funcion
        self.TS[new_name] = self.TS.pop(p.ambito_func['name'])
        self.TS[new_name]['type'] = p.ambito_func['tipo']
        self.TS[new_name]['uso'] = 'Nombre de funcion'
        return p

    @_('tipo FUNCTION IDEN')
    def ambito_func(self, p):
        self.ambito = self.ambito + ':' + p[2]
        return {'tipo': p.tipo, 'name': p.IDEN}

    @_('ambito_clase BEGIN declaraciones_clase END ";"', 'ambito_clase BEGIN declaraciones_clase EXTENDS id_vars ";" END ";"')
    def clase(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de clase")
        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        new_name = p.ambito_clase + ':' + self.ambito
        self.TS[new_name] = self.TS.pop(p.ambito_clase)
        self.TS[new_name]['type'] = 'CLASS'
        self.TS[new_name]['uso'] = 'Nombre de clase'
        return p

    @_('CLASS IDEN IDEN')
    def ambito_clase(self, p):
        self.ambito = self.ambito + ':' + '(' + p[1] + ')'
        return p.IDEN0

    @_('TYPEDEF IDEN ASSIGN "[" constantes "]" ";"')
    def tipoUsuario(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de tipo usuario")
        return p

    @_('constantes "," constante', 'constante')
    def constantes(self, p):
        return p

    @_('CONSTANTE_E', 'CONSTANTE_F', 'MINUS CONSTANTE_E', 'MINUS CONSTANTE_F')
    def constante(self, p):
        if len(p) == 2:
            key = p[1]

            if hasattr(p, 'CONSTANTE_E'):
                tipo_dato = 'CONSTANTE_E'  # (O el string exacto que uses en tu TS)
            else:
                tipo_dato = 'CONSTANTE_F'

            if self.TS[key]['count'] == 1:
                del self.TS[key]

            elif self.TS[key]['count'] > 1:
                self.TS[key]['count'] -= 1

            nueva_key = '-' + str(key)
            if nueva_key in self.TS:
                self.TS[nueva_key]['count'] += 1
            else:
                # Diccionario corregido
                self.TS[nueva_key] = {'type': tipo_dato, 'count': 1}

            if (tipo_dato == 'CONSTANTE_E') & (not check_int_range(key)):
                print("Error constante negativa fuera de rango")

            elif (tipo_dato == 'CONSTANTE_F') & (not check_flt_range(key)):
                print("Error constante negativa fuera de rango")

        return p

    #----------------------------EJECUTABLES---------------------------------------------
    @_('ejecutables ejecutable', 'ejecutable')
    def ejecutables(self, p):
        if len(p) == 1:
            return self.NodoUnario('S', p.ejecutable)
        else:
            return self.NodoBinario('S', p.ejecutables, p.ejecutable)

    @_('asignacion', 'asignacion_linea', 'control', 'invocacion_funcion ";"', 'invocacion_metodo ";"', 'retorno', 'pout')
    def ejecutable(self, p):
        return p[0]

    @_('RET "(" expr ")" ";"')
    def retorno(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia retorno")
        return self.NodoUnario('RET', p.expr)
    
    @_('POUT "(" expr ")" ";"', 'POUT "(" CADN ")" ";"')
    def pout(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia pout")
        return self.NodoUnario('POUT', p[2])
    
    @_('asignable "." IDEN "(" parametros ")" "[" posicionales "]"', 'asignable "." IDEN "(" parametros ")"')
    def invocacion_metodo(self, p): #invocacion_m . invocacion_f -> invocacion_m . invocacion_f . invocacion_f - > a.b.c.m().m1().m2()
        self._InfoLogger.info(f"Linea {p.lineno} | Invocacion a metodo")
        call_name = p.asignable.operando + '.' + p.IDEN
        self.atributo_valido(p)
        return self.NodoUnario('CALL ' + call_name, self.arboles['m:main:(ca)']['nodo'])

    @_('IDEN "(" parametros ")" "[" posicionales "]"', 'IDEN "(" parametros ")"')
    def invocacion_funcion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Invocacion a funcion")
        self.alcance(p.IDEN)
        return self.NodoUnario('CALL ' + p[0], self.arboles['f1:main']['nodo'])

    @_('posicionales "," CONSTANTE_E', 'posicionales "," MINUS CONSTANTE_E', 
       'CONSTANTE_E', 'MINUS CONSTANTE_E')
    def posicionales(self, p):
        return p

    @_('asignable ASSIGN expr ";"')
    def asignacion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de asignacion")
        return self.NodoBinario('=', p.asignable.operando, p.expr)

    @_('asignable ASSIGN2P expr_linea ";"')
    def asignacion_linea(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia asignacion de linea")
        return self.NodoBinario(':=', p.asignable.operando, p.expr_linea)

    @_('asignable "." IDEN', 'IDEN') #asingable.IDEN -> asignable.IDEN.IDEN
    #la idea seria desde aca controlar que todas las vars esten al alcance y ademas
    #para atributos de clases chequear que justamente esa clase contenga esos atributos
    def asignable(self, p):
        if len(p) == 3:
            self.atributo_valido(p)
            check = (p.asignable.operando).split(".")[-1]
            if (check + ':' + self.ambito) in self.TS:
                clase = self.TS[check + ':' + self.ambito]['type']

            else: clase = self.TS[check + ':' + 'main:(' + p.asignable.tipo + ')']['type']
            return self.NodoHoja(clase, p.asignable.operando + '.' + p.IDEN)
        else:
            self.alcance(p.IDEN)
            return self.NodoHoja(self.TS[p.IDEN + ':' + self.ambito]['type'], p.IDEN)

    @_('expr PLUS term', 'expr MINUS term', 'term')
    def expr(self, p):
        if len(p) == 3:
            return self.NodoBinario(p[1], p.expr, p.term)
        else:
            return p.term

    @_('term TIMES factor', 'term DIVIDE factor', 'factor')
    def term(self, p):
        if len(p) == 3:
            return self.NodoBinario(p[1], p.term, p.factor)
        else:
            return p.factor

    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'TOL "(" expr ")"')
    def factor(self, p):
        if len(p) == 1:
            if hasattr(p, 'asignable'): return p.asignable.operando
            else:
                return p[0]
        else:
            return self.NodoBinario('TOL', p.expr)

    @_('expr_linea PLUS term_linea', 'expr_linea MINUS term_linea', 'term_linea')
    def expr_linea(self, p):
        if len(p) == 3:
            return self.NodoBinario(p[1], p.expr_linea, p.term_linea)
        else:
            return p.term_linea
    
    @_('term_linea TIMES factor_linea', 'term_linea DIVIDE factor_linea', 'factor_linea')
    def term_linea(self, p):
        if len(p) == 3:
            return self.NodoBinario(p[1], p.term_linea, p.factor_linea)
        else:
            return p.factor_linea
    
    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'asignacion_de_linea', 'TOL "(" expr ")"')
    def factor_linea(self, p):
        if len(p) == 1:
            return p[0]
        else:
            return self.NodoBinario('TOL', p.expr)

    @_('asignable ASSIGN IDEN', 'asignable ASSIGN constante')
    def asignacion_de_linea(self, p):
        return self.NodoBinario('=', p.asignable, p[2])

    @_('parametros "," expr', 'expr')
    def parametros(self, p):
        return p

    @_('seleccion', 'iteracion')
    def control(self, p):
        return p

    @_('expr_linea GT expr_linea', 'expr_linea LT expr_linea',
       'expr_linea GE expr_linea', 'expr_linea LE expr_linea',
       'expr_linea NE expr_linea', 'expr_linea EQ expr_linea')
    def condicion(self, p):
        return p

    @_('IF "(" condicion ")" cuerpo_control END_IF ";"',
       'IF "(" condicion ")" cuerpo_control ELSE cuerpo_control END_IF ";"')
    def seleccion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de seleccion")
        return p

    @_('FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT cuerpo_control')
    def iteracion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de iteracion")
        return p
    
    @_('cuerpo_ejecutable', 'ejecutable')
    def cuerpo_control(self, p):
        return p

    def error(self, p):
        pass

    #----------------------------ERRORES---------------------------------------------

    @_('programa : program_in error ";"')
    def programa_error_declaracion(self, p):
        print(f"Error fatal en declaraciones")
        self._logger.error(f"Linea {p.lineno} | Error fatal en declaraciones")
        return ("error",)

    @_('programa : declaraciones cuerpo_ejecutable', 'programa : cuerpo_ejecutable')
    def programa_error_nombre(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta nombre de programa")
        if not hasattr(p, 'declaraciones'): print("Falta declaracion")
        return ("error",)

    @_('declaracion : error ";"', 'declaracion_func : error ";"', 'declaracion_clase : error ";"')
    def declaracion_error(self, p):
        self._logger.error(f"Linea {p.lineno} | Error de declaracion")
        return ("error",)

    @_('declaracion : dec_var error ";"', 'declaracion_func : dec_var error ";"', 'declaracion_clase : dec_var error ";"')
    def declaracion_error_lista_var(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de ',' o ';' en declaracion")
        return ("error",)

    @_('declaracion_clase : tipo IDEN "(" error ";"')
    def declaracion_error_parametros(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de parametros formales")
        return ("error",)

    @_('declaracion : tipo FUNCTION error ";"', 'declaracion_func : tipo FUNCTION error ";"')
    def declaracion_error_function_name(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de nombre de funcion")
        return ("error",)

    @_('declaracion : ambito_func "(" error ";"', 'declaracion_func : ambito_func "(" error ";"')
    def declaracion_error_function_paramf(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de nombre o tipo de parametro formal")
        return ("error",)

    @_('declaracion : CLASS IDEN error BEGIN declaraciones_clase END ";"')
    def clase_error_codigo(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de codigo en declaracion de clase")
        return ("error",)

    @_('declaracion : ambito_clase BEGIN declaraciones_clase EXTENDS error ";" END ";"')
    def clase_error_extends(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de identificadores luego del 'extends'")
        return ("error",)

    @_('declaracion : TYPEDEF IDEN ASSIGN "[" error "]" ";"')
    def tipoUsuario_error(self, p):
        self._logger.error(f"Linea {p.lineno} | Asencia de valores para la enumeración")
        return ("error",)

    @_('ejecutable : error ";"', 'ejecutable : error END')
    def ejecutable_error(self, p):
        self._logger.error(f"Linea {p.lineno} | Error ejecutable")
        return ("error",)

    @_('ejecutable : POUT "(" ")" ";"')
    def ejecutable_error_pout(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de argumento en sentencia 'pout'")
        return ("error",)

    @_('ejecutable : IF error ";"', 'ejecutable : IF "(" condicion error ";"')
    def ejecutable_error_if(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de parentesis de cierre o apertura en linea")
        return ("error",)

    @_('ejecutable : IF "(" condicion ")" cuerpo_control error ";"')
    def ejecutable_error_if_endIF(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de 'end_if'")
        return ("error",)

    @_('expr : expr PLUS error', 'expr : expr MINUS error',
       'expr_linea : expr_linea PLUS error', 'expr_linea : expr_linea MINUS error')
    def expr_error(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de operando derecho en linea")
        return ("error",)

    @_('term : term TIMES error', 'term : term DIVIDE error', 'term : TIMES factor', 'term : DIVIDE factor', 'term : TIMES error', 'term : DIVIDE error',
       'term_linea : term_linea TIMES error', 'term_linea : term_linea DIVIDE error', 'term_linea : TIMES factor_linea', 'term_linea : DIVIDE factor_linea', 'term_linea : TIMES error', 'term_linea : DIVIDE error')
    def term_error(self, p):
        self._logger.error(f"Linea {p.lineno} | Falta de operando")
        return ("error",)

    @_('asignacion_de_linea : asignable ASSIGN2P IDEN',
       'asignacion_de_linea : asignable ASSIGN2P constante')
    def asignacion_de_linea_error(self, p):
        self._logger.error(f"Linea {p.lineno} | Uso del símbolo de asignación normal ':=' donde debe usarse '='")
        return ("error",)

    @_('ejecutable : FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT error',
       'ejecutable : FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT BEGIN END ";"')
    def iteracion_error_cuerpo(self, p):
        print(f"Error o falta de cuerpo de control en iteracion en linea {p.lineno}")
        self._logger.error(f"Linea {p.lineno} | Falta de cuerpo de control en iteracion en linea")
        return ("error",)