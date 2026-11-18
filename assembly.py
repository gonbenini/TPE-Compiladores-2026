from parser import TpParser
import numbers
from utils import get_assembly
wat = get_assembly()
wat_with_aux = get_assembly("./final_assembly.wat")
blocks = []
number_block = 0
var_aux = 0
type_aux = {}
TS = {}

OPS_I32 = {'+': 'i32.add', '-': 'i32.sub', '*': 'i32.mul', '/': 'i32.div_s'}
OPS_F32 = {'+': 'f32.add', '-': 'f32.sub', '*': 'f32.mul', '/': 'f32.div'}

#invertimos los operadores de comparacion porque si el resultado es falso, se salta la ejecucion del bloque de codigo o al else.
COMP_I32 = {'>': 'i32.le_s', '<': 'i32.ge_s', '>=': 'i32.lt_s', '<=': 'i32.gt_s', '==': 'i32.ne', '!=': 'i32.eq'}
COMP_F32 = {'>': 'f32.le', '<': 'f32.ge', '>=': 'f32.lt', '<=': 'f32.gt', '==': 'f32.ne', '!=': 'f32.eq'}

'''Obtenemos el operando derecho para poder asignarlo a una variable auxiliar y reemplazar en el arbol.'''
def assignment(Nodo, type):
    hojas(Nodo.right)
    wat.info(f'{type}.set ${Nodo.left.op}')
    return TpParser.NodoHoja(Nodo.left.type, Nodo.left.op)

'''Obtenemos ambos operandos para poder realizar la operacion y asignar el resultado a una variable auxiliar y reemplazar en el arbol.'''
def arithmetic(Nodo, type):
    hojas(Nodo.left)
    hojas(Nodo.right)
    if Nodo.type == 'longint':
        wat.info(OPS_I32[Nodo.op])
    else:
        wat.info(OPS_F32[Nodo.op])

    global var_aux
    var_aux += 1
    wat.info(f'{type}.set $aux{var_aux}')

    type_aux[f'aux{var_aux}'] = Nodo.type
    return TpParser.NodoHoja(Nodo.type, f'aux{var_aux}')

def converted(Nodo, type):
    hojas(Nodo.son)
    if Nodo.son.type == 'singlef':
        wat.info(f'i32.trunc_f32_s')
    
    global var_aux
    var_aux += 1
    wat.info(f'{type}.set $aux{var_aux}')

    type_aux[f'aux{var_aux}'] = Nodo.type
    return TpParser.NodoHoja(Nodo.type, f'aux{var_aux}')

def comparate(Nodo, type):
    hojas(Nodo.left)
    hojas(Nodo.right)
    if Nodo.type == 'longint':
        wat.info(COMP_I32[Nodo.op])
    else:
        wat.info(COMP_F32[Nodo.op])

    return None #chequear

def condition(Nodo, type):
    Nodo.son = comparate(Nodo.son, type)
    wat.info(f'br_if $b{blocks[-1]}') #salta si la condicion da verdadera
    return None

def selection(Nodo, type):
    global number_block
    number_block += 1
    wat.info(f'(block $b{number_block}')
    blocks.append(number_block)
    if isinstance(Nodo.right, TpParser.NodoBinario):
        number_block += 1
        wat.info(f'(block $b{number_block}')
        blocks.append(number_block)
    Nodo.left = condition(Nodo.left, type)
    if isinstance(Nodo.right, TpParser.NodoBinario): #cuerpo
        Nodo.right.left = generateWAT(Nodo.right.left, type) #then
        wat.info(f'br $b{blocks[-2]}')
        wat.info(f')')
        Nodo.right.right = generateWAT(Nodo.right.right, type) #else
        wat.info(f')')
    else:
        Nodo.left = generateWAT(Nodo.right, type) #then
        wat.info(f')')

    blocks.pop()
    return None

def loop(Nodo, type):
    global number_block
    number_block += 1
    wat.info(f'(block $b{number_block}')
    blocks.append(number_block)
    number_block += 1
    wat.info(f'(loop $b{number_block}')

    Nodo.left = condition(Nodo.left, type)

    blocks.append(number_block)

    Nodo.right = generateWAT(Nodo.right, type)
    wat.info(f'br $b{blocks[-1]}')

    wat.info(f'))')
    blocks.pop()
    blocks.pop()

    return None

def printer(Nodo):
    global TS
    dir = TS[Nodo.son.op]['dir']
    value = TS[Nodo.son.op]['value']
    wat.info(f'i32.const {dir}')
    wat.info(f'i32.const {len(value) - 2}')
    wat.info(f'call $console_log_string')
    return None

def callFunction(Nodo, type):
    wat.info(f'call ${Nodo.op.split(" ")[1]}')
    global var_aux
    var_aux += 1
    wat.info(f'{type}.set $aux{var_aux}')

    type_aux[f'aux{var_aux}'] = Nodo.type
    return TpParser.NodoHoja(Nodo.type, f'aux{var_aux}')

def ret(Nodo):
    hojas(Nodo.son)
    return None

def hojas(Nodo):
    if isinstance(Nodo.op, numbers.Number):
        if Nodo.type == 'longint':
            wat.info(f'i32.const {Nodo.op}')
        else:
            wat.info(f'f32.const {Nodo.op}')
    else:
        wat.info(f'global.get ${Nodo.op}')

def generateWAT(Nodo, type):

    if isinstance(Nodo, TpParser.NodoBinario):

        if Nodo.op == 'IF': return selection(Nodo, type)

        if Nodo.op == 'COMPWHILE': return loop(Nodo, type)

        if not isinstance(Nodo.left, TpParser.NodoHoja): Nodo.left = generateWAT(Nodo.left, type)
        if not isinstance(Nodo.right, TpParser.NodoHoja): Nodo.right = generateWAT(Nodo.right, type)

        if Nodo.op in ('=', ':='): return assignment(Nodo, type)
        if (Nodo.op in OPS_I32) or (Nodo.op in OPS_F32): return arithmetic(Nodo, type)
        if (Nodo.op in COMP_I32) or (Nodo.op in COMP_F32): return comparate(Nodo, type)


    if isinstance(Nodo, TpParser.NodoUnario):
        if not isinstance(Nodo.son, TpParser.NodoHoja): Nodo.son = generateWAT(Nodo.son, type)

        if Nodo.op == 'TOL': return converted(Nodo, type)
        if Nodo.op == 'POUT': return printer(Nodo)
        if Nodo.op == 'TRANSFER_OBJECT': return generateWAT(Nodo.son, type)
        if Nodo.op.split(' ')[0] == 'CALL': return callFunction(Nodo, type)
        if Nodo.op == 'RET': return ret(Nodo)

def declarate_var(var, type):
    global TS
    if TS[var]['type'] == 'longint':
        wat.info(f'({type} ${var} (mut i32) (i32.const 0))')
    elif TS[var]['type'] == 'singlef':
        wat.info(f'({type} ${var} (mut f32) (f32.const 0))')

    else:
        original_type = TS[var]['type']
        real_type = TS[original_type + ':main']['type']
        if real_type == 'longint':
            wat.info(f'({type} ${var} (mut i32) (i32.const 0))')
        elif real_type == 'singlef':
            wat.info(f'({type} ${var} (mut f32) (f32.const 0))')

def declarate_func(func, arbol):
    global TS
    wat.info(f'(func ${func}')
    if TS[func]["type"] == 'longint':
        wat.info(f'(result i32)')
    else:
        wat.info(f'(result f32)')

    generateWAT(arbol, 'local')
    wat.info(')')

def generateDeclaration(arboles):
    global TS
    for i in TS:
        #variables
        if  'uso' in TS[i] and TS[i]['uso'] == 'Nombre de variable':
            type = TS[i]['type']
            if type in ['longint', 'singlef'] or TS[type + ':main']['type'] in ['longint', 'singlef']:
                declarate_var(i, 'global')

        #todas las funciones
        if 'uso' in TS[i] and (TS[i]['uso'] == 'Nombre de funcion' or TS[i]['uso'] == 'Nombre de metodo'):
            declarate_func(i, arboles[i]['nodo'])

        if 'type' in TS[i] and TS[i]['type'] == 'CADN':
            wat.info(f'(data (i32.const {TS[i]["dir"]}) {TS[i]['value']})')

def GetAssembly(Nodo, T, arboles):
    global TS
    TS = T
    generateDeclaration(arboles)
    wat.info(f'\n')

    wat.info('(func $main (export "main")')
    generateWAT(Nodo, 'global')
    wat.info('))')

    clean_wat()

    print(arboles)

def clean_wat():
    wat_with_aux.info('(module')
    wat_with_aux.info('(import "console" "log_string" (func $console_log_string (param i32 i32)))')
    wat_with_aux.info(f'(import "js" "mem" (memory 1))\n')
    for i in range(1, var_aux + 1):
        if type_aux[f'aux{i}'] == 'longint':
            wat_with_aux.info(f'(global $aux{i} (mut i32) (i32.const 0))')

        elif type_aux[f'aux{i}'] == 'singlef':
            wat_with_aux.info(f'(global $aux{i} (mut f32) (f32.const 0))')

    with open("./assembly.wat", "r") as f:
        content = f.read()

    wat_with_aux.info(content)
    