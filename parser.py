from math import e
import numbers
from abc import ABC, abstractmethod
from sly import Parser
from zmq import TYPE
from lexer import TpLexer

'''
Estas 3 clases nos sirven para abstraer el comportamiento entre parametros formales, reales y atributos con la unica intencion de usar el mismo metodo para generar la asignacion de parametros formales a reales y de atributos
con la unica intencion de poder utilizar las mismas funciones.
'''
class Lista(ABC):

    def __init__(self, lista):
        self.items = lista

    def get(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

    @abstractmethod
    def get_type(self, i):
        pass
class Atributo(Lista):
    def __init__(self, lista, TS):
        super().__init__(lista)
        self.TS = TS

    def get_type(self, i):
        return self.TS[self.items[i]]['type']
    
class ParamR(Lista):

    def get_type(self, i):
        return self.items[i].type
class ParamF(Lista): #parametros formales

    def __init__(self, lista, TS):
        super().__init__(lista)
        self.TS = TS

    def get_type(self, i):
        return self.TS[self.items[i]]['type']
class TpParser(Parser):

    def __init__(self, TS, AS, _info, _logger, arboles):
        # Inyectamos dependencias
        self.TS = TS
        self.AS = AS
        self._InfoLogger = _info
        self._logger = _logger
        self.ambito = 'main'
        self.arboles=arboles
        self.ret = False
        self.type_func = []
        self.decClass = False

    debugfile = 'parser.out'
    tokens = TpLexer.tokens

    precedence = (
        ('right', 'error'),
        ('right', 'END', ';'),
    )
        
    #la idea es con este manejar todas aquellas operaciones que tengan un solo hijo, tales como
    #retornos, impresiones, conversiones, etc. La idea de que tenga un tipo es simplemente por ir
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
            self.op = operando

        def __str__(self) -> str:
            return str(self.op)


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

    '''
        Esta funcion la utilizamos durante todo el trabajo para poder verificar si una variable, funcion
        o metodo esta declarada y es alcanzable desde el ambito actual. Nos devuelve un booleano
        y el path de la variable, funcion o metodo en caso de que este declarada y sea alcanzable.
        Se basa en recorrer los distintos ambitos desde el mas especifico al mas general, hasta llegar a main. En caso de no encontrarla
    '''
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

    '''
        Esta funcion la utilizamos para poder verificar si un atributo o metodo es valido para un objeto
        de una clase. Nos devuelve un booleano y el path del atributo o metodo en caso de que este declarado
        y sea alcanzable. Nos permite detectar atributos, metodos e incluso desambiguado de clases.
    '''
    def atributo_valido(self, p):
        if (p.asignable.type + ':main') in self.TS:
            clase = p.asignable.type

        else: return False, 'NIL'

        if self.TS[clase + ':' + 'main']['type'] == 'CLASS':
            metodo = (p.IDEN + ':' + 'main' + ':(' + clase + ')')
            print(p.asignable.op)
            atributo = next(
                (var for var in self.TS[p.asignable.op]['vars'].items
                if var.startswith(p.IDEN + ':')),
                None
            )
            clase_heredada = (p.IDEN + ':extend:(' + p.asignable.op.split(':')[0] + ':' + p.asignable.type + ':' + self.ambito + ')')
            
            if ':extend:(' in (p.asignable.op): #cambiar cambiar cambiar
                atributo_heredado = (p.IDEN + ':' + self.ambito + ':(' + p.asignable.op.split('(')[1].split(':')[0] + '.extend:' + p.asignable.type + ')')
            else:
                atributo_heredado = None

            if metodo in self.TS: # buscar metodo
                return True, metodo
            elif atributo is not None:
                return True, atributo
            elif atributo_heredado in self.TS: # buscar atributos heredados
                return True, atributo_heredado
            elif clase_heredada in self.TS:
                return True, clase_heredada     
            else:
                return False, 'NIL'
        
        else:
            return False, 'NIL'

    '''
        Esta funcion nos permite renombrar un token en la tabla de simbolos, cambiando su nombre
        y actualizando su tipo y uso siendo útil para manejar ambitos y evitar conflictos de nombres.
    '''
    def renameToken(self, new_name, old_name, type, use):
        self.TS[new_name] = self.TS.pop(old_name, {})
        self.TS[new_name]['type'] = type
        self.TS[new_name]['uso'] = use

    '''
        Esta funcion nos permite verificar si un nombre ya existe en la tabla de simbolos en el ambito
        especifico. Si ese es el caso, lo quitamos por completo.
    '''
    def check_duplicate(self, new_name, old_name=None):
        if new_name in self.TS:
            print(f"Error | redeclaracion de {new_name.rsplit(':')[0]} en ambito {self.ambito}")
            if old_name and old_name in self.TS:
                self.TS.pop(old_name)
            return False
        else:
            return True

    '''
        Esta funcion nos permite verificar si dos tipos son compatibles entre sí, devolviendo un booleano.
        Abarcamos el chequeo de tipos de usuario con constantes, chequeo de igual codigo de clases y
        chequeo de tipos simples. En caso de que no sean compatibles, se imprime un mensaje de error.
    '''
    def check_type(self, type1, type2, value=None, p=True):
        if value and isinstance(value.op, numbers.Number):

            if f"{type1}:main" in self.TS and 'valores' in self.TS[f"{type1}:main"]:
                values = self.TS[f"{type1}:main"]['valores']

            else:
                values = None
            if values:
                for i in values:
                    if i.type == value.type and i.op == value.op:
                        return True, 'type'
                print(f"Error | Valor {value} no pertenece al tipo {type1}")
                return False, 'nil'

        key1 = f"{type1}:main"
        key2 = f"{type2}:main"
        if key1 in self.TS and key2 in self.TS:
            class1 = self.TS[key1]['type'] == 'CLASS'
            class2 = self.TS[key2]['type'] == 'CLASS'
            if class1 and class2:
                if self.TS[key1]['code'] == self.TS[key2]['code']:
                    return True, 'class'
        
        if type1 == type2:
            return True, 'equal'
        else:
            if p:
                print(f"Error | Tipos incompatibles entre {type2} y {type1}")
            return False, 'nil'

    '''
        Esta funcion nos permite generar un arbol de asignaciones entre parametros formales y reales,
        o entre atributos y valores. Devuelve un booleano indicando si la asignacion es valida
        y el nodo raiz del arbol de asignaciones para poder acoplar como ejecutable.
    '''
    def assign_generate(self, asignables, asignados, check=False, posic=None):
        raiz = None
        posic = asignados if posic == None else posic
        if len(asignables) == len(asignados) == len(posic):
            if len(asignables) == 1:
                valido, op = self.check_type(asignables.get_type(0), asignados.get_type(0), asignados.get(0))
                if valido:
                    if op == 'class':
                        _, raiz = self.assign_generate(self.TS[asignables.get(0)]['vars'], self.TS[asignados.get(0).op]['vars'], True)
                        s =  self.NodoUnario('TRANSFER_OBJECT', raiz, asignables.get_type(0))
                    else:
                        asignable = self.NodoHoja(asignables.get_type(0), asignables.get(0))
                        asignado = self.NodoHoja(asignados.get_type(0), asignados.get(0))
                        s = self.NodoBinario('=', asignable, asignado, asignados.get_type(0))
                else:
                    s = self.NodoBinario('error', 'error', 'error', 'error')
                return True, s
            else:
                def generate(i, len):
                    valid1, op = self.check_type(asignables.get_type(i), asignados.get_type(i), asignados.get(i))
                    asignable1 = self.NodoHoja(asignables.get_type(i), asignables.get(i))
                    asignado1 = self.NodoHoja(asignados.get_type(i), asignados.get(i))
                    if not valid1:
                        assign1 = self.NodoBinario('error', 'error', 'error', 'error')
                    else:
                        if op == 'class':
                            _, raiz = self.assign_generate(self.TS[asignables.get(i)]['vars'], self.TS[asignados.get(i).op]['vars'], True)
                            assign1 = self.NodoUnario('TRANSFER_OBJECT', raiz, asignables.get_type(i))
                        else:
                            assign1 = self.NodoBinario('=', asignable1, asignado1, asignados.get_type(i))
                    if i == len - 2:
                        valid2, op = self.check_type(asignables.get_type(i + 1), asignados.get_type(i + 1), asignados.get(i + 1))
                        asignable2 = self.NodoHoja(asignables.get_type(i + 1), asignables.get(i + 1))
                        asignado2 = self.NodoHoja(asignados.get_type(i + 1), asignados.get(i + 1))
                        if not valid2:
                            assign2 = self.NodoBinario('error', 'error', 'error', 'error')
                        else:
                            if op == 'class':
                                _, raiz = self.assign_generate(self.TS[asignables.get(i + 1)]['vars'], self.TS[asignados.get(i + 1).op]['vars'], True)
                                assign2 = self.NodoUnario('TRANSFER_OBJECT', raiz, asignables.get_type(i + 1))
                            else:
                                assign2 = self.NodoBinario('=', asignable2, asignado2, asignados.get_type(i + 1))

                        return self.NodoBinario('S', assign1, assign2)

                    else:
                        return self.NodoBinario('S', generate(i + 1, len), assign1)
                raiz = generate(0, len(asignables))
                return True, raiz
            
        return False, None

    '''
        Esta funcion nos permite verificar si una funcion o metodo tiene un retorno.
        En caso de que no lo tenga, insertamos un retorno por defecto.
    '''
    def check_ret(self, new_name, type, nodo):
        if self.ret:
            self.ret = False
        else:
            op = 0 if type == 'longint' else 0.0
            hoja = self.NodoHoja(type, op)
            self.arboles[new_name]['nodo'] = self.NodoBinario('S', self.arboles[new_name]['nodo'], self.NodoUnario('RET', hoja, hoja.type))
    
    #----------------------------ESTRUCTURA PRINCIPAL---------------------------------------------

    @_('programa')
    def programa_I(self, p):
        return p.programa

    @_('program_in declaraciones cuerpo_ejecutable')
    def programa(self, p):
        self.imprimir_arbol(p.cuerpo_ejecutable)
        return p.cuerpo_ejecutable

    @_('PROGRAM IDEN')
    def program_in(self, p):
        self.TS[p.IDEN]['uso'] = 'Nombre de programa'
        return p

    #----------------------------DECLARACIONES---------------------------------------------

    @_('declaracion', 'declaraciones declaracion')
    def declaraciones(self, p):
        return p

    #obtenemos las declaraciones de atributos para poder almacenar.
    @_('declaraciones_clase declaracion_clase', 'declaracion_clase')
    def declaraciones_clase(self, p):
        if len(p) == 1:
            return p.declaracion_clase
        else:
            p.declaraciones_clase.extend(p.declaracion_clase)
            #se rompe si falta ; en la declaracion de una variable.
            return p.declaraciones_clase

    @_('declaraciones_func declaracion_func', 'declaracion_func')
    def declaraciones_func(self, p):
        return p

    @_('dec_var ";"', 'funcion')
    def declaracion_func(self, p):
        return p
    
    @_('dec_var ";"', 'metodo')
    def declaracion_clase(self, p):
        if not p[0]:
            return []
        return p[0]

    '''
        tratamos la declaracion de metodos, verificando renombramiento, retornos y guardando tanto
        los parametros formales como el arbol sintactico de la funcion para poder ser llamado posteriormente.
    '''
    @_('ambito_metodo parametros_f ")" cuerpo_ejecutable')
    def metodo(self, p):

        if p.ambito_metodo['tipo'] not in ('singlef', 'longint'):
            print(f"ERROR | Tipo de dato no valido para metodos")
            return []

        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de metodo")
        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        new_name = p.ambito_metodo['name'] + ':' + self.ambito

        if not self.check_duplicate(new_name, p.ambito_metodo['name']): return

        self.arboles[new_name] = {'nodo': p.cuerpo_ejecutable} #guardamos arbol sintactico de la funcion
        self.renameToken(new_name, p.ambito_metodo['name'], p.ambito_metodo['tipo'], 'Nombre de metodo')

        self.check_ret(new_name, p.ambito_metodo['tipo'], p.cuerpo_ejecutable)
        self.TS[new_name]['parametros'] = p.parametros_f
        self.type_func.pop()
        return []

    #tratos el inyectado de ambito antes de entrar a las declaraciones
    @_('tipo IDEN "("')
    def ambito_metodo(self, p):
        self.ambito = self.ambito + ':' + p.IDEN
        self.type_func.append(p.tipo)
        return {'tipo': p.tipo, 'name': p.IDEN}

    @_('BEGIN ejecutables END ";"')
    def cuerpo_ejecutable(self, p):
        return p.ejecutables
    
    @_('dec_var ";"', 'clase', 'funcion', 'tipoUsuario')
    def declaracion(self, p):
        return p

    def acomodar(self, name_var, tipo, name_single):
        _, path = self.alcance(tipo)
        if path != 'NIL' and 'type' in self.TS[path] and self.TS[path]['type'] == 'CLASS':
            self.TS[name_var]['vars'] = Atributo([], self.TS)
            vars = self.TS[path]['vars']
            for j in vars.items:
                name = (j['name'] + ':' + self.ambito + ':(' + name_single + ':' + tipo + ')')

                if not self.check_duplicate(name): break

                self.TS[name] = {'type': j['type'], 'uso': 'Nombre de variable'}

                self.TS[name_var]['vars'].items.append(name)

                if (j['type'] + ':main' in self.TS and self.TS[j['type'] + ':main']['type'] == 'CLASS'):
                    self.acomodar(name, j['type'], name_single + '.' + j['name'])

            if 'extend' in self.TS[path]:
                for j in self.TS[path]['extend']:
                    nombre_extend = (f'{j}:extend:({name_single}:{tipo}:{self.ambito})')
                    self.TS[nombre_extend] = {'type': j, 'uso': 'Nombre de variable'}
                    self.acomodar(nombre_extend, j, name_single + '.extend')     

    '''
        Esta funcion nos permite manejar la declaracion de variables y siendo util
        para manejar la declaracion de atributos de variables tipo objeto siendo recursivo
        su declaracion, es decir, si declaramos una variable de tipo objeto, se van a declarar
        todos los atributos de ese objeto.
    '''
    @_('tipo id_vars')
    def dec_var(self, p):
        # se debe chequear que el tipo es valido
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de variable/s")
        for i in p.id_vars:
            new_name = i + ':' + self.ambito
            if not self.check_duplicate(new_name, i) or self.decClass: continue
            self.renameToken(new_name, i, p.tipo, 'Nombre de variable')

            self.acomodar(new_name, p.tipo, i)

        vars = []
        for i in p.id_vars:
            vars.append({'name': i, 'type': p.tipo})

        return vars

    #Controlamos que el tipo este al alcance.
    @_('LONGINT', 'SINGLEF', 'IDEN')
    def tipo(self, p):
        if p[0] not in ('singlef', 'longint'):
            valido, path = self.alcance(p[0])
            if not valido:
                print("Error | Tipo fuera de alcance")
                return "error"
            elif ('type' in self.TS[path] and self.TS[path]['type'] not in ('CLASS', 'Tipo usuario', 'longint', 'singlef')) or ('type' not in self.TS[path]):
                print("Error | Tipo no valido")
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
            if p.parametro_f != "error":
                p.parametros_f.append(p.parametro_f)
            return p.parametros_f

    #declaramos los parametros formales en la tabla de simbolos.
    @_('tipo IDEN')
    def parametro_f(self, p):
        new_name = p.IDEN + ':' + self.ambito
        if not self.check_duplicate(new_name, p.IDEN): return "error"
        self.renameToken(new_name, p.IDEN, p.tipo, 'Nombre de variable')
        self.acomodar(new_name, p.tipo, p.IDEN)
        return new_name

    '''
        Esta funcion nos permite manejar la declaracion de funciones siendo lo mas importante
        el guardado del arbol sintactico para su posterior invocacion y el almacenamiento de los
        parametros formales en la tabla de simbolos.
    '''
    @_('ambito_func "(" parametros_f ")" declaraciones_func cuerpo_ejecutable',
       'ambito_func "(" parametros_f ")" cuerpo_ejecutable')
    def funcion(self, p):

        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        if p.ambito_func['tipo'] not in ('singlef', 'longint'):
            print(f"ERROR | Tipo de dato no valido para funciones")
            return p

        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de funcion")
        new_name = p.ambito_func['name'] + ':' + self.ambito

        if not self.check_duplicate(new_name, p.ambito_func['name']): return p

        self.arboles[new_name] = {'nodo': p.cuerpo_ejecutable} #guardamos arbol sintactico de la funcion
        self.renameToken(new_name, p.ambito_func['name'], p.ambito_func['tipo'], 'Nombre de funcion')

        self.check_ret(new_name, p.ambito_func['tipo'], p.cuerpo_ejecutable)
        self.TS[new_name]['parametros'] = p.parametros_f
        self.type_func.pop()
        return p

    @_('tipo FUNCTION IDEN')
    def ambito_func(self, p):
        self.ambito = self.ambito + ':' + p[2]
        self.type_func.append(p.tipo)
        return {'tipo': p.tipo, 'name': p.IDEN}

    '''
        Esta funcion nos permite manejar la declaracion de clases siendo lo mas importante
        el almacenamiento de los atributos, extensiones y el tratado de los codigo de clase
        para la similitud estructural.
    '''
    @_('ambito_clase BEGIN declaraciones_clase END ";"', 'ambito_clase BEGIN declaraciones_clase EXTENDS id_vars ";" END ";"')
    def clase(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de clase")
        self.ambito = self.ambito.rsplit(":", 1)[0] #desacoplamos ambito
        new_name = p.ambito_clase['name'] + ':' + self.ambito
        self.decClass = False

        if not self.check_duplicate(new_name, p.ambito_clase['name']): return p

        self.renameToken(new_name, p.ambito_clase['name'], 'CLASS', 'Nombre de clase')

        self.TS[new_name]['vars'] = Atributo(p.declaraciones_clase, self.TS)
        self.TS[new_name]['code'] = p.ambito_clase['code']

        vars = Atributo(p.declaraciones_clase, self.TS)
        if len(p) == 8:
            self.TS[new_name]['extend'] = []
            for i in p.id_vars:
                if p.ambito_clase['name'] == i:
                    print(f"ERROR | Clase '{i}' no puede extenderse a si misma")
                    continue
                valido, path = self.alcance(i)
                if not valido:
                    print(f"ERROR | Clase '{i}' fuera de alcance")
                    continue
                else:
                    if self.TS[path]['type'] != 'CLASS':
                        print(f"ERROR | '{i}' no es una clase")
                        continue
                    self.TS[new_name]['extend'].append(i)
                    #vars.items.extend(self.TS[i + ':main']['vars'].items)

        if p.ambito_clase['valido'] and p.ambito_clase['code'] != "error":
            first_class = self.TS[p.ambito_clase['code'] + ':main']['class']
            vars_code = self.TS[first_class]['vars']
            if len(vars_code) != len(vars):
                print(f"Error | Cantidad de atributos de clase {p.ambito_clase['name']} no coincide con la cantidad de atributos de la clase compatible")
                return p
            err = False
            for i, j in zip(vars_code.items, vars.items):
                valido, _ = self.check_type(i['type'], j['type'])
                if not valido:
                    print(f"Error | Tipo del atributo {j['name']} de clase {p.ambito_clase['name']} no coincide con su par {i['name']} en la clase compatible {first_class.split(':')[0]}")
                    err = True
            if err:
                return p

        return p

    '''
        Con esta funcion controlamos si dicho codigo de clase ya fue declarado
        y registramos el ambito.
    '''
    @_('CLASS IDEN IDEN')
    def ambito_clase(self, p):
        self.decClass = True
        valido, path = self.alcance(p.IDEN1)
        code = p.IDEN1
        if valido and self.TS[path]['uso'] != 'Nombre de codigo':
            print(f"Error | Redeclaracion de codigo de clase {p.IDEN1} en ambito {self.ambito}")
            code = "error"
            valido = False

        self.ambito = self.ambito + ':' + '(' + p[1] + ')'

        if not valido and code != "error":
            self.TS[code + ':' + self.ambito] = {'class': p.IDEN0 + ':' + self.ambito, 'uso': 'Nombre de codigo'}

        return {'name': p.IDEN0, 'valido': valido, 'code': code}

    #Esta funcion nos permite almacenar los valores posibles de un tipo usuario como lo mas importante.
    @_('TYPEDEF IDEN ASSIGN "[" constantes "]" ";"')
    def tipoUsuario(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Declaracion de tipo usuario")
        typei = True if all(isinstance(i.op, int) for i in p.constantes) else False
        typef = True if all(isinstance(i.op, float) for i in p.constantes) else False
        if not (typei or typef):
            print(f"ERROR | Tipos de datos diferentes entre las constantes {p.IDEN}")
            return p

        new_name = p.IDEN + ':main'

        if not self.check_duplicate(new_name, p.IDEN): return

        self.renameToken(new_name, p.IDEN, 'longint' if typei else 'singlef','Nombre de tipo')
        self.TS[new_name]['valores'] = p.constantes
        return p

    @_('constantes "," constante', 'constante')
    def constantes(self, p):
        if len(p) == 1:
            return [p.constante]
        else:
            p.constantes.append(p.constante)
            return p.constantes

    @_('CONSTANTE_E', 'CONSTANTE_F', 'MINUS CONSTANTE_E', 'MINUS CONSTANTE_F')
    def constante(self, p):
        if len(p) == 2:
            key = p[1]

            if hasattr(p, 'CONSTANTE_E'):
                tipo_dato = 'longint'  # (O el string exacto que uses en tu TS)
            else:
                tipo_dato = 'singlef'

            if self.TS[str(key)]['count'] == 1:
                del self.TS[str(key)]

            elif self.TS[str(key)]['count'] > 1:
                self.TS[str(key)]['count'] -= 1

            nueva_key = '-' + str(key)
            if nueva_key in self.TS:
                self.TS[nueva_key]['count'] += 1
            else:
                # Diccionario corregido
                self.TS[nueva_key] = {'type': tipo_dato, 'count': 1}

            #return p[1]
            return self.NodoHoja(tipo_dato, -p[1])

        return self.NodoHoja(self.TS[str(p[0])]['type'], p[0])

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

    #Esta funcion nos permite verificar que el tipo de retorno sea el correcto.
    @_('RET "(" expr ")" ";"')
    def retorno(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia retorno")
        self.ret = True

        if self.type_func and self.type_func[-1] != p.expr.type:
            print(f"ERROR | Se esperaba retornar {self.type_func[-1]} y se recibio {p.expr.type} en linea {p.lineno}")
            self.ret = False
            return self.NodoUnario('error', 'error', 'error')
        return self.NodoUnario('RET', p.expr, p.expr.type)
    
    @_('POUT "(" CADN ")" ";"')
    def pout(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia pout")
        return self.NodoUnario('POUT', p[2])

    '''
        Esta funcion nos permite verificar que la invocacion de un metodo sea valida, es decir,
        que el objeto tenga ese metodo y que los parametros formales y reales coincidan.
    '''
    @_('asignable "." IDEN "(" parametros ")" "[" posicionales "]"', 'asignable "." IDEN "(" parametros ")"')
    def invocacion_metodo(self, p): #invocacion_m . invocacion_f -> invocacion_m . invocacion_f . invocacion_f - > a.b.c.m().m1().m2()
        self._InfoLogger.info(f"Linea {p.lineno} | Invocacion a metodo")
        call_name = p.asignable.op + '.' + p.IDEN
        valido, path = self.atributo_valido(p)

        if not valido:
            print(f'Error | {p.asignable.op} no posee un metodo {p.IDEN}')
            return self.NodoUnario('error', 'error', 'error')
        elif self.TS[path]['uso'] == 'Nombre de metodo':
            params = ParamF(self.TS[path]['parametros'], self.TS)
            raiz = None
            parametros_reales = ParamR(p.parametros)
            if len(p) == 9:
                print('high')
                if len(p.posicionales) != len(p.parametros):
                    print("ERROR | La cantidad de parametros posicionales no coincide con la cantidad de parametros reales")
                    return self.NodoUnario('error', 'error', 'error')
                ord = {}
                for i in range(len(p.posicionales)):
                    ord[p.posicionales[i]] = parametros_reales.get(i)
                keys = [key for key in ord]
                keys.sort()
                parametros_reales.items = [ord[k] for k in keys]
            valido, raiz = self.assign_generate(params, parametros_reales, check=False)
            if valido:
                #return self.NodoBinario('CALL ' + call_name, raiz , self.arboles[path]['nodo'], self.TS[path]['type'])
                return self.NodoUnario('CALL ' + call_name, raiz, self.TS[path]['type'])

            print("ERROR | La cantidad de parametros reales o posicionales no coincide con los parametros formales")
            return self.NodoUnario('error', 'error', 'error')
        print("ERROR | La invocacion no corresponde a un metodo")
        return self.NodoUnario('error', 'error', 'error')

    '''
        Esta funcion nos permite verificar que la invocacion de una funcion sea valida, es decir,
        que la funcion este declarada y que los parametros formales y reales coincidan.
    '''
    @_('IDEN "(" parametros ")" "[" posicionales "]"', 'IDEN "(" parametros ")"')
    def invocacion_funcion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Invocacion a funcion")
        valido, path = self.alcance(p.IDEN)
        if not valido:
            print(f"Error | funcion {p.IDEN} no declarada o no alcanzable")
            return self.NodoUnario('CALL', 'error', 'error')
        elif self.TS[path]['uso'] == 'Nombre de funcion':
            params = ParamF(self.TS[path]['parametros'], self.TS)
            raiz = None
            parametros_reales = ParamR(p.parametros)
            if len(p) == 7:
                if len(p.posicionales) != len(p.parametros):
                    print("ERROR | La cantidad de parametros posicionales no coincide con la cantidad de parametros reales")
                    return self.NodoUnario('error', 'error', 'error')
                ord = {}
                for i in range(len(p.posicionales)):
                    ord[p.posicionales[i]] = parametros_reales.get(i)
                keys = [key for key in ord]
                keys.sort()
                parametros_reales.items = [ord[k] for k in keys]
            valido, raiz = self.assign_generate(params, parametros_reales, check=False)
            if valido:
                return self.NodoUnario('CALL ' + path, raiz, self.TS[path]['type'])
                #return self.NodoBinario('CALL ' + p[0], raiz , self.arboles[path]['nodo'], self.TS[path]['type'])

            print("ERROR | La cantidad de parametros reales o posicionales no coincide con los parametros formales")
            return self.NodoUnario('error', 'error', 'error')

        print("ERROR | La invocacion no corresponde a una funcion")
        return self.NodoUnario('error', 'error', 'error')

    @_('posicionales "," CONSTANTE_E', 'CONSTANTE_E')
    def posicionales(self, p):
        #ver como devolver para que lo use la funcion
        if len(p) == 1:
            return [p.CONSTANTE_E]
        else:
            p.posicionales.append(p.CONSTANTE_E)
            return p.posicionales

    '''
        Con estas dos funciones de asignacion controlamos la compatibilidad de tipos entre
        la variable y el valor a asignar, ademas de controlar la asignacion de objetos entre
        clases compatibles y la generacion del arbol de asignacion.
    '''
    @_('asignable ASSIGN expr ";"')
    def asignacion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de asignacion")
        valido, op = self.check_type(p.asignable.type, p.expr.type, self.NodoHoja(p.expr.type, p.expr.op))
        if valido:
            if op == 'class':
                _, raiz = self.assign_generate(self.TS[p.asignable.op]['vars'], self.TS[p.expr.op]['vars'], True)
                return self.NodoUnario('TRANSFER_OBJECT', raiz, p.asignable.type)

            return self.NodoBinario('=', p.asignable.op, p.expr, p.asignable.type)

        return self.NodoBinario('error', 'error', 'error', 'error')

    @_('asignable ASSIGN2P expr_linea ";"')
    def asignacion_linea(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia asignacion de linea")
        valido, op = self.check_type(p.asignable.type, p.expr_linea.type, self.NodoHoja(p.expr_linea.type, p.expr_linea.op))
        if valido:
            if op == 'class':
                _, raiz = self.assign_generate(self.TS[p.asignable.op]['vars'], self.TS[p.expr_linea.op]['vars'], True)
                return self.NodoUnario('TRANSFER_OBJECT', raiz, p.asignable.type)
            
            return self.NodoBinario(':=', p.asignable.op, p.expr_linea, p.asignable.type)
        
        return self.NodoBinario('error', 'error', 'error', 'error')

    @_('asignable "." IDEN', 'IDEN') #asingable.IDEN -> asignable.IDEN.IDEN
    #la idea seria desde aca controlar que todas las vars esten al alcance y ademas
    #para atributos de clases chequear que justamente esa clase contenga esos atributos
    def asignable(self, p):
        if len(p) == 3:
            valido, path = self.atributo_valido(p)

            if not valido:
                print(f'Error | {p.asignable.op} no posee un atributo {p.IDEN}')
                return self.NodoHoja('error', 'error')
            
            else:
                aux = self.TS[path]
                return self.NodoHoja(aux['type'], path)

        else:
            valido, path = self.alcance(p.IDEN)
            if not valido:
                print(f"ERROR | variable {p.IDEN} no declarada o no alcanzable")
                return self.NodoHoja('error', 'error')
            else:
                if self.TS[path]['uso'] != 'Nombre de variable':
                    print(f"ERROR | {p.IDEN} no es una variable")
                    return self.NodoHoja('error', 'error')
                return self.NodoHoja(self.TS[path]['type'], path)

    @_('expr PLUS term', 'expr MINUS term', 'term')
    def expr(self, p):
        if len(p) == 3:
            path1 = p.expr.type + ':main'
            if path1 in self.TS:
                type1 = self.TS[path1]['type']
                if type1 not in ('longint', 'singlef'):
                    print(f"ERROR | No se pueden operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
            path2 = p.term.type + ':main'
            if path2 in self.TS:
                type2 = self.TS[path2]['type']
                if type2 not in ('longint', 'singlef'):
                    print(f"ERROR | No se pueden operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
            
            valido, _ = self.check_type(p.expr.type, p.term.type)
            if valido:
                return self.NodoBinario(p[1], p.expr, p.term, p.expr.type)
            
            return self.NodoBinario('error', 'error', 'error', 'error')
        else:
            return p.term

    @_('term TIMES factor', 'term DIVIDE factor', 'factor')
    def term(self, p):
        if len(p) == 3:
            path1 = p.factor.type + ':main'
            if path1 in self.TS:
                type1 = self.TS[path1]['type']
                if type1 not in ('longint', 'singlef'):
                    print(f"ERROR | No se pueden operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
            path2 = p.term.type + ':main'
            if path2 in self.TS:
                type2 = self.TS[path2]['type']
                if type2 not in ('longint', 'singlef'):
                    print(f"ERROR | No se pueden operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
            
            valido, _ = self.check_type(p.term.type, p.factor.type)
            if valido:
                return self.NodoBinario(p[1], p.term, p.factor, p.term.type)
            
            return self.NodoBinario('error', 'error', 'error', 'error')
        else:
            return p.factor

    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'TOL "(" expr ")"')
    def factor(self, p):
        if len(p) == 1:
            return p[0]
        else:
            path = p.expr.type + ':main'
            if path in self.TS and self.TS[path]['type'] not in ('longint', 'singlef'):
                print(f"ERROR | No se puede convertir un tipo no numérico a longint")
                return self.NodoUnario('error', 'error', 'error')
            
            return self.NodoUnario('TOL', p.expr, 'longint')

    @_('expr_linea PLUS term_linea', 'expr_linea MINUS term_linea', 'term_linea')
    def expr_linea(self, p):
        if len(p) == 3:
            path1 = p.expr_linea.type + ':main'
            if path1 in self.TS:
                type1 = self.TS[path1]['type']
                if type1 not in ('longint', 'singlef'):
                    print(f"ERROR | No se puede operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
            path2 = p.term_linea.type + ':main'
            if path2 in self.TS:
                type2 = self.TS[path2]['type']
                if type2 not in ('longint', 'singlef'):
                    print(f"ERROR | No se puede operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
                
            valido, _ = self.check_type(p.expr_linea.type, p.term_linea.type)
            if valido:
                return self.NodoBinario(p[1], p.expr_linea, p.term_linea, p.expr_linea.type)
                    
            return self.NodoBinario('error', 'error', 'error', 'error')
        else:
            return p.term_linea
    
    @_('term_linea TIMES factor_linea', 'term_linea DIVIDE factor_linea', 'factor_linea')
    def term_linea(self, p):
        if len(p) == 3:
            path1 = p.term_linea.type + ':main'
            if path1 in self.TS:
                type1 = self.TS[path1]['type']
                if type1 not in ('longint', 'singlef'):
                    print(f"ERROR | No se puede operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
            path2 = p.factor_linea.type + ':main'
            if path2 in self.TS:
                type2 = self.TS[path2]['type']
                if type2 not in ('longint', 'singlef'):
                    print(f"ERROR | No se puede operar entre no numericos")
                    return self.NodoBinario('error', 'error', 'error', 'error')
                
            valido, _ = self.check_type(p.term_linea.type, p.factor_linea.type)
            if valido:
                return self.NodoBinario(p[1], p.term_linea, p.factor_linea, p.term_linea.type)
            
            return self.NodoBinario('error', 'error', 'error', 'error')
        else:
            return p.factor_linea
    
    @_('constante', 'invocacion_funcion', 'invocacion_metodo', 
        'asignable', 'asignacion_de_linea', 'TOL "(" expr ")"')
    def factor_linea(self, p):
        if len(p) == 1:
            return p[0]
        else:
            return self.NodoUnario('TOL', p.expr, 'longint')

    @_('asignable ASSIGN asignable', 'asignable ASSIGN constante')
    def asignacion_de_linea(self, p):
        valido, _ = self.check_type(p.asignable0.type, p[2].type, p[2])
        if valido:
            return self.NodoBinario('=', p.asignable0, p[2], p.asignable0.type)
        else:
            return self.NodoBinario('error', 'error', 'error', 'error')

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
        valido1, _ = self.check_type(p.expr_linea0.type, p.expr_linea1.type, p.expr_linea1, False)
        valido2, _ = self.check_type(p.expr_linea1.type, p.expr_linea0.type, p.expr_linea0, False)
        if valido1 or valido2:
            return self.NodoBinario(p[1], p[0], p[2])
        else:
            return self.NodoBinario('error', 'error', 'error', 'error')

    '''
        Esta funcion nos permite crear subarboles para las sentencias de seleccion, teniendo
        un nodo binario que con tiene la dicha condicion como hijo izquierdo y el cuerpo de
        la sentencia como hijo derecho. En caso de que haya un else, el cuerpo sera un nodo binario
        conteniendo la sentencia THEN y ELSE.
    '''
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

    '''
        Esta funcion nos permite crear subarboles para las sentencias de iteracion, teniendo
        un nodo binario que contiene la inicializacion, la condicion y el cuerpo de la
        sentencia.
    '''
    @_('FROM IDEN ASSIGN2P constante TO constante BY constante REPEAT cuerpo_control')
    def iteracion(self, p):
        self._InfoLogger.info(f"Linea {p.lineno} | Sentencia de iteracion")

        valido, path = self.alcance(p.IDEN)
        if valido:

            if self.TS[path]['uso'] != 'Nombre de variable':
                print(f"ERROR | {p.IDEN} no es una variable en linea {p.lineno}")
                return self.NodoBinario('error', 'error', 'error', 'error')

            equal_type, _ = self.check_type(self.TS[path]['type'], 'longint')
            equal_type2 = all(
                self.check_type(i.type, 'longint')[0]
                for i in [p.constante0, p.constante1, p.constante2]
            )
            if not equal_type or not equal_type2:
                print(f"ERROR | Tipos de datos no validos para iteracion en linea {p.lineno}")
                return self.NodoBinario('error', 'error', 'error', 'error')

            inicializacion = self.NodoBinario(":=", p.IDEN, p.constante0, self.TS[path]['type'])

            sentido = "<=" if p.constante0.op <= p.constante1.op else ">="
            condicion = self.NodoBinario(sentido, p.IDEN, p.constante1)
            condicion = self.NodoUnario("COND", condicion)

            sign = "+" if int(p.constante2.op) >= 0 else "-"
            step = self.NodoBinario(sign, p.IDEN, p.constante2, self.TS[path]['type'])
            incremento = self.NodoBinario("=", p.IDEN, step, self.TS[path]['type'])

            cuerpo_for = self.NodoBinario("CUERPO", p.cuerpo_control, incremento)
            
            composicion_while = self.NodoBinario("COMPWHILE", condicion, cuerpo_for)

            arbol_for = self.NodoBinario("FOR", inicializacion, composicion_while)

            if (sentido == "<=" and sign == '-') or (sentido == ">=" and sign == '+') or (p.constante2.op == 0):
                print(f"ERROR | Iteracion infinita en linea {p.lineno}")
                return self.NodoBinario('error', 'error', 'error', 'error')

            return arbol_for
        else:
            print(f"ERROR | Variable {p.IDEN} no declarada o no alcanzable en linea {p.lineno}")
            return self.NodoBinario('error', 'error', 'error', 'error')    
        
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