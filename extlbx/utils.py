# coding=utf-8
"""
UTILS
Funciones utilitarias generales

Autor: Pablo Pizarro R. @ ppizarror.com
Licencia:
    The MIT License (MIT)

    Copyright 2017-2018 Pablo Pizarro R.

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software
    is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Importación de librerías
import os
import re

# Constantes
LIST_END_LINE = -1
POS_IZQ = 1
POS_DER = 2


class Cd(object):
    def __init__(self, new_path):
        self.newPath = os.path.expanduser(new_path)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def find_line(data, line, returnline=False):
    """
    Encuentra la linea en un archivo y devuelve su ubicación.

    :param returnline: Indica si retorna también la línea buscada
    :param data: Datos del archivo
    :param line: Línea a buscar
    :return:
    """
    k = 0
    if str(type(data)) == "<type 'file'>":
        data.seek(0)
    for i in data:
        if line in i.strip() or line == i.strip():
            if returnline:
                return k, i
            else:
                return k
        k += 1
    if returnline:
        return [-1, '']
    else:
        return -1


def split_str(s, t):
    """
    Divide una cadena s por un término t retornando los elementos no vacíos.

    :param s: String
    :param t: Elemento a dividir la cadena
    :return: Lista de elementos
    """
    s = s.split(t)
    e = list()
    for k in s:
        if k is not '':
            e.append(k)
    return e


def del_block_from_list(data, a, b):
    """
    Borra el bloque de líneas desde a hasta b de la lista.

    :param data: Lista
    :param a: Línea inicial
    :param b: Línea final
    :return:
    """
    k = 0
    newdata = []
    for j in data:
        if k < a or k > b:
            newdata.append(j)
        k += 1
    return newdata


def add_block_from_list(data, new, a, addnewline=False):
    """
    Añade un bloque de líneas desde a.

    :param addnewline: Agrega línea en blanco
    :param data: Lista
    :param new: Datos a añadir
    :param a: Línea inicial
    :return:
    """
    k = 0
    newdata = []
    t = False
    if a == LIST_END_LINE:
        a = len(data) - 1
        t = True and addnewline
    for j in data:
        if k == a:
            if t:
                newdata.append('\n')
            for m in new:
                newdata.append(m)
        else:
            newdata.append(j)
        k += 1
    return newdata


def extract_block_from_list(data, a, b):
    """
    Extrae desde las líneas <a> a la <b> y retorna una lista.

    :param data: Lista de origen
    :param a: Posición a
    :param b: Posición b
    :return:
    """
    newdata = []
    k = 0
    for j in data:
        if a <= k <= b:
            newdata.append(j)
        k += 1
    return newdata


def replace_block_from_list(data, new, ra, rb):
    """
    Reemplaza un bloque de una lista desde <ra> a <rb>.

    :param data: Lista
    :param new: Nuevo bloque
    :param ra: Posición inicial
    :param rb: Posición final
    :return:
    """
    return add_block_from_list(del_block_from_list(data, ra, rb), new, ra)


def file_to_list(filename):
    """
    Carga un archivo y lo pasa a una lista

    :param filename: Nombre del archivo
    :return: Lista
    """
    data = []
    filedata = open(filename)
    for k in filedata:
        data.append(k)
    filedata.close()
    return data


def is_windows():
    """
    Función que retorna True/False si el sistema operativo cliente es Windows o no.

    :return: Boolean
    """
    if os.name == 'nt':
        return True
    return False


def is_linux():
    """
    Función que retorna True/False si el sistema operativo cliente es Linux o no.

    :return: Boolean
    """
    if os.name == 'posix':
        return True
    return False


def is_osx():
    """
    Función que retorna True/False si el sistema operativo cliente es OSX.

    :return: Boolean
    """
    if os.name == 'darwin':
        return True
    return False


def clear_dict(d, entry):
    """
    Limpia un diccionario.

    :param d: Diccionario
    :param entry: Entrada
    :return:
    """
    if type(entry) is list:
        for u in entry:
            for k in d[u].keys():
                d[entry][k] = []
    else:
        for k in d[entry].keys():
            d[entry][k] = []


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments).

    :param text: Lista
    :return:
    """

    # noinspection PyMissingOrEmptyDocstring
    def atoi(t):
        return int(t) if t.isdigit() else t

    return [atoi(c) for c in re.split('(\d+)', text)]


def sum_str_to_list_izq(s, l):
    """
    Suma un string a una lista u otro string por la izquierda

    :param s: String
    :param l: Lista o strng
    :return: Lista o string sumado
    """
    assert isinstance(s, str)
    if isinstance(l, str):
        return s + l
    elif isinstance(l, list):
        for i in range(len(l)):
            l[i] = s + l[i]
        return l
    else:
        raise Exception('Tipo l incorrecto')


def sum_str_to_list_der(s, l):
    """
    Suma un string a una lista u otro string por la derecha.

    :param s: String
    :param l: Lista o strng
    :return: Lista o string sumado
    """
    assert isinstance(s, str)
    if isinstance(l, str):
        return l + s
    elif isinstance(l, list):
        for i in range(len(l)):
            l[i] += s
        return l
    else:
        raise Exception('Tipo l incorrecto')


def sum_str_to_list(s, l, pos):
    """
    Suma un string a una lista u otro string.

    :param s: String
    :param l: Lista
    :param pos: Posición
    :return:
    """
    if pos is POS_IZQ:
        return sum_str_to_list_izq(s, l)
    elif pos is POS_DER:
        return sum_str_to_list_der(s, l)
    else:
        raise Exception('Pos desconocida')
