"""
LATEX
Funciones utilitarias para el manejo de comandos y código LaTeX

Autor: Pablo Pizarro R. @ ppizarror.com
Licencia:
    The MIT License (MIT)

    Copyright 2017 Pablo Pizarro R.

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

__all__ = [
    'find_block',
    'find_command',
    'find_line',
    'paste_external_tex_into_file',
    'replace_argument'
]

# Importación de librerías
import types
import sys

from extlbx.utils import del_block_from_list, extract_block_from_list, replace_block_from_list


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
    if i == -1:
        raise ValueError(f'No se encontró la cadena {initstr}')
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
    # noinspection PyUnresolvedReferences
    if sys.version_info < (3, 0) and isinstance(type(line), types.UnicodeType):
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
                                 stconfig, dolibstrip=False, add_ending_line=False, dist=False, force_nl=False):
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
    :param dist: Indica que la función se llama en modo dist
    :param force_nl: Forzar nueva línea
    :return:
    """
    # Se escribe desde el largo del header en adelante
    if files is not None:
        libdata = files[libr]  # Datos del import
    else:
        libdata = []
        fld = open(libr, encoding='utf8')
        if '.tex' in libr:
            for i in fld:
                libdata.append(i)
        fld.close()

    # Si tiene END retorna, se borran luego todas las líneas vacías
    if len(libdata) > 0 and libdata[len(libdata) - 1] == '% END':
        libdata.pop()
        while True:
            if libdata[len(libdata) - 1].strip() == '':
                libdata.pop()
            else:
                break

    if '.tex' not in libr:
        headersize = 0

    for libdatapos in range(headersize, len(libdata)):
        srclin = libdata[libdatapos]

        # Forzar nueva línea
        forcenl = False or force_nl
        if ' !NL' in srclin:
            forcenl = True
            srclin = srclin.replace(' !NL', '')
        if ' !DISTNL' in srclin:
            print(srclin)
            forcenl = True and dist
            srclin = srclin.replace(' !DISTNL', '')

        # Forzar borrado de comentarios
        forcedelcom = False
        if ' !DELCOM' in srclin:
            forcedelcom = True
            srclin = srclin.replace(' !DELCOM', '')

        # Forzar strip
        forcestrip = False
        if ' !STRIP' in srclin:
            forcestrip = True
            srclin = srclin.replace(' !STRIP', '')

        # Insertar una línea nueva modo normal
        if ' !PREVNL' in srclin:
            if not dist:
                fl.write('\n')
            srclin = srclin.replace(' !PREVNL', '')

        # Insertar una línea nueva modo normal
        if ' !PREVDISTNL' in srclin:
            if dist:
                fl.write('\n')
            srclin = srclin.replace(' !PREVDISTNL', '')

        # Si es un archivo
        if '% !FILE' in srclin:

            # Obtiene el archivo
            file_libr = srclin.replace('\\input{', '').replace('}', '').strip()
            file_libr = file_libr.split(' ')[0]
            if '.tex' not in file_libr:
                file_libr += '.tex'

            # Obtiene parámetros
            file_params = srclin.strip().split(' ')
            for k in file_params:
                if '<' in k and '>' in k:
                    file_params = k
                    break
            file_params = file_params.replace('<', '').replace('>', '')
            file_params = file_params.split(',')

            file_strip = 'STRIP' in file_params
            file_delcom = 'DELCOM' in file_params
            file_nl = 'NL' in file_params
            file_ignoredist = 'NODIST' in file_params

            if file_ignoredist and not dist:
                paste_external_tex_into_file(fl, file_libr, None, headersize, file_strip, file_delcom, file_delcom,
                                             configfile, stconfig, file_strip, file_nl)
                continue

        # Se borran los comentarios
        if deletecoments and libdelcom or forcedelcom:
            if '%' in srclin and '\\%' not in srclin and '}%' not in srclin and '{%' not in srclin:
                if libr == configfile:
                    if srclin.upper() == srclin:
                        if stconfig:
                            fl.write('\n')
                        fl.write(srclin)
                        stconfig = True
                        continue
                comments = srclin.strip().split('%')
                if comments[0] == '':
                    srclin = ''
                else:
                    srclin = srclin.replace('%' + comments[1], '')
                    if libdatapos != len(libdata) - 1:
                        srclin = srclin.strip() + '\n'
                    else:
                        srclin = srclin.strip()
            elif srclin.strip() == '':
                srclin = ''
        else:
            if libr == configfile:
                # noinspection PyBroadException
                try:
                    if libdata[libdatapos + 1][0] == '%' and srclin.strip() == '':
                        srclin = '\n'
                except:
                    pass

        # Se ecribe la línea
        if srclin != '' and srclin.strip() != '%' and \
                not (not add_ending_line and srclin.strip() == '' and libdatapos == len(libdata) - 1):
            # Se aplica strip dependiendo del archivo
            if libstrip or dolibstrip or forcestrip:
                fl.write(srclin.strip())
            else:
                fl.write(srclin)

        # Se forza nueva línea
        if forcenl:
            # print(srclin)
            fl.write('\n')

    if libr != configfile and add_ending_line or 'imports' in libr:
        fl.write('\n')  # Se agrega espacio vacío


def find_extract(data, element, white_end_block=False):
    """
    Encuentra el bloque determinado por <element> y retorna el bloque.

    :param element: Elemento a buscar
    :param data: Lista.
    :param white_end_block: Indica si el bloque termina en espacio en blanco o con llave
    :return: Retorna la lista que contiene el elemento
    """
    ia, ja = find_block(data, element, white_end_block)
    return extract_block_from_list(data, ia, ja)


def find_replace_block(data, block, newblock, white_end_block=False, iadd=0, jadd=0, verbose=False):
    """
    Busca el bloque en una lista de datos y reemplaza por un bloque <newblock>.

    :param data: Datos
    :param block: Bloque a buscar
    :param newblock: Bloque a reemplazar
    :param iadd: Agrega líneas al inicio del bloque
    :param jadd: Agrega líneas al término del bloque
    :param verbose: Escribe en la línea de comandos los resultados
    :param white_end_block: Indica si el bloque termina en espacio en blanco o con llave
    :return: Lista
    """
    i, j = find_block(data, block, white_end_block)
    if verbose:
        print(i, j)
    return replace_block_from_list(data, newblock, i + iadd, j + jadd)


def find_delete_block(data, block, white_end_block=False, iadd=0, jadd=0, altending=None):
    """
    Busca el bloque en una lista de datos y lo elimina.

    :param data: Datos
    :param block: Bloque a buscar
    :param iadd: Agrega líneas al inicio del bloque
    :param jadd: Agrega líneas al término del bloque
    :param white_end_block: Indica si el bloque termina en espacio en blanco o con llave
    :param altending: Final alternativo bloque
    :return: Lista
    """
    ra, rb = find_block(data, block, blankend=white_end_block, altend=altending)
    return del_block_from_list(data, ra + iadd, rb + jadd)
