# coding=utf-8
"""
CONVERT
Convierte los archivos y exporta versiones

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
from latex import *
from releases import *
from shutil import copyfile
from stats import *
from subprocess import call
from version import *
from ziputils import *
import copy
import time

# Constantes
CREATE_NO_WINDOW = 0x08000000
MSG_DCOMPILE = 'COMPILANDO ... '
MSG_FOKTIMER = 'OK [t {0:.3g}]'
MSG_GEN_FILE = 'GENERANDO ARCHIVOS ... '
MSG_LAST_VER = 'ULTIMA VERSION:\t {0}'
MSG_UPV_FILE = 'ACTUALIZANDO VERSION ...'
STRIP_ALL_GENERATED_FILES = False  # Aplica strip a todos los archivos en dist/


# noinspection PyUnusedLocal
def nonprint(arg, *args, **kwargs):
    """
    Desactiva el printing.
    """
    pass


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
    :return:
    """
    i, j = find_block(data, block, white_end_block)
    if verbose:
        print(i, j)
    return replace_block_from_list(data, newblock, i + iadd, j + jadd)


def find_delete_block_recursive(data, block, white_end_block=False, iadd=0, jadd=0, altending=None):
    """
    Busca el bloque en una lista de datos y lo elimina.

    :param data: Datos
    :param block: Bloque a buscar
    :param iadd: Agrega líneas al inicio del bloque
    :param jadd: Agrega líneas al término del bloque
    :param white_end_block: Indica si el bloque termina en espacio en blanco o con llave
    :param altending: Final alternativo bloque
    :return:
    """
    rdata = data
    while True:
        ra, rb = find_block(rdata, block, blankend=white_end_block, altend=altending)
        if ra == -1 or rb == -1:
            return rdata
        rdata = del_block_from_list(rdata, ra + iadd, rb + jadd)


def find_delete_line_recursive(data, line, replace=''):
    """
    Busca el bloque en una lista de datos y lo elimina.

    :param data: Datos
    :param line: Linea a buscar
    :param replace: Linea a reemplazar
    :return:
    """
    rdata = data
    while True:
        r = find_line(rdata, line)
        if r == -1:
            return rdata
        rdata = del_block_from_list(rdata, r, r)
        if replace != '':
            rdata = add_block_from_list(rdata, [replace], r)


def find_delete_block(data, block, white_end_block=False, iadd=0, jadd=0, altending=None):
    """
    Busca el bloque en una lista de datos y lo elimina.

    :param data: Datos
    :param block: Bloque a buscar
    :param iadd: Agrega líneas al inicio del bloque
    :param jadd: Agrega líneas al término del bloque
    :param white_end_block: Indica si el bloque termina en espacio en blanco o con llave
    :param altending: Final alternativo bloque
    :return:
    """
    ra, rb = find_block(data, block, blankend=white_end_block, altend=altending)
    return del_block_from_list(data, ra + iadd, rb + jadd)


# noinspection PyBroadException
def export_informe(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                   addwhitespace=False, deletecoments=True, plotstats=True, doclean=False, addstat=True, savepdf=True,
                   informeroot=None, mainroot=None, backtoroot=False, statsroot=None):
    """
    Exporta el archivo principal, actualiza version.

    :param addstat: Agrega las estadísticas
    :param addwhitespace: Añade espacios en blanco al comprimir archivos
    :param backtoroot: Se devuelve a la carpeta root
    :param deletecoments: Borra comentarios
    :param doclean: Limpia el diccionario
    :param docompile: Compila automáticamente
    :param dosave: Guarda o no los archivos
    :param informeroot: Raíz de informe-template
    :param mainroot: Carpeta raíz del export
    :param plotstats: Plotea las estadísticas
    :param printfun: Función que imprime en consola
    :param savepdf: Guarda el pdf generado
    :param statsroot: Raíz de la carpeta de estadísticas
    :param version: Versión
    :param versiondev: Versión developer
    :param versionhash: Hash de la versión
    :return:
    """

    # Tipo release
    release = RELEASES[REL_INFORME]

    # Se cambia de carpeta
    os.chdir(informeroot)

    # Obtiene archivos
    configfile = release['CONFIGFILE']
    distfolder = release['DIST']
    examplefile = release['EXAMPLEFILE']
    filedelcoments = release['FILEDELCOMENTS']
    files = release['FILES']
    filestrip = release['FILESTRIP']
    initconffile = release['INITCONFFILE']
    mainfile = release['MAINFILE']
    mainsinglefile = release['SINGLEFILE']
    stat = release['STATS']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionheader = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header de la versión
    versionhead = versionheader.format(version, dia)

    # Se buscan números de lineas de hyperref
    initconf_data = open(initconffile)
    initconf_data.read()
    l_tdate, d_tdate = find_line(initconf_data, 'Template.Fecha', True)
    l_thash, d_thash = find_line(initconf_data, 'Template.Version.Hash', True)
    l_ttype, d_ttype = find_line(initconf_data, 'Template.Tipo', True)
    l_tvdev, d_tvdev = find_line(initconf_data, 'Template.Version.Dev', True)
    l_tvrel, d_tvrel = find_line(initconf_data, 'Template.Version.Release', True)
    l_vcmtd, d_vcmtd = find_line(initconf_data, 'pdfproducer', True)
    initconf_data.close()

    # Se actualizan líneas de hyperref
    d_tdate = replace_argument(d_tdate, 1, dia)
    d_thash = replace_argument(d_thash, 1, versionhash)
    d_ttype = replace_argument(d_ttype, 1, 'Normal')
    d_tvdev = replace_argument(d_tvdev, 1, versiondev + '-N')
    d_tvrel = replace_argument(d_tvrel, 1, version)
    d_vcmtd = replace_argument(d_vcmtd, 1, release['VERLINE'].format(version))

    # Carga los archivos y cambian las versiones
    t = time.time()
    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    for f in files.keys():
        data = files[f]
        # noinspection PyBroadException
        try:
            fl = open(f)
            for line in fl:
                data.append(line)
            fl.close()
        except:
            printfun('Error al cargar el archivo {0}'.format(f))

        # Se cambia la versión
        data[headerversionpos] = versionhead

        # Se actualiza la versión en initconf
        if f == initconffile:
            data[l_tdate] = d_tdate
            data[l_thash] = d_thash
            data[l_ttype] = d_ttype
            data[l_tvdev] = d_tvdev
            data[l_tvrel] = d_tvrel
            data[l_vcmtd] = d_vcmtd

        # Se reescribe el archivo
        if dosave and (f == mainfile or f == examplefile):  # Se desactiva la escritura de archivos
            newfl = open(f, 'w')
            for j in data:
                newfl.write(j)
            newfl.close()

    # Se guardan archivos en DIST
    if dosave:
        for f in files.keys():
            fl = open(distfolder + f, 'w')

            # Se escribe el header
            data = files[f]
            kline = 0
            for d in data:
                if kline < headersize:
                    fl.write(d)
                else:
                    break
                kline += 1

            # Strip
            dostrip = True
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    if dosave:

        # Se clona archivo de ejemplo
        copyfile(examplefile, release['EXAMPLECLONE'])
        copyfile(examplefile, distfolder + release['EXAMPLECLONE'])

        # Se modifican propiedades para establecer tipo compacto
        data = files[initconffile]
        d_ttype = replace_argument(d_ttype, 1, 'Compacto')
        d_tvdev = replace_argument(d_tvdev, 1, versiondev + '-C')
        data[l_thash] = d_thash
        data[l_ttype] = d_ttype
        data[l_tvdev] = d_tvdev

        # Se buscan funciones no válidas en compacto
        delfile = 'lib/cmd/core.tex'
        fl = files[delfile]
        files[delfile] = find_delete_block(fl, '\\newcommand{\\bgtemplatetestimg}{')
        ra, rb = find_block(fl, 'GLOBALenvimagenewlinemarg', True)
        nconf = replace_argument(fl[ra], 1, '0.0')
        files[delfile][ra] = nconf

        delfile = 'lib/page/portrait.tex'
        fl = files[delfile]
        a, b = find_block(fl, '\ifthenelse{\equal{\portraitstyle}{\\bgtemplatetestcode}}{', altend='}{')
        files[delfile] = del_block_from_list(fl, a, b)
        a, b = find_block(files[delfile], '\\throwbadconfigondoc{Estilo de portada incorrecto}')
        files[delfile][a] = files[delfile][a][:-2]
        files[delfile] = find_delete_line_recursive(fl, '\hspace{-0.255cm}', replace='}')

        delfile = 'lib/cfg/init.tex'
        fl = files[delfile]
        files[delfile] = find_delete_block(fl,
                                           '\ifthenelse{\equal{\portraitstyle}{\\bgtemplatetestcode}}{\importtikzlib}{}',
                                           white_end_block=True)

        # Se crea el archivo unificado
        fl = open(mainsinglefile, 'w')
        data = files[mainfile]
        data.pop(1)  # Se elimina el tipo de documento del header
        data.insert(1,
                    '% Advertencia:  Documento generado automáticamente a partir del main.tex y\n%               los '
                    'archivos .tex de la carpeta lib/\n')
        # data[codetablewidthpos] = data[codetablewidthpos].replace(itableoriginal, itablenew)
        line = 0
        stconfig = False  # Indica si se han escrito comentarios en configuraciones

        # Se buscan los archivos /all y pega contenido
        all_l = 0
        for d in data:
            if '/all}' in d:
                allfile = d.strip().replace('\input{', '').replace('}', '').split(' ')[0] + '.tex'
                data.pop(all_l)
                newdata = files[allfile]
                for k in newdata:
                    if '%' not in k[0] and k.strip() != '':
                        data.insert(all_l, k.strip() + '\n')
            all_l += 1

        # Se recorren las líneas del archivo
        for d in data:
            write = True
            if line < initdocumentline:
                fl.write(d)
                write = False
            # Si es una línea en blanco se agrega
            if d == '\n' and write:
                fl.write(d)
            else:
                # Si es un import pega el contenido
                try:
                    if d[0:6] == '\input':
                        libr = d.replace('\input{', '').replace('}', '').strip()
                        libr = libr.split(' ')[0]
                        if '.tex' not in libr:
                            libr += '.tex'
                        if libr != examplefile:
                            paste_external_tex_into_file(fl, libr, files, headersize, filestrip[libr],
                                                         filedelcoments[libr], deletecoments, configfile,
                                                         stconfig, add_ending_line=True)
                        else:
                            fl.write(d.replace('lib/etc/', ''))
                        write = False
                except:
                    pass

                # Se agrega un espacio en blanco a la página después del comentario
                if line >= initdocumentline and write:
                    if d[0:2] == '% ' and d[3] != ' ' and d != '% CONFIGURACIONES\n':
                        if d != '% FIN DEL DOCUMENTO\n' and addwhitespace:
                            fl.write('\n')
                            pass
                        d = d.replace('IMPORTACIÓN', 'DECLARACIÓN')
                        if d == '% RESUMEN O ABSTRACT\n':
                            d = '% ======================= RESUMEN O ABSTRACT =======================\n'
                        fl.write(d)
                    elif d == '% CONFIGURACIONES\n':
                        pass
                    else:
                        fl.write(d)

            # Aumenta la línea
            line += 1

        fl.close()

        # Se copia el archivo a dist
        copyfile(mainsinglefile, distfolder + mainsinglefile)

    printfun(MSG_FOKTIMER.format(time.time() - t))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            call(['pdflatex', '-interaction=nonstopmode', mainsinglefile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t1 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainsinglefile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t2 = time.time() - t
            tmean = (t1 + t2) / 2
            printfun(MSG_FOKTIMER.format(t2))

            # Copia a la carpeta pdf_version
            if savepdf:
                copyfile(mainsinglefile.replace('.tex', '.pdf'), release['PDF_FOLDER'].format(version))

        # Se agregan las estadísticas
        if addstat:
            add_stat(statsroot + stat['FILE'], versiondev, tmean, dia, lc, versionhash)

        # Se plotean las estadísticas
        if plotstats:
            plot_stats(statsroot + stat['FILE'], statsroot + stat['CTIME'], statsroot + stat['LCODE'])

    # Se exporta el proyecto normal
    if dosave:
        czip = release['ZIP']['NORMAL']
        export_normal = Zip(mainroot + czip['FILE'])
        export_normal.set_ghostpath(distfolder)
        export_normal.add_excepted_file(czip['EXCEPTED'])
        export_normal.add_file(czip['ADD']['FILES'])
        export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

        # Se exporta el proyecto único
        czip = release['ZIP']['COMPACT']
        export_single = Zip(mainroot + czip['FILE'])
        export_single.set_ghostpath(distfolder)
        export_single.add_file(czip['ADD']['FILES'], 'dist/')
        export_single.add_folder(czip['ADD']['FOLDER'])
        export_single.save()

        # Se exportan los distintos estilos de versiones
        fl_mainfile = open(mainfile)
        fl_mainsinglefile = open(mainsinglefile)

        # Se cargan los archivos en listas
        data_mainfile = []
        data_mainsinglefile = []
        for i in fl_mainfile:
            data_mainfile.append(i)
        for i in fl_mainsinglefile:
            data_mainsinglefile.append(i)

        # Se buscan las líneas del departamento y de la imagen
        fl_pos_dp_mainfile = find_line(data_mainfile, '\def\departamentouniversidad')
        fl_pos_im_mainfile = find_line(data_mainfile, '\def\imagendepartamento')
        fl_pos_dp_mainsinglefile = find_line(data_mainsinglefile, '\def\departamentouniversidad')
        fl_pos_im_mainsinglefile = find_line(data_mainsinglefile, '\def\imagendepartamento')

        # Se cierran los archivos
        fl_mainfile.close()
        fl_mainsinglefile.close()

        # Se recorre cada versión y se genera el .zip
        for m in release['ZIP']['OTHERS']['DATA']:
            data_mainfile[fl_pos_dp_mainfile] = '\\def\\departamentouniversidad {' + m[0][1] + '}\n'
            data_mainfile[fl_pos_im_mainfile] = '\\def\\imagendepartamento {departamentos/' + m[1] + '}\n'
            data_mainsinglefile[fl_pos_dp_mainsinglefile] = '\\def\\departamentouniversidad {' + m[0][1] + '}\n'
            data_mainsinglefile[fl_pos_im_mainsinglefile] = '\\def\\imagendepartamento {departamentos/' + m[1] + '}\n'

            # Se reescriben los archivos
            new_mainfile = open(distfolder + mainfile, 'w')
            for i in data_mainfile:
                new_mainfile.write(i)
            new_mainfile.close()
            new_mainsinglefile = open(distfolder + mainsinglefile, 'w')
            for i in data_mainsinglefile:
                new_mainsinglefile.write(i)
            new_mainsinglefile.close()

            # Se genera el .zip
            czip = release['ZIP']['NORMAL']
            export_normal = Zip(mainroot + release['ZIP']['OTHERS']['NORMAL'].format(m[1]))
            export_normal.set_ghostpath(distfolder)
            export_normal.add_excepted_file(czip['EXCEPTED'])
            export_normal.add_file(czip['ADD']['FILES'])
            export_normal.add_folder('dist/lib')
            export_normal.add_folder(release['ZIP']['OTHERS']['EXPATH'])
            export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(m[1]))
            for k in m[2]:
                export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(k))
            export_normal.save()

            # Se genera el single
            czip = release['ZIP']['COMPACT']
            export_single = Zip(mainroot + release['ZIP']['OTHERS']['SINGLE'].format(m[1]))
            export_single.set_ghostpath(distfolder)
            export_single.add_file(czip['ADD']['FILES'], 'dist/')
            export_single.add_folder(release['ZIP']['OTHERS']['EXPATH'])
            export_single.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(m[1]))
            for k in m[2]:
                export_single.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(k))
            export_single.save()

        data_mainfile[fl_pos_dp_mainfile] = replace_argument(data_mainfile[fl_pos_dp_mainfile], 1,
                                                             'Departamento de la Universidad')
        data_mainfile[fl_pos_im_mainfile] = replace_argument(data_mainfile[fl_pos_im_mainfile], 1,
                                                             'departamentos/fcfm')
        data_mainsinglefile[fl_pos_dp_mainsinglefile] = replace_argument(data_mainsinglefile[fl_pos_dp_mainsinglefile],
                                                                         1, 'Departamento de la Universidad')
        data_mainsinglefile[fl_pos_im_mainsinglefile] = replace_argument(data_mainsinglefile[fl_pos_im_mainsinglefile],
                                                                         1, 'departamentos/fcfm')

        # Se reescriben los archivos
        new_mainfile = open(distfolder + mainfile, 'w')
        for i in data_mainfile:
            new_mainfile.write(i)
        new_mainfile.close()
        new_mainsinglefile = open(distfolder + mainsinglefile, 'w')
        for i in data_mainsinglefile:
            new_mainsinglefile.write(i)
        new_mainsinglefile.close()

    # try:
    #     pyperclip.copy('Version ' + versiondev)
    # except:
    #     pass

    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')

    # Se cambia a carpeta root
    if backtoroot:
        os.chdir(mainroot)

    return


# noinspection PyUnboundLocalVariable
def export_auxiliares(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                      addwhitespace=False, deletecoments=True, plotstats=True, addstat=True, doclean=True,
                      savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta las auxiliares.

    :param addstat: Agrega las estadísticas
    :param addwhitespace: Añade espacios en blanco al comprimir archivos
    :param deletecoments: Borra comentarios
    :param doclean: Borra los archivos generados en lista
    :param docompile: Compila automáticamente
    :param dosave: Guarda o no los archivos
    :param informeroot: Raíz de informe-template
    :param mainroot: Carpeta raíz del export
    :param plotstats: Plotea las estadísticas
    :param printfun: Función que imprime en consola
    :param savepdf: Guarda el pdf generado
    :param statsroot: Raíz de la carpeta de estadísticas
    :param version: Versión
    :param versiondev: Versión developer
    :param versionhash: Hash de la versión
    :return:
    """

    # Tipo release
    release = RELEASES[REL_AUXILIAR]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_informe(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, addwhitespace=addwhitespace, deletecoments=deletecoments,
                   printfun=nonprint, addstat=False, savepdf=False, informeroot=informeroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    mainf = RELEASES[REL_INFORME]['FILES']
    files = release['FILES']
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['lib/cmd/all.tex'] = file_to_list('lib/cmd/all_auxiliar.tex')
    files['lib/cmd/column.tex'] = copy.copy(mainf['lib/cmd/column.tex'])
    files['lib/cmd/core.tex'] = copy.copy(mainf['lib/cmd/core.tex'])
    files['lib/cmd/math.tex'] = copy.copy(mainf['lib/cmd/math.tex'])
    files['lib/cmd/equation.tex'] = copy.copy(mainf['lib/cmd/equation.tex'])
    files['lib/cmd/image.tex'] = copy.copy(mainf['lib/cmd/image.tex'])
    files['lib/cmd/title.tex'] = file_to_list('lib/cmd/auxiliar_title.tex')
    files['lib/cmd/other.tex'] = copy.copy(mainf['lib/cmd/other.tex'])
    files['lib/cmd/auxiliar.tex'] = file_to_list('lib/cmd/auxiliar.tex')
    files['lib/etc/example.tex'] = file_to_list('lib/etc/auxiliar_example.tex')
    files['lib/cfg/init.tex'] = copy.copy(mainf['lib/cfg/init.tex'])
    files['lib/config.tex'] = copy.copy(mainf['lib/config.tex'])
    files['lib/cfg/page.tex'] = copy.copy(mainf['lib/cfg/page.tex'])
    files['lib/style/all.tex'] = copy.copy(mainf['lib/style/all.tex'])
    files['lib/style/color.tex'] = copy.copy(mainf['lib/style/color.tex'])
    files['lib/style/code.tex'] = copy.copy(mainf['lib/style/code.tex'])
    files['lib/style/other.tex'] = copy.copy(mainf['lib/style/other.tex'])
    files['lib/env/imports.tex'] = copy.copy(mainf['lib/env/imports.tex'])
    filedelcoments = release['FILEDELCOMENTS']
    filestrip = release['FILESTRIP']
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # MODIFICA EL MAIN
    main_auxiliar = file_to_list(subrelfile['MAIN'])
    nb = find_extract(main_auxiliar, '% EQUIPO DOCENTE')
    nb.append('\n')
    files[mainfile] = find_replace_block(files[mainfile], '% INTEGRANTES, PROFESORES Y FECHAS', nb)
    files[mainfile][1] = '% Documento:    Archivo principal\n'
    files[mainfile] = find_delete_block(files[mainfile], '% PORTADA', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% RESUMEN O ABSTRACT', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% TABLA DE CONTENIDOS - ÍNDICE', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% IMPORTACIÓN DE ENTORNOS', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% CONFIGURACIONES FINALES', white_end_block=True)
    ra = find_line(files[mainfile], 'titulodelinforme')
    files[mainfile][ra] = '\def\\tituloauxiliar {Título de la auxiliar}\n'
    ra = find_line(files[mainfile], 'temaatratar')
    files[mainfile][ra] = '\def\\temaatratar {Tema de la auxiliar}\n'
    nl = find_extract(main_auxiliar, '% IMPORTACIÓN DE FUNCIONES', True)
    files[mainfile] = find_replace_block(files[mainfile], '% IMPORTACIÓN DE FUNCIONES', nl, white_end_block=True,
                                         jadd=-1)
    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # MODIFICA CONFIGURACIIONES
    fl = release['CONFIGFILE']

    # Configuraciones que se borran
    cdel = ['addemptypagetwosides', 'nomlttable', 'nomltsrc', 'nomltfigure',
            'nomltcont', 'nameportraitpage', 'nameabstract', 'indextitlecolor',
            'portraittitlecolor', 'fontsizetitlei', 'styletitlei',
            'firstpagemargintop', 'romanpageuppercase', 'showappendixsecindex',
            'nomchapter', 'nomnpageof', 'indexforcenewpage']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    ra, rb = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl] = del_block_from_list(files[fl], ra, rb)
    for cdel in ['namereferences', 'nomltwsrc', 'nomltwfigure', 'nomltwtable', 'nameappendixsection',
                 'nomltappendixsection']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    ra, rb = find_block(files[fl], 'showdotontitles', True)
    nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.30').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'cfgbookmarksopenlevel', True)
    nconf = replace_argument(files[fl][ra], 1, '1')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'tablepadding', True)
    files[fl].insert(ra + 1, '\def\\templatestyle {style1}        % Estilo del template: style1,style2\n')

    # CAMBIA IMPORTS
    fl = release['IMPORTSFILE']
    idel = ['usepackage{notoccite}']
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    aux_imports = file_to_list(subrelfile['IMPORTS'])
    nl = find_extract(aux_imports, '% Anexos/Apéndices', True)
    files[fl] = find_replace_block(files[fl], '\ifthenelse{\equal{\showappendixsecindex}', nl, jadd=-1,
                                   white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Estilo portada', white_end_block=True)

    # CAMBIO INITCONF
    fl = release['INITCONFFILE']
    ra, _ = find_block(files[fl], '\checkvardefined{\\titulodelinforme}')
    files[fl][ra] = '\checkvardefined{\\tituloauxiliar}\n'
    ra, _ = find_block(files[fl], '\g@addto@macro\\titulodelinforme\\xspace')
    files[fl][ra] = '\t\g@addto@macro\\tituloauxiliar\\xspace\n'
    ra, _ = find_block(files[fl], '\ifthenelse{\isundefined{\\tablaintegrantes}}{')
    files[fl][ra] = '\ifthenelse{\isundefined{\\equipodocente}}{\n'
    ra, _ = find_block(files[fl], '\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\tablain')
    files[fl][ra] = '\t\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\equipodocente, creando una vacia}\n'
    ra, _ = find_block(files[fl], '\def\\tablaintegrantes {}')
    files[fl][ra] = '\t\def\\equipodocente {}\n'
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Template-Auxiliares')
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX-N')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Documento.Titulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloauxiliar')
    ra, _ = find_block(files[fl], 'pdftitle')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloauxiliar')
    ra, _ = find_block(files[fl], '\setcounter{tocdepth}')
    files[fl][ra] = replace_argument(files[fl][ra], 2, '1')
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))
    files[fl] = find_delete_block(files[fl], '% Se añade listings a tocloft', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Se revisa si se importa tikz', white_end_block=True)

    # PAGECONF
    fl = release['PAGECONFFILE']
    aux_pageconf = file_to_list(subrelfile['PAGECONF'])
    nl = find_extract(aux_pageconf, '% Numeración de páginas', True)
    files[fl] = find_replace_block(files[fl], '% Numeración de páginas', nl, white_end_block=True, jadd=-1)
    nl = find_extract(aux_pageconf, '% Márgenes de páginas y tablas', True)
    files[fl] = find_replace_block(files[fl], '% Márgenes de páginas y tablas', nl, white_end_block=True, jadd=-1)
    nl = find_extract(aux_pageconf, '% Se crean los header-footer', True)
    files[fl] = find_replace_block(files[fl], '% Se crean los header-footer', nl, white_end_block=True, jadd=-1)
    i1, f1 = find_block(aux_pageconf, '% Numeración de objetos', True)
    nl = extract_block_from_list(aux_pageconf, i1, f1)
    files[fl] = add_block_from_list(files[fl], nl, len(files[fl]) + 1)
    pcfg = ['listfigurename', 'listtablename', 'contentsname', 'lstlistlistingname']
    for pcfg in pcfg:
        ra, _ = find_block(files[fl], pcfg)
    files[fl].pop(ra)

    # AUXILIAR FUNCTIONS
    fl = release['FUNCTIONS']
    files[fl] = find_delete_block(files[fl], '% COMPILACION', white_end_block=True)
    aux_fun = file_to_list(subrelfile['ENVFUN'])
    nl = find_extract(aux_fun, '% Crea una sección de referencias solo para bibtex', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE)
    nl = find_extract(aux_fun, '% Crea una sección de anexos', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Inicia código fuente con parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Inserta código fuente con parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Importa código fuente desde un archivo con parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Inicia código fuente sin parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Inserta código fuente sin parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Importa código fuente desde un archivo sin parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Itemize en negrita', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Enumerate en negrita', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    files[fl].pop()

    # CORE FUN
    delfile = release['COREFUN']
    fl = files[delfile]
    files[delfile] = find_delete_block(fl, '\\newcommand{\\bgtemplatetestimg}{')
    fl = files[delfile]
    files[delfile] = find_delete_block(fl, '\def\\bgtemplatetestcode {d0g3}', white_end_block=True)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Template Auxiliar LaTeX\n'
            data[10] = '% Sitio web:    [{0}]\n'.format(release['WEB']['MANUAL'])
            data[11] = '% Licencia MIT: [https://opensource.org/licenses/MIT]\n'
            data[headerversionpos] = versionhead
        except:
            print('Error en archivo ' + fl)

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        for f in files.keys():
            fl = open(subrlfolder + f, 'w')

            # Se escribe el header
            data = files[f]
            kline = 0
            for d in data:
                if kline < headersize:
                    fl.write(d)
                else:
                    break
                kline += 1

            # Strip
            dostrip = True
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

    if dosave:

        # Se crea ejemplo
        fl = open(subrlfolder + 'example.tex', 'w')
        data = files[release['EXAMPLEFILE']]
        for k in data:
            fl.write(k)
        fl.close()

        # Actualización a compacto
        fl = release['INITCONFFILE']
        ra, _ = find_block(files[fl], 'Template.Version.Dev')
        files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX-C')
        ra, _ = find_block(files[fl], 'Template.Tipo')
        files[fl][ra] = replace_argument(files[fl][ra], 1, 'Compacto')

        # Se crea compacto
        line = 0
        fl = open(subrlfolder + release['SINGLEFILE'], 'w')
        data = files[mainfile]
        stconfig = False  # Indica si se han escrito comentarios en configuraciones

        # Se buscan los archivos /all y pega contenido
        all_l = 0
        for d in data:
            if '/all}' in d:
                allfile = d.strip().replace('\input{', '').replace('}', '').split(' ')[0] + '.tex'
                data.pop(all_l)
                newdata = files[allfile]
                for k in newdata:
                    if '%' not in k[0] and k.strip() != '':
                        data.insert(all_l, k.strip() + '\n')
            all_l += 1

        for d in data:
            write = True
            if line < initdocumentline:
                fl.write(d)
                write = False
            # Si es una línea en blanco se agrega
            if d == '\n' and write:
                fl.write(d)
            else:
                # Si es un import pega el contenido
                # noinspection PyBroadException
                try:
                    if d[0:6] == '\input':
                        libr = d.replace('\input{', '').replace('}', '').strip()
                        libr = libr.split(' ')[0]
                        if '.tex' not in libr:
                            libr += '.tex'
                        if libr != examplefile:
                            paste_external_tex_into_file(fl, libr, files, headersize, filestrip[libr],
                                                         filedelcoments[libr], deletecoments, configfile,
                                                         stconfig, add_ending_line=True)

                        else:
                            fl.write(d.replace('lib/etc/', ''))
                        write = False
                except:
                    pass

                # Se agrega un espacio en blanco a la página después del comentario
                if line >= initdocumentline and write:
                    if d[0:2] == '% ' and d[3] != ' ' and d != '% CONFIGURACIONES\n':
                        if d != '% FIN DEL DOCUMENTO\n' and addwhitespace:
                            fl.write('\n')
                        d = d.replace('IMPORTACIÓN', 'DECLARACIÓN')
                        fl.write(d)
                    elif d == '% CONFIGURACIONES\n':
                        pass
                    else:
                        fl.write(d)

            # Aumenta la línea
            line += 1
        fl.close()

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', '-interaction=nonstopmode', release['SINGLEFILE']], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', release['SINGLEFILE']], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                tmean = (t1 + t2) / 2
                printfun(MSG_FOKTIMER.format(t2))

                # Copia a la carpeta pdf_version
                if savepdf:
                    copyfile(release['SINGLEFILE'].replace('.tex', '.pdf'), release['PDF_FOLDER'].format(version))

        # Se agregan las estadísticas
        if addstat:
            add_stat(statsroot + stat['FILE'], versiondev, tmean, dia, lc, versionhash)

        # Se plotean las estadísticas
        if plotstats:
            plot_stats(statsroot + stat['FILE'], statsroot + stat['CTIME'], statsroot + stat['LCODE'])

    # Se exporta el proyecto normal
    if dosave:
        czip = release['ZIP']['NORMAL']
        export_normal = Zip(czip['FILE'])
        with Cd(subrlfolder):
            export_normal.set_ghostpath(czip['GHOST'])
            export_normal.add_excepted_file(czip['EXCEPTED'])
            export_normal.add_file(czip['ADD']['FILES'])
            export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

        # Se exporta el proyecto único
        czip = release['ZIP']['COMPACT']
        export_single = Zip(czip['FILE'])
        with Cd(subrlfolder):
            export_single.set_ghostpath(czip['GHOST'])
            export_single.add_file(release['SINGLEFILE'])
            export_single.add_folder('img')
            export_single.add_file('lib/etc/example.tex', 'lib/etc/')
        export_single.save()

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')
        clear_dict(RELEASES[REL_AUXILIAR], 'FILES')

    # Retorna a root
    os.chdir(mainroot)
    return


def export_controles(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                     addwhitespace=False, deletecoments=True, plotstats=True, addstat=True, savepdf=True,
                     informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta las auxiliares.

    :param addstat: Agrega las estadísticas
    :param addwhitespace: Añade espacios en blanco al comprimir archivos
    :param deletecoments: Borra comentarios
    :param docompile: Compila automáticamente
    :param dosave: Guarda o no los archivos
    :param informeroot: Raíz de informe-template
    :param mainroot: Carpeta raíz del export
    :param plotstats: Plotea las estadísticas
    :param printfun: Función que imprime en consola
    :param savepdf: Guarda el pdf generado
    :param statsroot: Raíz de la carpeta de estadísticas
    :param version: Versión
    :param versiondev: Versión developer
    :param versionhash: Hash de la versión
    :return:
    """

    # Tipo release
    release = RELEASES[REL_CONTROLES]

    # Obtiene archivos
    t = time.time()

    # Genera auxiliares
    # noinspection PyTypeChecker
    export_auxiliares(version, versiondev, versionhash, dosave=False, docompile=False,
                      plotstats=False, addwhitespace=addwhitespace, deletecoments=deletecoments,
                      printfun=nonprint, addstat=False, doclean=False, savepdf=False, informeroot=informeroot,
                      mainroot=mainroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')

    os.chdir(informeroot)
    mainf = RELEASES[REL_AUXILIAR]['FILES']
    files = release['FILES']
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['lib/cmd/all.tex'] = file_to_list('lib/cmd/all_control.tex')
    files['lib/cmd/core.tex'] = copy.copy(mainf['lib/cmd/core.tex'])
    files['lib/cmd/column.tex'] = copy.copy(mainf['lib/cmd/column.tex'])
    files['lib/cmd/control.tex'] = copy.copy(mainf['lib/cmd/auxiliar.tex'])
    files['lib/cmd/math.tex'] = copy.copy(mainf['lib/cmd/math.tex'])
    files['lib/cmd/equation.tex'] = copy.copy(mainf['lib/cmd/equation.tex'])
    files['lib/cmd/image.tex'] = copy.copy(mainf['lib/cmd/image.tex'])
    files['lib/cmd/title.tex'] = copy.copy(mainf['lib/cmd/title.tex'])
    files['lib/cmd/other.tex'] = copy.copy(mainf['lib/cmd/other.tex'])
    files['lib/etc/example.tex'] = file_to_list('lib/etc/control_example.tex')
    files['lib/cfg/init.tex'] = copy.copy(mainf['lib/cfg/init.tex'])
    files['lib/config.tex'] = copy.copy(mainf['lib/config.tex'])
    files['lib/cfg/page.tex'] = copy.copy(mainf['lib/cfg/page.tex'])
    files['lib/style/all.tex'] = copy.copy(mainf['lib/style/all.tex'])
    files['lib/style/color.tex'] = copy.copy(mainf['lib/style/color.tex'])
    files['lib/style/code.tex'] = copy.copy(mainf['lib/style/code.tex'])
    files['lib/style/other.tex'] = copy.copy(mainf['lib/style/other.tex'])
    files['lib/env/imports.tex'] = copy.copy(mainf['lib/env/imports.tex'])
    filedelcoments = release['FILEDELCOMENTS']
    filestrip = release['FILESTRIP']
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # MODIFICA EL MAIN
    main_auxiliar = file_to_list(subrelfile['MAIN'])
    nb = find_extract(main_auxiliar, '% EQUIPO DOCENTE')
    nb.append('\n')
    files[mainfile] = find_replace_block(files[mainfile], '% EQUIPO DOCENTE', nb)
    ra = find_line(files[mainfile], 'tituloauxiliar')
    files[mainfile][ra] = '\def\\tituloevaluacion {Título del Control}\n'
    ra = find_line(files[mainfile], 'temaatratar')
    files[mainfile][ra] = '\def\indicacionevaluacion {\\textbf{INDICACIÓN DEL CONTROL}} % Opcional\n'
    nl = find_extract(main_auxiliar, '% IMPORTACIÓN DE FUNCIONES', True)
    files[mainfile] = find_replace_block(files[mainfile], '% IMPORTACIÓN DE FUNCIONES', nl, white_end_block=True,
                                         jadd=-1)
    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # CONTROL
    fl = release['FUNCTIONS']
    files[fl][1] = '% Documento:    Funciones exclusivas de Template-Controles\n'
    fun_control = file_to_list(fl)
    files[fl].append('\n')
    nl = find_extract(fun_control, '\\newcommand{\\newquestionthemed}')
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    files[fl].append('\n')
    files[fl].append('\n')
    nl = find_extract(fun_control, '\\newcommand{\itempto}', white_end_block=True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE)
    files[fl].pop()
    files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # PAGECONFFILE
    fl = release['PAGECONFFILE']
    control_pageconf = file_to_list(subrelfile['PAGECONF'])
    nl = find_extract(control_pageconf, '% Se crean los header-footer', True)
    files[fl] = find_replace_block(files[fl], '% Se crean los header-footer', nl, white_end_block=True, jadd=-1)

    # CONFIGS
    fl = release['CONFIGFILE']
    ra = find_line(files[fl], 'anumsecaddtocounter')
    files[fl][ra] += '\def\\bolditempto {true}            % Puntaje item en negrita\n'
    cdel = ['templatestyle']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # CAMBIO INITCONF
    fl = release['INITCONFFILE']
    ra, _ = find_block(files[fl], '\checkvardefined{\\tituloauxiliar}')
    files[fl][ra] = '\checkvardefined{\\tituloevaluacion}\n'
    ra, _ = find_block(files[fl], '\g@addto@macro\\tituloauxiliar\\xspace')
    files[fl][ra] = '\t\g@addto@macro\\tituloevaluacion\\xspace\n'
    ra, _ = find_block(files[fl], '\checkvardefined{\\temaatratar}')
    files[fl].pop(ra)
    ra, _ = find_block(files[fl], '\g@addto@macro\\temaatratar\\xspace')
    files[fl].pop(ra)
    _, rb = find_block(files[fl], '\ifthenelse{\isundefined{\equipodocente}}', blankend=True)
    files[fl][rb] = '\ifthenelse{\isundefined{\indicacionevaluacion}}{\n\t\def\indicacionevaluacion {}\n}{}\n\n'
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Template-Controles')
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-CTR/EXM-N')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Documento.Titulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloevaluacion')
    ra, _ = find_block(files[fl], 'pdftitle')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloevaluacion')
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))
    ra, _ = find_block(files[fl], 'Documento.Tema')
    files[fl].pop(ra)
    ra, _ = find_block(files[fl], 'pdfsubject={')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloevaluacion')

    # Cambia encabezado archivos
    for fl in files.keys():
        # noinspection PyBroadException
        try:
            data = files[fl]
            data[0] = '% Template:     Template Controles LaTeX\n'
            data[10] = '% Sitio web:    [{0}]\n'.format(release['WEB']['MANUAL'])
            data[11] = '% Licencia MIT: [https://opensource.org/licenses/MIT]\n'
            data[headerversionpos] = versionhead
        except:
            print('Fallo carga de archivo ' + fl)

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        for f in files.keys():
            fl = open(subrlfolder + f, 'w')

            # Se escribe el header
            data = files[f]
            kline = 0
            for d in data:
                if kline < headersize:
                    fl.write(d)
                else:
                    break
                kline += 1

            # Strip
            dostrip = True
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

    if dosave:

        # Se crea ejemplo
        fl = open(subrlfolder + 'example.tex', 'w')
        data = files[release['EXAMPLEFILE']]
        for k in data:
            fl.write(k)
        fl.close()

        # Actualización a compacto
        fl = release['INITCONFFILE']
        ra, _ = find_block(files[fl], 'Template.Version.Dev')
        files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-CTR/EXM-C')
        ra, _ = find_block(files[fl], 'Template.Tipo')
        files[fl][ra] = replace_argument(files[fl][ra], 1, 'Compacto')

        # Se crea compacto
        line = 0
        fl = open(subrlfolder + release['SINGLEFILE'], 'w')
        data = files[mainfile]
        stconfig = False  # Indica si se han escrito comentarios en configuraciones

        # Se buscan los archivos /all y pega contenido
        all_l = 0
        for d in data:
            if '/all}' in d:
                allfile = d.strip().replace('\input{', '').replace('}', '').split(' ')[0] + '.tex'
                data.pop(all_l)
                newdata = files[allfile]
                for k in newdata:
                    if '%' not in k[0] and k.strip() != '':
                        data.insert(all_l, k.strip() + '\n')
            all_l += 1

        for d in data:
            write = True
            if line < initdocumentline:
                fl.write(d)
                write = False
            # Si es una línea en blanco se agrega
            if d == '\n' and write:
                fl.write(d)
            else:
                # Si es un import pega el contenido
                # noinspection PyBroadException
                try:
                    if d[0:6] == '\input':
                        libr = d.replace('\input{', '').replace('}', '').strip()
                        libr = libr.split(' ')[0]
                        if '.tex' not in libr:
                            libr += '.tex'
                        if libr != examplefile:
                            paste_external_tex_into_file(fl, libr, files, headersize, filestrip[libr],
                                                         filedelcoments[libr], deletecoments, configfile,
                                                         stconfig, add_ending_line=True)
                        else:
                            fl.write(d.replace('lib/etc/', ''))
                        write = False
                except:
                    pass

                # Se agrega un espacio en blanco a la página después del comentario
                if line >= initdocumentline and write:
                    if d[0:2] == '% ' and d[3] != ' ' and d != '% CONFIGURACIONES\n':
                        if d != '% FIN DEL DOCUMENTO\n' and addwhitespace:
                            fl.write('\n')
                        d = d.replace('IMPORTACIÓN', 'DECLARACIÓN')
                        fl.write(d)
                    elif d == '% CONFIGURACIONES\n':
                        pass
                    else:
                        fl.write(d)

            # Aumenta la línea
            line += 1
        fl.close()

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', '-interaction=nonstopmode', release['SINGLEFILE']], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', release['SINGLEFILE']], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                tmean = (t1 + t2) / 2
                printfun(MSG_FOKTIMER.format(t2))

                # Copia a la carpeta pdf_version
                if savepdf:
                    copyfile(release['SINGLEFILE'].replace('.tex', '.pdf'), release['PDF_FOLDER'].format(version))

        # Se agregan las estadísticas
        if addstat:
            add_stat(statsroot + stat['FILE'], versiondev, tmean, dia, lc, versionhash)

        # Se plotean las estadísticas
        if plotstats:
            plot_stats(statsroot + stat['FILE'], statsroot + stat['CTIME'], statsroot + stat['LCODE'])

    # Se exporta el proyecto normal
    if dosave:
        czip = release['ZIP']['NORMAL']
        export_normal = Zip(czip['FILE'])
        with Cd(subrlfolder):
            export_normal.set_ghostpath(czip['GHOST'])
            export_normal.add_excepted_file(czip['EXCEPTED'])
            export_normal.add_file(czip['ADD']['FILES'])
            export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

        # Se exporta el proyecto único
        czip = release['ZIP']['COMPACT']
        export_single = Zip(czip['FILE'])
        with Cd(subrlfolder):
            export_single.set_ghostpath(czip['GHOST'])
            export_single.add_file(subrlfolder + release['SINGLEFILE'])
            export_single.add_folder(subrlfolder + 'img')
            export_single.add_file(subrlfolder + 'lib/etc/example.tex', subrlfolder + 'lib/etc/')
        export_single.save()

    # Limpia el diccionario
    clear_dict(RELEASES[REL_INFORME], 'FILES')
    clear_dict(RELEASES[REL_AUXILIAR], 'FILES')
    clear_dict(RELEASES[REL_CONTROLES], 'FILES')

    os.chdir(mainroot)
    return
