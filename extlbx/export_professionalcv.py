# coding=utf-8
"""
EXPORT PROFESSIONAL-CV
Exporta el template Professional-CV

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

# Importación de librerías
from __future__ import print_function
from convert import *
from latex import *
from releases import REL_PROFESSIONALCV
from shutil import copyfile
from stats import *
from subprocess import call
from version import *
from ziputils import *
import time


# noinspection PyBroadException
def exportcv(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
             addwhitespace=False, deletecoments=True, plotstats=False, doclean=True, addstat=True, savepdf=True,
             mainroot=None, backtoroot=False, statsroot=None):
    """
    Exporta Professional-CV.

    :param addstat: Añade estadísticas
    :param addwhitespace: Añade espacio en blanco al comprimir archivos
    :param backtoroot: Devuelve al root
    :param deletecoments: Borra comentarios
    :param doclean: Limpia las variables al terminar
    :param docompile: Indica si compila
    :param dosave: Indica si guarda
    :param mainroot: Carpeta principal de Export-Subtemplate
    :param plotstats: Plotea estadísticas
    :param printfun: Función para imprimir
    :param savepdf: Guarda el pdf
    :param statsroot: Carpeta de estadísticas
    :param version: Versión del template
    :param versiondev: Versión de desarrollo del template
    :param versionhash: Hash de la versión
    :return:
    """

    # Tipo release
    reltag = REL_PROFESSIONALCV
    release = RELEASES[reltag]

    # Se cambia de carpeta
    os.chdir(release['ROOT'])

    # Obtiene archivos
    configfile = release['CONFIGFILE']
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
        if dosave:
            newfl = open(f, 'w')
            for j in data:
                newfl.write(j)
            newfl.close()

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    if dosave:

        # Se modifican propiedades para establecer tipo compacto
        data = files[initconffile]
        d_ttype = replace_argument(d_ttype, 1, 'Compacto')
        d_tvdev = replace_argument(d_tvdev, 1, versiondev + '-C')
        data[l_thash] = d_thash
        data[l_ttype] = d_ttype
        data[l_tvdev] = d_tvdev

        # Se crea el archivo unificado
        fl = open(mainsinglefile, 'w')
        data = files[mainfile]
        data.pop(1)  # Se elimina el tipo de documento del header
        data.insert(1,
                    '% Advertencia:  Documento generado automáticamente a partir de cv.tex y\n%               los '
                    'archivos .tex de la carpeta lib/\n')
        line = 0
        stconfig = False  # Indica si se han escrito comentarios en configuraciones

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

                        # Se escribe desde el largo del header en adelante
                        libdata = files[libr]  # Datos del import
                        libstirp = filestrip[libr]  # Eliminar espacios en blanco
                        libdelcom = filedelcoments[libr]  # Borrar comentarios

                        for libdatapos in range(headersize, len(libdata)):
                            srclin = libdata[libdatapos]

                            # Se borran los comentarios
                            if deletecoments and libdelcom:
                                if '%' in srclin:
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
                                    try:
                                        if libdata[libdatapos + 1][0] == '%' and srclin.strip() is '':
                                            srclin = '\n'
                                    except:
                                        pass

                            # Se ecribe la línea
                            if srclin is not '':
                                # Se aplica strip dependiendo del archivo
                                if libstirp:
                                    fl.write(srclin.strip())
                                else:
                                    fl.write(srclin)

                        if libr != configfile:
                            fl.write('\n')  # Se agrega espacio vacío
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
                        fl.write(d)
                    elif d == '% CONFIGURACIONES\n':
                        pass
                    else:
                        fl.write(d)

            # Aumenta la línea
            line += 1

        fl.close()

    printfun(MSG_FOKTIMER.format(time.time() - t))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            call(['pdflatex', '-interaction=nonstopmode', mainsinglefile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t1 = time.time() - t
            call(['pdflatex', '-interaction=nonstopmode', mainsinglefile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t2 = time.time() - t
            tmean = (t1 + t2) / 2
            printfun(MSG_FOKTIMER.format(tmean))

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
        export_normal.add_excepted_file(czip['EXCEPTED'])
        export_normal.add_file(czip['ADD']['FILES'])
        export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

        # Se exporta el proyecto único
        czip = release['ZIP']['COMPACT']
        export_single = Zip(mainroot + czip['FILE'])
        export_single.add_file(czip['ADD']['FILES'], 'lib/')
        export_single.add_folder(czip['ADD']['FOLDER'])
        export_single.save()

    # Se borra la información generada en las listas
    if doclean:
        clear_dict(RELEASES[reltag], 'FILES')

    # Se cambia a carpeta root
    if backtoroot:
        os.chdir(mainroot)

    return
