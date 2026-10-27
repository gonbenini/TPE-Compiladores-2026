from hmac import new
from turtle import pos

from sly import Parser
from zmq import has
from lexer import TpLexer

class TpParser(Parser):

    def __init__(self, TS, _info, _logger):
        # Inyectamos dependencias
        self.TS = TS
        self._InfoLogger = _info
        self._logger = _logger
        self.ambito = 'main'
        self.arboles={}

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    precedence = (
        ('right', 'error'),
        ('right', 'END', ';'),
    )

    #la idea es con este manejar todas aquellas operaciones que tengan un solo hijo, tales como
    #retornos, impresiones, conversiones, etc. La idea de que tenga es tipo es simplemente por ir
    #representando los tipos a lo largo del arbol
    class NodoUnario:
        def __init__(self, op, son=None, type=None):
            self.op = op
            self.son = son if son else 'NIL'
            self.type = type

    #la idea con este es manejar todas aquellas operaciones binarias. La idea del tipo es ir
    #representando los tipos de diferentes operaciones.
    class NodoBinario:
        def __init__(self, op, left='NIL', right=None, type=None):
            self.op = op
            self.left = left
            self.right = right if right else 'NIL'
            self.type = type 

        def __str__(self) -> str:
            a = self.left.__str__() if self.left else ''
            return ' '.join([a, self.op, self.right.__str__(), ';'])

    #la idea con este es manejar los operandos individuales por si solo, con la inclusion
    #del tipo para poder ir elevandolo a traves del arbol
    class NodoHoja:
        def __init__(self, tipo, operando) -> None:
            self.type=tipo
            self.operando=operando

        def __str__(self) -> str:
            return str(self.operando)


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
                #print(f"Variable {name + ':main'} encontrada")
                return True, name + ':main'

            else:
                #print(f"Variable {name} no declarada o no alcanzable")
                return False, 'NIL'
            
        elif encontrado:
            #print(f"Variable {search_name} encontrada")
            return True, search_name

        else: 
            #print(f"Variable {name} no declarada o no alcanzable")
            return False, 'NIL'

    def atributo_valido(self, p):
        if (p.asignable.tipo + ':main') in self.TS:
            clase = p.asignable.tipo

        else: return False, 'NIL'

        if self.TS[clase + ':' + 'main']['type'] == 'CLASS':
            if (p.IDEN + ':' + 'main' + ':(' + clase + ')') in self.TS:
                return True, (p.IDEN + ':main' + ':(' + clase + ')')
                #manejar bien los errores de retorno
            else:
                #print('no valido')
                return False, 'NIL'

        else:
            #print('xd')
            return False, 'NIL'

    def renameToken(self, new_name, old_name, type, use):
        self.TS[new_name] = self.TS.pop(old_name)
        self.TS[new_name]['type'] = type
        self.TS[new_name]['uso'] = use

    def check_duplicate(self, new_name, old_name):
        if new_name in self.TS:
            print(f"Error | redeclaracion de {new_name.rsplit(':')[0]} en ambito {self.ambito}")
            self.TS.pop(old_name)
            return False
        else:
            return True

    def check_type(self, type1, type2):
        if type1 == type2:
            return True
        else:
            print(f"Error | Tipos incompatibles entre {type2} y {type1}")
            return False

    def assign_generate(self, params_f, params_r, posic=None):
        raiz = None
        posic = params_r if posic == None else posic
        if len(params_f) == len(params_r) == len(posic):
            if len(params_f) == 1:
                valido = self.check_type(self.TS[params_f[0]]['type'], params_r[0].type)
                if valido:
                    s = self.NodoBinario('=', params_f[0], params_r[0], params_r[0].type)
                else:
                    s = self.NodoBinario('error', 'error', 'error')
                return True, s
            else:
                cadena_asignacion = None  
                for i in range(len(params_f)):
                    valido = self.check_type(self.TS[params_f[i]]['type'], params_r[i].type)
                    if valido:
                        nodo_asignacion = self.NodoBinario('=', params_f[i], params_r[i], params_r[i].type)
                        nodo_cadena = self.NodoBinario('asign.', 'None', nodo_asignacion)
                        if not cadena_asignacion:
                            cadena_asignacion = nodo_cadena
                            raiz = nodo_cadena
                        else:
                            cadena_asignacion.left = nodo_asignacion
                            cadena_asignacion = nodo_asignacion
                    else:
                        nodo_asignacion = self.NodoBinario('error', 'error', 'error')

                return True, raiz
        return False, None
    #----------------------------ESTRUCTURA PRINCIPAL---------------------------------------------

    @_('programa')
    def programa_I(self, p):
        return p

    @_('program_in declaraciones cuerpo_ejecutable')
    def programa(self, p):
        self.imprimir_arbol(p.cuerpo_ejecutable)
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
        # if new_name in self.TS:
        #     print(f"Error | redeclaracion de {p.ambito_metodo['name']}")
        #     self.TS.pop(p.ambito_metodo['name'])
        #     return
        if not self.check_duplicate(new_name, p.ambito_metodo['name']): return

        self.arboles[new_name] = {'nodo': p.cuerpo_ejecutable} #guardamos arbol sintactico de la funcion
        self.renameToken(new_name, p.ambito_metodo['name'], p.ambito_metodo['tipo'], 'Nombre de metodo')
            # self.TS[new_name] = self.TS.pop(p.ambito_metodo['name'])
            # self.TS[new_name]['type'] = p.ambito_metodo['tipo']
            # self.TS[new_name]['uso'] = 'Nombre de metodo'
        self.TS[new_name]['parametros'] = p.parametros_f
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
        # se debe chequear que el tipo es valido
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de variable/s")
        for i in p.id_vars:
            new_name = i + ':' + self.ambito
            if not self.check_duplicate(new_name, i): return
            self.renameToken(new_name, i, p.tipo, 'Nombre de variable')
                # self.TS[new_name] = self.TS.pop(i)
                # self.TS[new_name]['type'] = p.tipo
                # self.TS[new_name]['uso'] = 'Nombre de variable'
        return p

    @_('SINGLEF', 'LONGINT', 'IDEN')
    def tipo(self, p):
        if p[0] not in ('singlef', 'longint'):
            valido, _ = self.alcance(p[0])
            #print(valido)
            if not valido:
                print("Error | Tipo fuera de alcance")
                return "error"
        return p[0]

    @_('id_vars "," IDEN', 'IDEN')
    def id_vars(self, p):
        if len(p) == 1:
            return [p.IDEN]
        else:
            p.id_vars.append(p.IDEN)
            return p.id_vars

    @_('parametros_f "," parametro_f', 'parametro_f')
    #capaz deberia devolver un nodo hoja por parametro formal?
    def parametros_f(self, p):
        if len(p) == 1:
            return [p.parametro_f]
        else:
            p.parametros_f.append(p.parametro_f)
            return p.parametros_f

    @_('tipo IDEN')
    def parametro_f(self, p):
        #ver como asociarla cada parametro_f con su funcion
        # para luego poder hacer las asignaciones de parametros reales
        # a formales

        #deberiamos chequear que no haya redeclaracion tambien
        new_name = p.IDEN + ':' + self.ambito
        if not self.check_duplicate(new_name, p.IDEN): return
        self.renameToken(new_name, p.IDEN, p.tipo, 'Nombre de variable')
            # self.TS[new_name] = self.TS.pop(p.IDEN)
            # self.TS[new_name]['type'] = p.tipo
            # self.TS[new_name]['uso'] = 'Nombre de variable'
        return new_name

    @_('ambito_func "(" parametros_f ")" declaraciones_func cuerpo_ejecutable',
       'ambito_func "(" parametros_f ")" cuerpo_ejecutable')
    def funcion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de funcion")
        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        new_name = p.ambito_func['name'] + ':' + self.ambito

        if not self.check_duplicate(new_name, p.ambito_func['name']): return

        self.arboles[new_name] = {'nodo': p.cuerpo_ejecutable} #guardamos arbol sintactico de la funcion
        self.renameToken(new_name, p.ambito_func['name'], p.ambito_func['tipo'], 'Nombre de funcion')
            # self.TS[new_name] = self.TS.pop(p.ambito_func['name'])
            # self.TS[new_name]['type'] = p.ambito_func['tipo']
            # self.TS[new_name]['uso'] = 'Nombre de funcion'
        self.TS[new_name]['parametros'] = p.parametros_f
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

        if not self.check_duplicate(new_name, p.ambito_clase): return

        self.renameToken(new_name, p.ambito_clase, 'CLASS', 'Nombre de clase')
            # self.TS[new_name] = self.TS.pop(p.ambito_clase)
            # self.TS[new_name]['type'] = 'CLASS'
            # self.TS[new_name]['uso'] = 'Nombre de clase'
        return p

    @_('CLASS IDEN IDEN')
    def ambito_clase(self, p):
        self.ambito = self.ambito + ':' + '(' + p[1] + ')'
        return p.IDEN0

    @_('TYPEDEF IDEN ASSIGN "[" constantes "]" ";"')
    def tipoUsuario(self, p):
        #acomodar lo de uso y renombar tambien
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de tipo usuario")
        new_name = p.IDEN + ':main'
        # if new_name in self.TS:
        #     print(f"Error | redeclaracion de {new_name}")
        #     self.TS.pop(p.ambito_metodo['name'])
        #     return
        if not self.check_duplicate(new_name, p.IDEN): return

        self.renameToken(new_name, p.IDEN, 'Tipo usuario','Nombre de tipo')
            # self.TS[new_name] = self.TS.pop(p.IDEN)
            # self.TS[new_name]['type'] = 'Tipo usuario'
            # self.TS[new_name]['uso'] = 'Nombre de tipo'
        return p

    @_('constantes "," constante', 'constante')
    def constantes(self, p):
        return p

    @_('CONSTANTE_E', 'CONSTANTE_F', 'MINUS CONSTANTE_E', 'MINUS CONSTANTE_F')
    def constante(self, p):
        if len(p) == 2:
            key = p[1]

            if hasattr(p, 'CONSTANTE_E'):
                tipo_dato = 'longint'  # (O el string exacto que uses en tu TS)
            else:
                tipo_dato = 'singlef'

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

            #return p[1]
            return self.NodoHoja(tipo_dato, p[1])

        #return p[0]
        return self.NodoHoja(self.TS[p[0]]['type'], p[0])

    #----------------------------EJECUTABLES---------------------------------------------
    @_('ejecutables ejecutable', 'ejecutable')
    def ejecutables(self, p):
        if len(p) == 1:
            return p.ejecutable
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
        valido, path = self.atributo_valido(p)
        #print(path)

        if not valido:
            print(f'Error | {p.asignable.operando} no posee un metodo {p.IDEN}')
            return self.NodoUnario('error', 'error')
        else:
            return self.NodoUnario('CALL ' + call_name, self.arboles[path]['nodo'], self.TS[path]['type'])

    @_('IDEN "(" parametros ")" "[" posicionales "]"', 'IDEN "(" parametros ")"')
    def invocacion_funcion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Invocacion a funcion")
        valido, path = self.alcance(p.IDEN)
        if not valido:
            print(f"Error | funcion {p.IDEN} no declarada o no alcanzable")
            return self.NodoUnario('CALL', 'error')
        else:
            params = self.TS[path]['parametros']
            posic = p.posicionales if hasattr(p, 'posicionales') else p.parametros
            raiz = None
            parametros_reales = p.parametros
            if len(p) == 7:
                ord = {}
                for i in range(len(p.posicionales)):
                    ord[p.posicionales[i]] = parametros_reales[i]
                keys = [key for key in ord]
                keys.sort()
                parametros_reales = [ord[k] for k in keys]

            valido, raiz = self.assign_generate(params, parametros_reales, posic)
            if valido:
                return self.NodoBinario('CALL ' + p[0], raiz , self.arboles[path]['nodo'], self.TS[path]['type'])

            print("ERROR | La cantidad de parametros reales o posicionales no coincide con los parametros formales")
            return self.NodoUnario('error', 'error', 'error')

    @_('posicionales "," CONSTANTE_E', 'CONSTANTE_E')
    def posicionales(self, p):
        #ver como devolver para que lo use la funcion
        if len(p) == 1:
            return [p.CONSTANTE_E]
        else:
            p.posicionales.append(p.CONSTANTE_E)
            return p.posicionales

    @_('asignable ASSIGN expr ";"')
    def asignacion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de asignacion")
        valido = self.check_type(p.asignable.type, p.expr.type)
        if valido:
            return self.NodoBinario('=', p.asignable.operando, p.expr, p.asignable.type)

        return self.NodoBinario('error', 'error', 'error')

    @_('asignable ASSIGN2P expr_linea ";"')
    def asignacion_linea(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia asignacion de linea")
        return self.NodoBinario(':=', p.asignable.operando, p.expr_linea)

    @_('asignable "." IDEN', 'IDEN') #asingable.IDEN -> asignable.IDEN.IDEN
    #la idea seria desde aca controlar que todas las vars esten al alcance y ademas
    #para atributos de clases chequear que justamente esa clase contenga esos atributos
    def asignable(self, p):
        if len(p) == 3:
            valido, path = self.atributo_valido(p)
            if not valido:
                print(f'Error | {p.asignable.operando} no posee un atributo {p.IDEN}')
                return self.NodoHoja('error', 'error')
            else:
                return self.NodoHoja(self.TS[path]['type'], p.asignable.operando + '.' + p.IDEN)

        else:
            valido, path = self.alcance(p.IDEN)
            if not valido:
                print(f"Error | variable {p.IDEN} no declarada o no alcanzable")
                return self.NodoHoja('error', 'error')
            else:
                return self.NodoHoja(self.TS[path]['type'], p.IDEN)

    @_('expr PLUS term', 'expr MINUS term', 'term')
    def expr(self, p):
        if len(p) == 3:
            valido = self.check_type(p.expr.type, p.term.type)
            if valido:
                return self.NodoBinario(p[1], p.expr, p.term, p.expr.type)
            
            return self.NodoBinario('error', 'error', 'error')
        else:
            return p.term

    @_('term TIMES factor', 'term DIVIDE factor', 'factor')
    def term(self, p):
        if len(p) == 3:
            valido = self.check_type(p.term.type, p.factor.type)
            if valido:
                return self.NodoBinario(p[1], p.term, p.factor, p.term.type)
            
            return self.NodoBinario('error', 'error', 'error')
        else:
            return p.factor

    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'TOL "(" expr ")"')
    def factor(self, p):
        if len(p) == 1:
            return p[0]
        else:
            return self.NodoUnario('TOL', p.expr, 'longint')

    @_('expr_linea PLUS term_linea', 'expr_linea MINUS term_linea', 'term_linea')
    def expr_linea(self, p):
        if len(p) == 3:
            valido = self.check_type(p.expr_linea.type, p.term_linea.type)
            if valido:
                return self.NodoBinario(p[1], p.expr_linea, p.term_linea, p.expr_linea.type)
                    
            return self.NodoBinario('error', 'error', 'error')
        else:
            return p.term_linea
    
    @_('term_linea TIMES factor_linea', 'term_linea DIVIDE factor_linea', 'factor_linea')
    def term_linea(self, p):
        if len(p) == 3:
            valido = self.check_type(p.term_linea.type, p.factor_linea.type)
            if valido:
                return self.NodoBinario(p[1], p.term_linea, p.factor_linea, p.term_linea.type)
            
            return self.NodoBinario('error', 'error', 'error')
        else:
            return p.factor_linea
    
    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'asignacion_de_linea', 'TOL "(" expr ")"')
    def factor_linea(self, p):
        if len(p) == 1:
            return p[0]
        else:
            return self.NodoUnario('TOL', p.expr, 'longint')

    @_('asignable ASSIGN IDEN', 'asignable ASSIGN constante')
    def asignacion_de_linea(self, p):
        return self.NodoBinario('=', p.asignable, p[2])

    @_('parametros "," expr', 'expr')
    def parametros(self, p):
        if len(p) == 1:
            return [p.expr]
        else:
            p.parametros.append(p.expr)
            return p.parametros

    @_('seleccion', 'iteracion')
    def control(self, p):
        return p[0]

    @_('expr_linea GT expr_linea', 'expr_linea LT expr_linea',
       'expr_linea GE expr_linea', 'expr_linea LE expr_linea',
       'expr_linea NE expr_linea', 'expr_linea EQ expr_linea')
    def condicion(self, p):
        return self.NodoBinario(p[1], p[0], p[2])

    @_('IF "(" condicion ")" cuerpo_control END_IF ";"',
       'IF "(" condicion ")" cuerpo_control ELSE cuerpo_control END_IF ";"')
    def seleccion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de seleccion")
        condicion = self.NodoUnario('COND', p.condicion)
        if not hasattr(p, 'ELSE'):
            cuerpo_then = self.NodoUnario('THEN', p.cuerpo_control)
            cuerpo = self.NodoUnario('CUERPO', cuerpo_then)
            return self.NodoBinario('IF', condicion, cuerpo)
        else:
            cuerpo_then = self.NodoUnario('THEN', p.cuerpo_control0)
            cuerpo_else = self.NodoUnario('ELSE', p.cuerpo_control1)
            cuerpo = self.NodoBinario('CUERPO', cuerpo_then, cuerpo_else)
            return self.NodoBinario('IF', condicion, cuerpo)

    @_('FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT cuerpo_control')
    def iteracion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de iteracion")
        
        #IDEN, constante0 -> IDEN = constante0
        inicializacion = self.NodoBinario(":=", p.IDEN, p.constante0)

        #condicion -> IDEN <= constante1
        condicion = self.NodoBinario("<=", p.IDEN, p.constante1)
        condicion = self.NodoUnario("COND", condicion)

        #constante2 -> constante0 += constante2
        sum = self.NodoBinario("+", p.IDEN, p.constante2)
        incremento = self.NodoBinario("=", p.IDEN, sum)

        cuerpo_for = self.NodoBinario("CUERPO", p.cuerpo_control, incremento)
        
        composicion_while = self.NodoBinario("COMPWHILE", condicion, cuerpo_for)

        arbol_for = self.NodoBinario("FOR", inicializacion, composicion_while)

        return arbol_for
    
    @_('cuerpo_ejecutable', 'ejecutable')
    def cuerpo_control(self, p):
        return p[0]

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