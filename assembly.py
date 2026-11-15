from parser import TpParser
import numbers

def assignment(Nodo, wat, type):
    wat = generateWAT(Nodo.right, wat, type)
    wat += f'{type}.set ${Nodo.left}\n'
    return wat

def hojas(Nodo, wat):
    if isinstance(Nodo.op, numbers.Number):
        if Nodo.type == 'longint':
            wat += f'i32.const {Nodo.op}\n'
        else:
            wat += f'f32.const {Nodo.op}\n'
    else:
        wat += f'global.get ${Nodo.op}\n'

    return wat

def generateWAT(Nodo, wat, type):
    if Nodo is None:
        return wat
    
    if isinstance(Nodo, TpParser.NodoHoja):
        return hojas(Nodo, wat)

    if isinstance(Nodo, TpParser.NodoBinario) and Nodo.op == '=':
        return assignment(Nodo, wat, type)

    if isinstance(Nodo, TpParser.NodoUnario) and Nodo.op == 'TRANSFER_OBJECT':
        return assignment(Nodo.son, wat, type)
    return wat

def declarate_var(wat, var, type, TS):
    if TS[var]['type'] == 'longint':
        wat+= f'{type} ${var} (mut i32) (i32.const 0)\n'
    else:
        wat+= f'{type} ${var} (mut f32) (f32.const 0)\n'

    return wat

def declarate_func(wat, func, TS, arbol):

    wat += f'(func ${func}\n'
    params = TS[func]['parametros']
    for p in params:
        if TS[p]['type'] == 'longint':
            wat += f'(param ${p} i32)\n'
        else:
            wat += f'(param ${p} f32)\n'

    wat += f'(result {TS[func]["type"]})\n' #preguntar como lo manejamos.

    name = func.split(':')[0]
    #declaracion de variables locales.
    for i in TS:
        if name in i.split(':', 1)[1] and i not in TS[func]['parametros'] and TS[i]['uso'] == 'Nombre de variable':
            wat = declarate_var(wat, i, 'local', TS)

    wat = generateWAT(arbol, wat, 'local')
    return wat

def GetAssembly(Nodo, TS, arboles):
    wat = '(module\n'
    for i in TS:
        if i.split(':', 1)[1] == 'main' or '(' in i: #tratamos a los atributos como globales.
            if  TS[i]['uso'] == 'Nombre de variable' and TS[i]['type'] in ['longint', 'singlef']:
                wat = declarate_var(wat, i, 'global', TS)

            elif TS[i]['uso'] == 'Nombre de funcion':
                wat = declarate_func(wat, i, TS, arboles[i]['nodo'])
            
    wat += '(func $main (export "main")\n'
    wat = generateWAT(Nodo, wat, 'global')
    wat += '))'
    return wat