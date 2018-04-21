# coding=utf-8
"""
LATEX
Funciones utilitarias para el manejo de comandos y código LaTeX

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
from __future__ import print_function
import types


def find_block(data, initstr, blankend=False, altend=None):
    """
    Busca el bloque de texto en una lista y devuelve el número de las líneas.

    :param blankend: Indica si el bloque termina en blanco
    :param data: Lista de un archivo
    :param initstr: Texto inicial del bloque
    :param altend: Final alternativo bloque
    :return:
    """
    j = 0
    i = -1
    f = -1
    for k in data:
        k = decodeline(k)
        if initstr.lower() in k.strip().lower() and i < 0:
            i = j
        if not blankend:
            if altend is None:
                if i >= 0 and ((k.strip() == '}' and len(k.strip()) == 1) or k.strip() == '%ENDBLOCK'):
                    f = j
                    break
            else:
                if i >= 0 and k.strip() == altend:
                    f = j
                    break
        else:
            if i >= 0 and k.strip() == '':
                f = j
                break
        j += 1
    return i, f


def find_line(data, initstr, blankend=False):
    """
    Busca una línea.

    :param blankend: Indica si el bloque termina en blanco
    :param data: Lista de un archivo
    :param initstr: Texto inicial de la línea
    :return:
    """
    i, _ = find_block(data, initstr, blankend)
    return i


def find_command(data, commandname):
    """
    Busca las líneas de la función en un archivo.

    :param data: Datos del archivo
    :param commandname: Nombre de la función
    :return:
    """
    data.seek(0)
    k = 0
    commandline = '\\newcommand{\\' + commandname + '}'
    foundcommand = -1
    for i in data:
        i = decodeline(i)
        if foundcommand == -1:
            if commandline in i.strip():
                foundcommand = k
        else:
            if i.strip() == '}':
                return [foundcommand, k]
        k += 1
    return [-1, -1]


def decodeline(line):
    """
    Convierte de unicode a utf8.

    :param line: Línea
    :return:
    """
    if isinstance(type(line), types.UnicodeType):
        return line.encode('utf-8')
    else:
        return str(line)


def replace_argument(line, argnum, new, arginitsep='{', argendsep='}'):
    """
    Reemplaza el argumento entre llaves de una determinada línea.

    :param argendsep: Keyword al finalizar argumento
    :param arginitsep: Keyword al iniciar argumento
    :param new: Nuevos datos
    :param line: Línea a reemplazar
    :param argnum: Número del argumento
    :return: String
    """
    if argnum < 1:
        raise Exception('Numero de argumento invalido')
    n = len(line)
    c = False
    ki = -1
    ke = 0
    a = []
    line = decodeline(line)
    for k in range(0, n):
        if line[k] is arginitsep and c is not True:
            c = True
            k += 1
            ki = k
            a.append([line[ke:ki], False])
        elif line[k] is argendsep and c:
            c = False
            ke = k
            k += 1
            if ke < ki:
                raise Exception('Error al encontrar cierre parametro')
            a.append([line[ki:ke], True])
    a.append([line[ke:n], True])

    d = 0
    f = False
    for k in range(0, len(a)):
        if a[k][1]:
            d += 1
        if d == argnum:
            a[k][0] = new
            f = True
            break
    if not f:
        raise Exception('No se encontro el numero de argumento')
    z = ''
    for k in a:
        z += k[0]
    return z


def paste_external_tex_into_file(fl, libr, files, headersize, libstrip, libdelcom, deletecoments, configfile,
                                 stconfig, dolibstrip=False, add_ending_line=False):
    """
    Pega un archivo de latex en un archivo fl.

    :param fl: Archivo abierto, tipo open
    :param libr: Nombre del .tex
    :param files: Indica ubicación en memoria de los archivos
    :param headersize: Tamaño de cabecera de los .tex
    :param libstrip: Indica si se eliminan los espacios en blanco
    :param libdelcom: Lista que indica si se eliminan
    :param deletecoments: Borrar comentarios del archivo
    :param configfile: Indica el archivo de configuración del template
    :param stconfig: Se añade línea en blanco al reconocer el archivo de configuración
    :param dolibstrip: Se forza strip al archivo
    :param add_ending_line: Indica si se agrega una línea en blanco al final del archivo
    :return:
    """
    # Se escribe desde el largo del header en adelante
    libdata = files[libr]  # Datos del import

    for libdatapos in range(headersize, len(libdata)):
        srclin = libdata[libdatapos]

        # Se borran los comentarios
        if deletecoments and libdelcom:
            if '%' in srclin and '\%' not in srclin:
                if libr == configfile:
                    if srclin.upper() == srclin:
                        if stconfig:
                            fl.write('\n')
                        fl.write(srclin)
                        stconfig = True
                        continue
                comments = srclin.strip().split('%')
                if comments[0] is '':
                    srclin = ''
                else:
                    srclin = srclin.replace('%' + comments[1], '')
                    if libdatapos != len(libdata) - 1:
                        srclin = srclin.strip() + '\n'
                    else:
                        srclin = srclin.strip()
            elif srclin.strip() is '':
                srclin = ''
        else:
            if libr == configfile:
                # noinspection PyBroadException
                try:
                    if libdata[libdatapos + 1][0] == '%' and srclin.strip() is '':
                        srclin = '\n'
                except:
                    pass

        # Se ecribe la línea
        if srclin is not '':
            # Se aplica strip dependiendo del archivo
            if libstrip or dolibstrip:
                fl.write(srclin.strip())
            else:
                fl.write(srclin)

    if libr != configfile and add_ending_line:
        fl.write('\n')  # Se agrega espacio vacío
