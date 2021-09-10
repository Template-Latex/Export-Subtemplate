# coding=utf-8
"""
CONVERT
Convierte los archivos y exporta versiones

Autor: Pablo Pizarro R. @ ppizarror.com
Licencia:
    The MIT License (MIT)

    Copyright 2017-2021 Pablo Pizarro R.

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
STRIP_TEMPLATE_FILE = False  # Elimina comentarios y aplica strip a archivo del template


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
    :return: Lista
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
    :return: Data
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
    :return: None
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
    :return: Lista
    """
    ra, rb = find_block(data, block, blankend=white_end_block, altend=altending)
    return del_block_from_list(data, ra + iadd, rb + jadd)


def assemble_template_file(templatef, configfile, distfolder, headersize, files):
    """
    Genera el archivo del template.

    :param templatef: Lista del archivo del template
    :param configfile: Archivo de configuraciones
    :param distfolder: Carpeta output
    :param headersize: Tamaño del header
    :param files: Lista de archivos
    """
    modlists = [' !DELCOM', ' !DISTNL', ' !NL', ' !STRIP', ' !PREVNL', ' !PREVDISTNL']
    new_template_file = []
    for d in range(len(templatef)):
        lined = templatef[d]
        if '\input{' == lined.strip()[0:7]:
            ifile = get_file_from_input(lined)
            if ifile == configfile:
                new_template_file.append('\input{template_config}\n')
            else:
                if STRIP_TEMPLATE_FILE:
                    dataifile = file_to_list(distfolder + ifile)
                else:
                    dataifile = files[ifile]
                if new_template_file[-1].strip() != '' and '% ' not in new_template_file[-1]:
                    new_template_file.append('\n')
                for j in range(len(dataifile)):
                    jline = dataifile[j]
                    if j < headersize:
                        continue
                    if jline.strip() == '' and STRIP_TEMPLATE_FILE:
                        continue
                    if j == len(dataifile) - 1 and jline.strip() == '':
                        continue
                    if '% ' in jline:
                        for mod in modlists:
                            jline = jline.replace(mod, '')
                    new_template_file.append(jline)
        else:
            new_template_file.append(lined)
    # tlen = len(new_template_file) - 1
    # new_template_file[tlen] = new_template_file[tlen].strip()
    save_list_to_file(new_template_file, distfolder + 'template.tex')


def compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                     release, version, stat, versiondev, dia, lc, versionhash, plotstats):
    """
    Compila el template.

    :param subrlfolder: Carpeta de distribución
    :param printfun: Función para imprimir en consola
    :param mainfile: Archivo principal
    :param savepdf: Guarda el pdf
    :param addstat: Guarda las estadísticas
    :param statsroot: Raíz carpeta estadísticas
    :param release: Release
    :param version: Número de versión
    :param stat: Estadísticas
    :param versiondev: Versión DEV
    :param dia: Día
    :param lc: LC
    :param versionhash: Hash de la versión
    :param plotstats: Imprime estadísticas
    """
    t = time.time()
    with open(os.devnull, 'w') as FNULL:
        printfun(MSG_DCOMPILE, end='')
        with Cd(subrlfolder):
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t1 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t2 = time.time() - t
            # t = time.time()
            # call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            # t3 = time.time() - t
            # t = time.time()
            # call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            # t4 = time.time() - t
            # tmean = (t1 + t2) / 2
            tmean = min(t1, t2)
            # tmean = min(t1, t2, t3, t4)
            printfun(MSG_FOKTIMER.format(tmean))

            # Copia a la carpeta pdf_version
            if savepdf:
                copyfile(mainfile.replace('.tex', '.pdf'), release['PDF_FOLDER'].format(version))

    # Se agregan las estadísticas
    if addstat:
        add_stat(statsroot + stat['FILE'], versiondev, tmean, dia, lc, versionhash)

    # Se plotean las estadísticas
    if plotstats:
        plot_stats(statsroot + stat['FILE'], statsroot + stat['CTIME'], statsroot + stat['LCODE'])


# noinspection PyBroadException
def export_informe(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                   plotstats=True, doclean=False, addstat=True, savepdf=True,
                   informeroot=None, mainroot=None, backtoroot=False, statsroot=None):
    """
    Exporta el archivo principal, actualiza version.

    :param addstat: Agrega las estadísticas
    :param backtoroot: Se devuelve a la carpeta root
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_INFORME]

    # Se cambia de carpeta
    os.chdir(informeroot)

    # Obtiene archivos
    configfile = 'src/config.tex'
    examplefile = 'src/etc/example.tex'
    files = release['FILES']
    initconffile = 'src/cfg/init.tex'
    mainfile = release['MAINFILE']
    distfolder = release['DIST']
    stat = release['STATS']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
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
    l_tdate, d_tdate = find_line(initconf_data, 'Template.Date', True)
    l_thash, d_thash = find_line(initconf_data, 'Template.Version.Hash', True)
    l_ttype, d_ttype = find_line(initconf_data, 'Template.Type', True)
    l_tvdev, d_tvdev = find_line(initconf_data, 'Template.Version.Dev', True)
    l_tvrel, d_tvrel = find_line(initconf_data, 'Template.Version.Release', True)
    l_vcmtd, d_vcmtd = find_line(initconf_data, 'pdfproducer', True)
    initconf_data.close()

    # Se actualizan líneas de hyperref
    d_tdate = replace_argument(d_tdate, 1, dia)
    d_thash = replace_argument(d_thash, 1, versionhash)
    d_ttype = replace_argument(d_ttype, 1, 'Normal')
    d_tvdev = replace_argument(d_tvdev, 1, versiondev)
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
            save_list_to_file(data, f)

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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(distfolder + configfile, distfolder + 'template_config.tex')
        copyfile(distfolder + examplefile, distfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, distfolder, headersize, files)

    # Se obtiene la cantidad de líneas de código
    lc = 0
    for f in files.keys():
        lc += len(files[f])

    printfun(MSG_FOKTIMER.format(time.time() - t))

    # Compila el archivo
    if docompile and dosave:
        compile_template(distfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

    # Se exporta el proyecto normal
    if dosave:
        # Se exportan los distintos estilos de versiones
        jmainfilel = 0
        data_mainfile = file_to_list(distfolder + mainfile)
        for j in range(len(data_mainfile)):
            if get_file_from_input(data_mainfile[j]) == examplefile:
                data_mainfile[j] = '\input{example} % Ejemplo, se puede borrar\n'
                jmainfilel = j
        save_list_to_file(data_mainfile, distfolder + mainfile)

        # Se crea el archivo principal
        czip = release['ZIP']['NORMAL']
        export_normal = Zip(mainroot + czip['FILE'])
        export_normal.set_ghostpath(distfolder)
        export_normal.add_excepted_file(czip['EXCEPTED'])
        export_normal.add_file(czip['ADD']['FILES'])
        export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

        # Se buscan las líneas del departamento y de la imagen
        fl_pos_dp_mainfile = find_line(data_mainfile, '\def\universitydepartment')
        fl_pos_im_mainfile = find_line(data_mainfile, '\def\universitydepartmentimage')

        # Se recorre cada versión y se genera el .zip
        for m in DEPTOS:
            data_mainfile[fl_pos_dp_mainfile] = '\\def\\universitydepartment {' + m[0] + '}\n'
            data_mainfile[fl_pos_im_mainfile] = '\\def\\universitydepartmentimage {departamentos/' + m[1] + '}\n'

            # Se reescriben los archivos
            save_list_to_file(data_mainfile, distfolder + mainfile)

            # Se genera el .zip
            czip = release['ZIP']['NORMAL']
            export_normal = Zip(mainroot + release['ZIP']['OTHERS']['NORMAL'].format(m[1]))
            export_normal.set_ghostpath(distfolder)
            export_normal.add_excepted_file(czip['EXCEPTED'])
            export_normal.add_file(czip['ADD']['FILES'])
            export_normal.add_folder(release['ZIP']['OTHERS']['EXPATH'])
            export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(m[1]))
            for k in m[2]:
                export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(k))
            export_normal.save()

        # Rollback archivo. Necesario para subtemplates
        data_mainfile[fl_pos_dp_mainfile] = replace_argument(data_mainfile[fl_pos_dp_mainfile], 1,
                                                             'Departamento de la Universidad')
        data_mainfile[fl_pos_im_mainfile] = replace_argument(data_mainfile[fl_pos_im_mainfile], 1,
                                                             'departamentos/fcfm')
        data_mainfile[jmainfilel] = examplefile + ' % Ejemplo, se puede borrar\n'
        save_list_to_file(data_mainfile, distfolder + mainfile)

    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')

    # Se cambia a carpeta root
    if backtoroot:
        os.chdir(mainroot)


# noinspection PyUnboundLocalVariable
def export_auxiliares(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                      plotstats=True, addstat=True, doclean=True,
                      savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta las auxiliares.

    :param addstat: Agrega las estadísticas
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_AUXILIAR]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_informe(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, printfun=nonprint, addstat=False, savepdf=False,
                   informeroot=informeroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    mainf = RELEASES[REL_INFORME]['FILES']
    files = release['FILES']
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['template.tex'] = file_to_list('template_auxiliar.tex')
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = file_to_list('src/cmd/auxiliar_title.tex')
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/auxiliar.tex'] = file_to_list('src/cmd/auxiliar.tex')
    files['src/etc/example.tex'] = file_to_list('src/etc/example_auxiliar.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA EL MAIN
    # -------------------------------------------------------------------------
    main_auxiliar = file_to_list('main_auxiliar.tex')
    nb = find_extract(main_auxiliar, '% EQUIPO DOCENTE')
    nb.append('\n')
    files[mainfile] = find_replace_block(files[mainfile], '% INTEGRANTES, PROFESORES Y FECHAS', nb)
    files[mainfile][1] = '% Documento:    Archivo principal\n'
    files[mainfile] = find_delete_block(files[mainfile], '% PORTADA', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% RESUMEN O ABSTRACT', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% TABLA DE CONTENIDOS - ÍNDICE', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% IMPORTACIÓN DE ENTORNOS', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% CONFIGURACIONES FINALES', white_end_block=True)
    ra = find_line(files[mainfile], 'documenttitle')
    files[mainfile][ra] = '\def\\documenttitle {Título de la auxiliar}\n'
    ra = find_line(files[mainfile], 'documentsubtitle')
    files[mainfile].pop(ra)
    ra = find_line(files[mainfile], 'documentsubject')
    files[mainfile][ra] = '\def\\documentsubject {Tema de la auxiliar}\n'
    for j in range(len(files[mainfile])):
        if get_file_from_input(files[mainfile][j]) == examplefile:
            files[mainfile][j] = '\input{example} % Ejemplo, se puede borrar\n'
    ra = find_line(files[mainfile], 'universitydepartmentimagecfg')
    files[mainfile][ra] = replace_argument(files[mainfile][ra], 1, 'height=1.75cm')

    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'

    # Configuraciones que se borran
    cdel = ['addemptypagetwosides', 'nameportraitpage', 'indextitlecolor',
            'portraittitlecolor', 'fontsizetitlei', 'styletitlei',
            'firstpagemargintop', 'romanpageuppercase', 'showappendixsecindex',
            'nomchapter', 'nomnpageof', 'indexforcenewpage', 'predocpageromannumber',
            'predocresetpagenumber', 'margineqnindexbottom', 'margineqnindextop',
            'bibtexindexbibliography', 'anumsecaddtocounter', 'predocpageromanupper']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    ra, rb = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl] = del_block_from_list(files[fl], ra, rb)
    for cdel in []:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    # ra, rb = find_block(files[fl], 'showdotaftersnum', True) Desactivado desde v3.3.4
    # nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    # files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'equationrestart', True)
    nconf = replace_argument(files[fl][ra], 1, 'none')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.3').replace('  %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'cfgbookmarksopenlevel', True)
    nconf = replace_argument(files[fl][ra], 1, '1')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'showlinenumbers', True)
    files[fl].insert(ra + 1, '\def\\templatestyle {style1}        % Estilo del template: style1 a style4\n')
    # files[fl].pop()

    # -------------------------------------------------------------------------
    # CAMBIA LAS ECUACIONES
    # -------------------------------------------------------------------------
    fl = 'src/cmd/equation.tex'
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['usepackage{notoccite}', 'ragged2e']
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    aux_imports = file_to_list('src/env/imports_auxiliar.tex')
    nl = find_extract(aux_imports, '% Anexos/Apéndices', True)
    files[fl] = find_replace_block(files[fl], '\ifthenelse{\equal{\showappendixsecindex}', nl, jadd=-1,
                                   white_end_block=True)

    ra, _ = find_block(files[fl], '% En v6.3.7 se desactiva cellspace', True)
    rb, _ = find_block(files[fl], '% \usepackage{subfigure}', True)
    files[fl] = del_block_from_list(files[fl], ra, rb + 1)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    ra, _ = find_block(files[fl], '\ifthenelse{\isundefined{\\authortable}}{')
    files[fl][ra] = '\ifthenelse{\isundefined{\\teachingstaff}}{\n'
    ra, _ = find_block(files[fl], '\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\authortable')
    files[fl][ra] = '\t\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\teachingstaff, creando una vacia}\n'
    ra, _ = find_block(files[fl], '\def\\authortable {}')
    files[fl][ra] = '\t\def\\teachingstaff {}}{\n'

    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], '\setcounter{tocdepth}')
    files[fl][ra] = replace_argument(files[fl][ra], 2, '1')
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    files[fl] = find_delete_block(files[fl], '% Se añade listings a tocloft', white_end_block=True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Se revisa si se importa tikz', white_end_block=True, iadd=-1)

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    # Elimina subtitulo
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\documentsubtitle}{}}{', jadd=1)

    ra, _ = find_block(files[fl], 'Sloppy arruina portadas al exigir', True)
    files[fl].pop(ra)

    # Agrega saltos de líneas
    for i in ['% Crea referencias enumeradas en apacite', '% Desactiva la URL de apacite',
              '% Referencias en 2 columnas']:
        ra, _ = find_block(files[fl], i)
        files[fl][ra] = '\n' + files[fl][ra]

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/page.tex'
    aux_pageconf = file_to_list('src/cfg/page_auxiliar.tex')
    nl = find_extract(aux_pageconf, '% Numeración de páginas', True)
    files[fl] = find_replace_block(files[fl], '% Numeración de páginas', nl, white_end_block=True, jadd=-1)
    nl = find_extract(aux_pageconf, '% Márgenes de páginas y tablas', True)
    files[fl] = find_replace_block(files[fl], '% Márgenes de páginas y tablas', nl, white_end_block=True, jadd=-1)
    nl = find_extract(aux_pageconf, '% Se crean los header-footer', True)
    files[fl] = find_replace_block(files[fl], '% Se crean los header-footer', nl, white_end_block=True, jadd=-1)
    i1, f1 = find_block(aux_pageconf, '% Numeración de objetos', True)
    nl = extract_block_from_list(aux_pageconf, i1, f1)
    files[fl] = add_block_from_list(files[fl], nl, len(files[fl]) + 1)
    files[fl].pop()
    _, rb = find_block(files[fl], '% Configura el nombre del abstract', blankend=True)
    i1, f1 = find_block(aux_pageconf, '% Establece el estilo de las sub-sub-sub-secciones', True)
    nl = extract_block_from_list(aux_pageconf, i1 - 1, f1)
    nl.insert(0, '\n')
    files[fl] = add_block_from_list(files[fl], nl, rb)
    # files[fl].append('\\titleclass{\subsubsubsection}{straight}[\subsection]\n')

    # -------------------------------------------------------------------------
    # AUXILIAR FUNCTIONS
    # -------------------------------------------------------------------------
    fl = 'src/cmd/auxiliar.tex'
    files[fl] = find_delete_block(files[fl], '% COMPILACION', white_end_block=True)
    aux_fun = file_to_list('src/env/environments.tex')
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

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '% Imagen de prueba tikz', white_end_block=True)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Auxiliar LaTeX\n'
            data[headersize - 3] = '% Manual template: [{0}]\n'.format(release['WEB']['MANUAL'])
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

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

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')
        clear_dict(RELEASES[REL_AUXILIAR], 'FILES')

    # Retorna a root
    os.chdir(mainroot)


def export_controles(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                     plotstats=True, addstat=True, savepdf=True,
                     informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta las auxiliares.

    :param addstat: Agrega las estadísticas
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_CONTROLES]

    # Obtiene archivos
    t = time.time()

    # Genera auxiliares
    # noinspection PyTypeChecker
    export_auxiliares(version, versiondev, versionhash, dosave=False, docompile=False,
                      plotstats=False, printfun=nonprint, addstat=False, doclean=False, savepdf=False,
                      informeroot=informeroot, mainroot=mainroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')

    os.chdir(informeroot)
    mainf = RELEASES[REL_AUXILIAR]['FILES']
    files = release['FILES']
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['template.tex'] = file_to_list('template_control.tex')
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/control.tex'] = copy.copy(mainf['src/cmd/auxiliar.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_control.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA EL MAIN
    # -------------------------------------------------------------------------
    main_auxiliar = file_to_list('main_control.tex')
    nb = find_extract(main_auxiliar, '% EQUIPO DOCENTE')
    nb.append('\n')
    files[mainfile] = find_replace_block(files[mainfile], '% EQUIPO DOCENTE', nb)
    ra = find_line(files[mainfile], 'documenttitle')
    files[mainfile][ra] = '\def\\documenttitle {Título del Control}\n'
    ra = find_line(files[mainfile], 'documentsubject')
    files[mainfile][ra] = '\def\evaluationindication {\\textbf{INDICACIÓN DEL CONTROL}}\n'
    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # -------------------------------------------------------------------------
    # CONTROL
    # -------------------------------------------------------------------------
    fl = 'src/cmd/control.tex'
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

    # -------------------------------------------------------------------------
    # PAGECONFFILE
    # -------------------------------------------------------------------------
    fl = 'src/cfg/page.tex'
    control_pageconf = file_to_list('src/cfg/page_control.tex')
    nl = find_extract(control_pageconf, '% Se crean los header-footer', True)
    files[fl] = find_replace_block(files[fl], '% Se crean los header-footer', nl, white_end_block=True, jadd=-1)

    # -------------------------------------------------------------------------
    # CONFIGS
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'
    ra = find_line(files[fl], '% CONFIGURACIONES DE OBJETOS')
    files[fl][ra] += '\def\\bolditempto {true}            % Puntaje item en negrita\n'
    cdel = ['templatestyle']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    ra, _ = find_block(files[fl], '\checkvardefined{\\documentsubject}')
    files[fl].pop(ra)
    ra, _ = find_block(files[fl], '\g@addto@macro\\documentsubject\\xspace')
    files[fl].pop(ra)
    _, rb = find_block(files[fl], '\ifthenelse{\isundefined{\\teachingstaff}}', blankend=True)
    files[fl][rb] = '\ifthenelse{\isundefined{\\evaluationindication}}{\n\t\def\\evaluationindication {}\n}{}\n\n'

    ra, _ = find_block(files[fl], '\pdfmetainfosubject')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\documenttitle')
    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-CTR/EXM')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))
    ra, _ = find_block(files[fl], 'Document.Subject')
    files[fl].pop(ra)

    # Cambia encabezado archivos
    for fl in files.keys():
        # noinspection PyBroadException
        try:
            data = files[fl]
            data[0] = '% Template:     Controles LaTeX\n'
            data[headersize - 3] = '% Manual template: [{0}]\n'.format(release['WEB']['MANUAL'])
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

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

    # Limpia el diccionario
    clear_dict(RELEASES[REL_INFORME], 'FILES')
    clear_dict(RELEASES[REL_AUXILIAR], 'FILES')
    clear_dict(RELEASES[REL_CONTROLES], 'FILES')

    os.chdir(mainroot)


# noinspection PyUnboundLocalVariable
def export_reporte(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                   plotstats=True, addstat=True, doclean=True,
                   savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta los reportes.

    :param addstat: Agrega las estadísticas
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_REPORTE]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_informe(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, printfun=nonprint, addstat=False, savepdf=False, informeroot=informeroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    mainf = RELEASES[REL_INFORME]['FILES']
    files = release['FILES']
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['template.tex'] = file_to_list('template_reporte.tex')
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_reporte.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'
    distfolder = release['DIST']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA EL MAIN
    # -------------------------------------------------------------------------
    main_reporte = file_to_list('main_reporte.tex')
    files[mainfile] = find_delete_block(files[mainfile], '% INTEGRANTES, PROFESORES Y FECHAS', jadd=1)
    files[mainfile][1] = '% Documento:    Archivo principal\n'
    files[mainfile] = find_delete_block(files[mainfile], '% PORTADA', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% RESUMEN O ABSTRACT', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% TABLA DE CONTENIDOS - ÍNDICE', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% IMPORTACIÓN DE ENTORNOS', white_end_block=True)
    ra, _ = find_block(files[mainfile], '\input{src/etc/example}', True)
    files[mainfile] = add_block_from_list(files[mainfile], main_reporte, ra, addnewline=True)
    ra, _ = find_block(files[mainfile], 'universitydepartmentimagecfg', True)
    files[mainfile].pop(ra)
    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # Cambia las variables del documento principales
    nl = ['% INFORMACIÓN DEL DOCUMENTO\n',
          '\def\\documenttitle {Título del reporte}\n',
          '\def\\documentsubtitle {}\n',
          '\def\\documentsubject {Tema a tratar}\n',
          '\def\\documentdate {\\today}\n\n']
    files[mainfile] = find_replace_block(files[mainfile], '% INFORMACIÓN DEL DOCUMENTO', nl, white_end_block=True,
                                         jadd=-1)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'
    config_reporte = file_to_list('src/config_reporte.tex')

    # Configuraciones que se borran
    cdel = ['firstpagemargintop', 'portraitstyle', 'predocpageromannumber', 'predocpageromanupper',
            'predocresetpagenumber', 'fontsizetitlei', 'styletitlei', 'nameportraitpage', 'indextitlecolor',
            'addindextobookmarks', 'portraittitlecolor', 'margineqnindexbottom', 'margineqnindextop',
            'bibtexindexbibliography', 'addemptypagetwosides']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    for cdel in ['pagemargintop']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('  %', '%')  # Reemplaza espacio en comentarios de la lista
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    files[fl] = add_block_from_list(files[fl], [files[fl][ra],
                                                '\def\indexdepth {4}                % Profundidad de los marcadores\n'],
                                    ra, addnewline=True)
    ra, rb = find_block(files[fl], 'pagemarginbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '2.5')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '3.81')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemarginright', True)
    nconf = replace_argument(files[fl][ra], 1, '3.81')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.5')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style7')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'fontsizetitle', True)
    nconf = replace_argument(files[fl][ra], 1, '\\Large')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'fontsizesubtitle', True)
    nconf = replace_argument(files[fl][ra], 1, '\\large')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'fontsizesubsubtitle', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'hfwidthwrap', True)
    files[fl] = replace_block_from_list(files[fl], config_reporte, ra, ra)

    ra, _ = find_block(files[fl], '% CONFIGURACIÓN DE LAS LEYENDAS - CAPTION', True)
    files[fl][ra] = '\n' + files[fl][ra]

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['ragged2e']
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    ra, _ = find_block(files[fl], '\showappendixsecindex')
    nl = ['\\def\\showappendixsecindex {false}\n',
          files[fl][ra]]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    ra, _ = find_block(files[fl], '% En v6.3.7 se desactiva cellspace', True)
    rb, _ = find_block(files[fl], '% \usepackage{subfigure}', True)
    files[fl] = del_block_from_list(files[fl], ra, rb + 1)

    ra, _ = find_block(files[fl], '% Desde v6.2.8 se debe cargar al final para evitar errores:', True)
    rb, _ = find_block(files[fl], '% Desde v6.5.6 se carga después de las referencias ', True)
    files[fl] = del_block_from_list(files[fl], ra, rb)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_auxiliar = file_to_list('src/cfg/init_reporte.tex')
    nl = find_extract(init_auxiliar, 'Operaciones especiales Template-Reporte', True)
    nl.insert(0, '% -----------------------------------------------------------------------------\n')
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE)
    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Se crean variables si se borraron', True, iadd=-1)

    cdel = ['\\author{\\pdfmetainfoauthor}', '\\title{\\pdfmetainfotitle}']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # Borra línea definiciones
    ra, _ = find_block(files[fl], '\checkvardefined{\\universitydepartmentimagecfg}')
    files[fl].pop(ra)

    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-REPT')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    ra, _ = find_block(files[fl], 'Sloppy arruina portadas al exigir', True)
    files[fl].pop(ra)

    # Agrega saltos de líneas
    for i in ['% Crea referencias enumeradas en apacite', '% Desactiva la URL de apacite',
              '% Referencias en 2 columnas']:
        ra, _ = find_block(files[fl], i)
        files[fl][ra] = '\n' + files[fl][ra]

    # Borra último salto de línea
    files[fl].pop()

    # -------------------------------------------------------------------------
    # CAMBIA TÍTULOS
    # -------------------------------------------------------------------------
    fl = 'src/cmd/title.tex'
    files[fl] = find_delete_block(files[fl], '% Crea una sección en el índice y en el header', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título en un índice, con número de página',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título en un índice, sin número de página',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-sub-subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl],
                                  '% Insertar un título sin número, sin indexar y sin cambiar el título del header',
                                  white_end_block=True)

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '\\newcommand{\\bgtemplatetestimg}{')
    files[fl] = find_delete_block(files[fl], '\def\\bgtemplatetestcode {d0g3}', white_end_block=True)
    ra, _ = find_block(files[fl], '% Imagen de prueba tikz')
    files[fl].pop(ra)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Reporte LaTeX\n'
            data[headersize - 3] = '% Manual template: [{0}]\n'.format(release['WEB']['MANUAL'])
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

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

        # Se exportan los distintos estilos de versiones
        data_mainfile = file_to_list(subrlfolder + mainfile)

        # Se buscan las líneas del departamento y de la imagen
        fl_pos_dp_mainfile = find_line(data_mainfile, '\def\universitydepartment')
        fl_pos_im_mainfile = find_line(data_mainfile, '\def\universitydepartmentimage')

        # Se recorre cada versión y se genera el .zip
        for m in DEPTOS:
            data_mainfile[fl_pos_dp_mainfile] = '\\def\\universitydepartment {' + m[0] + '}\n'
            data_mainfile[fl_pos_im_mainfile] = '\\def\\universitydepartmentimage {departamentos/' + m[1] + '}\n'

            # Se reescriben los archivos
            save_list_to_file(data_mainfile, subrlfolder + mainfile)

            # Se genera el .zip
            czip = release['ZIP']['NORMAL']
            export_normal = Zip(release['ZIP']['OTHERS']['NORMAL'].format(m[1]))
            with Cd(subrlfolder):
                export_normal.set_ghostpath(distfolder)
                export_normal.add_excepted_file(czip['EXCEPTED'])
                export_normal.add_file(czip['ADD']['FILES'])
                export_normal.add_folder(release['ZIP']['OTHERS']['EXPATH'])
                export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(m[1]))
                for k in m[2]:
                    export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(k))
            export_normal.save()

        # Rollback archivo principal. Necesario para subtemplates
        data_mainfile[fl_pos_dp_mainfile] = replace_argument(data_mainfile[fl_pos_dp_mainfile], 1,
                                                             'Departamento de la Universidad')
        data_mainfile[fl_pos_im_mainfile] = replace_argument(data_mainfile[fl_pos_im_mainfile], 1,
                                                             'departamentos/fcfm')
        save_list_to_file(data_mainfile, subrlfolder + mainfile)

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')

    # Retorna a root
    os.chdir(mainroot)


# noinspection PyUnboundLocalVariable
def export_articulo(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                    plotstats=True, addstat=True, doclean=True,
                    savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta los articulos.

    :param addstat: Agrega las estadísticas
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_ARTICULO]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_reporte(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, printfun=nonprint, addstat=False, doclean=False, savepdf=False,
                   informeroot=informeroot, mainroot=mainroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')

    os.chdir(informeroot)
    mainf = RELEASES[REL_REPORTE]['FILES']
    files = release['FILES']
    files['main.tex'] = file_to_list('main_articulo.tex')
    files['template.tex'] = file_to_list('template_articulo.tex')
    files['src/cmd/articulo.tex'] = file_to_list('src/cmd/articulo.tex')
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_articulo.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'

    # Configuraciones que se borran
    cdel = ['hfpdashcharstyle', 'titlefontsize', 'titlefontstyle', 'titlelinemargin',
            'titleshowauthor', 'titleshowcourse', 'titleshowdate', 'titlesupmargin',
            'hfwidthcourse', 'hfwidthtitle', 'hfwidthwrap', 'disablehfrightmark']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    ra, rb = find_block(files[fl], 'pagemarginbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '1.91').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '1.27')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemarginright', True)
    nconf = replace_argument(files[fl][ra], 1, '1.27')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '1.91').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '9.5').replace(' %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'fontdocument', True)
    nconf = replace_argument(files[fl][ra], 1, 'libertine').replace('  %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'natbibrefstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'natsimpleurl').replace('      %', '%')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'stylecitereferences', True)
    nconf = replace_argument(files[fl][ra], 1, 'natbib')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'fontsizesubsubtitle', True)
    files[fl][ra] = files[fl][ra].replace(' {\\', '{\\')
    ra, rb = find_block(files[fl], 'documentinterline', True)
    nconf = replace_argument(files[fl][ra], 1, '1').replace('%', '    %')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'fontsizerefbibl', True)
    nconf = replace_argument(files[fl][ra], 1, '\\small').replace('%', '     %')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'natbibrefsep', True)
    nconf = replace_argument(files[fl][ra], 1, '3')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captiontextbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captionlrmarginmc', True)
    nconf = replace_argument(files[fl][ra], 1, '0.5').replace('  %', '%')
    files[fl][ra] = nconf

    ra, rb = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style1').replace('16 estilos', '17 estilos')
    files[fl][ra] = nconf + '\\def\\titleauthorspacing {0.35}     % Distancia entre autores [cm]\n' \
                            '\\def\\titleauthormaxwidth {0.85}    % Tamaño máximo datos autores [linewidth]\n' \
                            '\\def\\titlebold {true}              % Título en negrita\n' \
                            '\\def\\titlestyle {style1}           % Estilo título (5 estilos)\n'

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    cdel = ['University.Location', 'pdfsubject=',
            '\\def\\pdfmetainfoauthor {\\documentauthor}', '\\def\\pdfmetainfoauthor {}',
            '\\def\\pdfmetainfocoursename {\\coursename}',
            '\\def\\pdfmetainfocoursecode {\\coursecode}',
            '\\def\\pdfmetainfosubject {\\documentsubject}',
            '\\def\\pdfmetainfouniversitydepartment {\\universitydepartment}',
            '\\def\\pdfmetainfouniversityfaculty {\\universityfaculty}',
            '\\def\\pdfmetainfouniversity {\\universityname}',
            '\\def\\pdfmetainfouniversitylocation {\\universitylocation}',
            '\\def\\pdfmetainfocoursecode {}', '\\def\\pdfmetainfocoursename {}',
            '\\def\\pdfmetainfosubject {}', '\\def\\pdfmetainfouniversitydepartment {}',
            '\\def\\pdfmetainfouniversityfaculty {}',
            '\\def\\pdfmetainfouniversity {}', '\\def\\pdfmetainfouniversitylocation {}',
            'pdfauthor={\\pdfmetainfoauthor},', 'Course.Code', 'Course.Name', 'Document.Author',
            'Document.Subject', 'University.Department', 'University.Faculty', 'University.Name']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # Cambia autor
    # ra, _ = find_block(files[fl], 'pdfauthor={\\pdfmetainfoauthor},', True)
    # files[fl][ra] = files[fl][ra].replace('pdfmetainfoauthor', 'authorshf')

    ra, _ = find_block(files[fl], '% Operaciones especiales Template-Reporte')
    rb, _ = find_block(files[fl], '\\vskip \\titlelinemargin}')
    files[fl] = del_block_from_list(files[fl], ra - 1, rb + 1)

    new_defined = ['% Se revisa si las variables no han sido borradas\n',
                   '\\checkvardefined{\\documenttitle}\n']
    files[fl] = find_replace_block(files[fl], '% Se revisa si las variables no han sido borradas', new_defined,
                                   white_end_block=True, jadd=-2)

    new_defined = ['% Se añade \\xspace a las variables\n',
                   '% -----------------------------------------------------------------------------\n'
                   '\\makeatletter\n'
                   '\t\\g@addto@macro\\documenttitle\\xspace\n'
                   '\\makeatother\n']
    files[fl] = find_replace_block(files[fl], '% Se añade \\xspace a las variables', new_defined,
                                   white_end_block=True, jadd=-2)

    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-ARTC')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    # -------------------------------------------------------------------------
    # CAMBIO PAGECONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/page.tex'
    page_articulo = file_to_list('src/cfg/page_articulo.tex')
    nl = find_extract(page_articulo, '% Se crean los header-footer', white_end_block=True)
    files[fl] = find_replace_block(files[fl], '% Se crean los header-footer', nl, white_end_block=True,
                                   jadd=-1)
    ra, _ = find_block(files[fl], '% Se crean los header-footer')
    files[fl][ra] = files[fl][ra].replace('%', '\t%')

    # -------------------------------------------------------------------------
    # CAMBIO FINALCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/final.tex'
    # final_articulo = file_to_list('src/cfg/final_articulo.tex')
    # nl = find_extract(final_articulo, '% Define funciones generales', white_end_block=True)
    # nl[0] = '\t\t' + nl[0]
    ra, _ = find_block(files[fl], '% Define funciones generales')
    rb, _ = find_block(files[fl], '% No se encontró el header-footer, no hace nada')
    nl.pop()
    files[fl] = replace_block_from_list(files[fl], [], ra, rb)
    files[fl] = find_delete_block(files[fl], '% Actualiza headers', white_end_block=True, jadd=-1)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Articulo LaTeX\n'
            data[headersize - 3] = '% Manual template: [{0}]\n'.format(release['WEB']['MANUAL'])
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

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

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')
        clear_dict(RELEASES[REL_REPORTE], 'FILES')

    # Retorna a root
    os.chdir(mainroot)


# noinspection PyUnboundLocalVariable
def export_presentacion(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                        plotstats=True, addstat=True, doclean=True,
                        savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta la presentacion.

    :param addstat: Agrega las estadísticas
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_PRESENTACION]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_informe(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, printfun=nonprint, addstat=False, savepdf=False, informeroot=informeroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    mainf = RELEASES[REL_INFORME]['FILES']
    files = release['FILES']
    files['main.tex'] = file_to_list('main_presentacion.tex')
    files['template.tex'] = file_to_list('template_presentacion.tex')
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/presentacion.tex'] = file_to_list('src/cmd/presentacion.tex')
    files['src/etc/example.tex'] = file_to_list('src/etc/example_presentacion.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'
    distfolder = release['DIST']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'

    # Configuraciones que se borran
    cdel = ['predocpageromannumber', 'predocpageromanupper', 'predocresetpagenumber',
            'addemptypagetwosides', 'nomltfigure', 'nomltsrc', 'nomlttable', 'nomltcont', 'nomlteqn',
            'firstpagemargintop', 'nameportraitpage', 'fontsizessstitle', 'fontsizesubsubtitle',
            'fontsizesubtitle', 'fontsizetitle', 'fontsizetitlei', 'stylessstitle',
            'stylesubsubtitle', 'stylesubtitle', 'styletitle', 'styletitlei', 'ssstitlecolor',
            'subsubtitlecolor', 'subtitlecolor', 'indextitlecolor', 'portraittitlecolor',
            'titlecolor', 'ssstitlecolor', 'pdfcompileversion', 'bibtexenvrefsecnum',
            'bibtexindexbibliography', 'bibtextextalign', 'showlinenumbers', 'colorpage',
            'nomnpageof', 'nameappendixsection', 'apacitebothers', 'apaciterefnumber',
            'apaciterefsep', 'apaciterefcitecharclose', 'apaciterefcitecharopen',
            'apaciteshowurl', 'apacitestyle', 'appendixindepobjnum', 'sectionappendixlastchar',
            'twocolumnreferences', 'nomchapter', 'anumsecaddtocounter', 'fontsizerefbibl',
            'hfpdashcharstyle', 'nameabstract', 'margineqnindexbottom', 'margineqnindextop',
            'natbibrefcitecharclose', 'natbibrefcitecharopen', 'natbibrefcitecompress',
            'natbibrefcitesepcomma', 'natbibrefcitetype', 'natbibrefsep', 'natbibrefstyle'
            ]
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% MÁRGENES DE PÁGINA', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DE LOS TÍTULOS', white_end_block=True)
    for cdel in ['captionmarginimagesmc', 'captionmarginimages']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('    %', '%')  # Reemplaza espacio en comentarios de la lista
    for cdel in ['namemathcol', 'namemathdefn', 'namemathej',
                 'namemathlem', 'namemathobs', 'namemathprp', 'namemaththeorem',
                 'namereferences', 'nomltappendixsection', 'nomltwfigure',
                 'nomltwsrc', 'nomltwtable']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')
    for cdel in ['cfgpdfpageview', 'bibtexstyle', 'marginimagemultright']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace(' %', '%')
    for cdel in ['captiontextbold', 'captiontextsubnumbold', 'cfgpdffitwindow']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('%', ' %')
    for cdel in []:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('%', '  %')
    for cdel in ['documentinterline']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('%', '    %')
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    files[fl] = add_block_from_list(files[fl], [files[fl][ra],
                                                '\def\indexdepth {4}                % Profundidad de los marcadores\n'],
                                    ra, addnewline=True)
    for i in file_to_list('src/config_presentacion.tex'):
        files[fl].append(i)

    # ra, rb = find_block(files[fl], 'cfgpdflayout', True)
    # nconf = replace_argument(files[fl][ra], 1, 'SinglePage')
    # files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'cfgpdfpageview', True)
    nconf = replace_argument(files[fl][ra], 1, 'FitBV')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '10')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'bibtexstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'apalike')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'sourcecodenumbersep', True)
    nconf = replace_argument(files[fl][ra], 1, '3')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'documentparindent', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', ' %')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captionlrmarginmc', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captionlrmargin', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'documentinterline', True)
    nconf = replace_argument(files[fl][ra], 1, '1')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captiontextbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captiontextsubnumbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'cfgpdffitwindow', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'marginimagebottom', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.50')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'marginimagemultright', True)
    nconf = replace_argument(files[fl][ra], 1, '0.35')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captionmarginimagesmc', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.04')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'captionmarginimages', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.04')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'sourcecodefonts', True)
    nconf = replace_argument(files[fl][ra], 1, '\\footnotesize').replace(' {', '{').replace('      %', '%')
    files[fl][ra] = nconf

    ra, _ = find_block(files[fl], 'stylecitereferences', True)
    files[fl][ra] = '\\def\\stylecitereferences {bibtex}  % Estilo cita/ref {bibtex,custom}\n'
    ra, _ = find_block(files[fl], 'captionfontsize', True)
    files[fl][ra] = '\\def\\captionfontsize{footnotesize} % Tamaño de fuente de los caption\n'
    # files[fl].pop()

    ra, _ = find_block(files[fl], 'fonturl', True)
    files[fl][ra] += '\\def\\frametextjustified {true}     % Justifica todos los párrafos de los frames\n'

    # -------------------------------------------------------------------------
    # CAMBIA LAS ECUACIONES
    # -------------------------------------------------------------------------
    fl = 'src/cmd/equation.tex'
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA LOS TÍTULOS
    # -------------------------------------------------------------------------
    fl = 'src/cmd/title.tex'
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = 'src/env/environments.tex'
    files[fl] = find_delete_block(files[fl], '% Crea una sección de resumen', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea una sección de referencias solo para bibtex', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea una sección de anexos', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA OTROS
    # -------------------------------------------------------------------------
    fl = 'src/cmd/other.tex'
    files[fl] = find_delete_block(files[fl], '% Cambia el tamaño de la página', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Ofrece diferentes formatos de pagina', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['xcolor', 'hyperref', 'sectsty', 'tocloft', 'notoccite', 'titlesec',
            'graphicx']
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% Dimensiones y geometría del documento', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Cambia el estilo de los títulos', white_end_block=True)
    ra, _ = find_block(files[fl], '% Agrega punto a títulos/subtítulos', True)
    files[fl][ra] = '% Agrega punto a títulos/subtítulos\n\\def\\showdotaftersnum {true}\n'
    ra, _ = find_block(files[fl], '\showappendixsecindex')
    nl = ['\\def\\showappendixsecindex {false}\n',
          files[fl][ra]]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    ra, _ = find_block(files[fl], '% Muestra los números de línea')
    nl = ['}\n\\def\\showlinenumbers {true}\n',
          '\\ifthenelse{\\equal{\\showlinenumbers}{true}}{ % Muestra los números de línea\n']
    files[fl] = replace_block_from_list(files[fl], nl, ra - 1, ra - 1)

    files[fl].pop()
    files[fl].append('\\usefonttheme{professionalfonts}\n\\usepackage{transparent}\n')

    ra, _ = find_block(files[fl], '% Desde v6.2.8 se debe cargar al final para evitar errores:')
    rb, _ = find_block(files[fl], '% Anexos/Apéndices')
    nl = ['\\usepackage[pdfencoding=auto,psdextra]{hyperref}\n']
    files[fl] = replace_block_from_list(files[fl], nl, ra, rb - 3)

    ra, _ = find_block(files[fl], '% En v6.3.7 se desactiva cellspace', True)
    rb, _ = find_block(files[fl], '% \usepackage{subfigure}', True)
    files[fl] = del_block_from_list(files[fl], ra, rb + 1)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_presentacion = file_to_list('src/cfg/init_presentacion.tex')

    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Agrega compatibilidad de sub-sub-sub-secciones al TOC', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Se crean variables si se borraron', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Actualización margen títulos', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Se añade listings (código fuente) a tocloft', True, iadd=-2)
    files[fl] = find_delete_block(files[fl], '\pdfminorversion', white_end_block=True, iadd=-1)

    # Borra línea definiciones
    ra, _ = find_block(files[fl], '\checkvardefined{\\universitydepartmentimagecfg}')
    files[fl].pop(ra)

    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-PRES')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))
    for i in ['\\author{\\pdfmetainfoauthor}', '\\title{\\pdfmetainfotitle}',
              '\\checkvardefined{\\documenttitle}', '\g@addto@macro\\documenttitle']:
        ra, _ = find_block(files[fl], i)
        files[fl].pop(ra)

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    # Elimina subtitulo
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\documentsubtitle}{}}{', jadd=1)

    # Índice de ecuaciones
    files[fl] = find_delete_block(files[fl], '% Crea índice de ecuaciones', white_end_block=True, iadd=-1, jadd=-1)

    # Color de página
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\colorpage}{white}}{}{', white_end_block=True,
                                  jadd=-1)

    # Cambia las bibliografias
    nl = find_extract(init_presentacion, '% Configuración de referencias y citas', white_end_block=True)
    ra, _ = find_block(files[fl], '% Configuración de referencias y citas')
    _, rb = find_block(files[fl], '% Referencias en 2 columnas', blankend=True)
    files[fl] = replace_block_from_list(files[fl], nl, ra, rb - 1)

    ra, _ = find_block(files[fl], 'Sloppy arruina portadas al exigir', True)
    files[fl].pop(ra)

    ra, _ = find_block(files[fl], '\\setcounter{secnumdepth}{4}', True)
    files[fl][ra] += '\n'

    files[fl].pop()

    # Inserta bloques
    for i in ['% Justificación de textos',
              '% Word-break en citas',
              '% Corrige espaciamiento de itemize',
              '% Cambios generales en presentación',
              '% Configura los bloques',
              '% Definición de entornos beamer',
              '% Reinicia número de subfiguras y subtablas',
              '% Configura footnotes']:
        nl = find_extract(init_presentacion, i, white_end_block=True)
        nl.insert(0, '% -----------------------------------------------------------------------------\n')
        for j in nl:
            files[fl].append(j)

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/page.tex'
    aux_pageconf = file_to_list('src/cfg/page_presentacion.tex')
    nl = find_extract(aux_pageconf, '% Numeración de páginas', True)
    files[fl] = find_replace_block(files[fl], '% Numeración de páginas', nl, white_end_block=True, jadd=-1)
    nl = find_extract(aux_pageconf, '% Estilo de títulos', True)
    files[fl] = find_replace_block(files[fl], '% Estilo de títulos', nl, white_end_block=True, jadd=-1)
    nl = find_extract(aux_pageconf, '% Definición de nombres de objetos', True)
    files[fl] = find_replace_block(files[fl], '% Definición de nombres de objetos', nl, white_end_block=True, jadd=-1)
    files[fl] = find_delete_block(files[fl], '% Se crean los header-footer', white_end_block=True, jadd=-1, iadd=-2)
    ra, _ = find_block(files[fl], '\\setpagemargincm{\\pagemarginleft}')
    files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% Muestra los números de línea', white_end_block=True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Estilo citas', white_end_block=True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Estilo de títulos', white_end_block=True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Configura el nombre del abstract', white_end_block=True, iadd=-1)
    ra, _ = find_block(files[fl], '% Márgenes de páginas y tablas')
    files[fl][ra] = files[fl][ra].replace('páginas y ', '')

    # -------------------------------------------------------------------------
    # FINALCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/final.tex'
    files[fl] = find_delete_block(files[fl], '% Se usa número de páginas en arábigo', white_end_block=True, jadd=-1,
                                  iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Reinicia número de página', white_end_block=True, jadd=-1, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Estilo de títulos - restablece estilos por el índice',
                                  white_end_block=True, jadd=-1, iadd=-2)
    files[fl] = find_delete_block(files[fl], 'Establece el estilo de las sub-sub-sub-secciones', white_end_block=True,
                                  jadd=-1, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Se restablecen headers y footers', white_end_block=True, jadd=-1,
                                  iadd=-1)
    ra, _ = find_block(files[fl], '% Crea funciones para numerar objetos')
    files[fl].pop(ra - 2)
    ra, _ = find_block(files[fl], '% Se restablecen números de página y secciones')
    files[fl][ra + 1] = '\t% -------------------------------------------------------------------------\n'
    files[fl] = find_delete_block(files[fl], '% Muestra los números de línea', white_end_block=True, jadd=1,
                                  iadd=-1)

    # -------------------------------------------------------------------------
    # CAMBIA TÍTULOS
    # -------------------------------------------------------------------------
    fl = 'src/cmd/title.tex'
    files[fl] = find_delete_block(files[fl], '% Crear un capítulo como una sección', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea una sección en el índice y en el header', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título en un índice, con número de página',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título en un índice, sin número de página',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-sub-subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl],
                                  '% Insertar un título sin número, sin indexar y sin cambiar el título del header',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título sin número',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un subtítulo sin número',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-subtítulo sin número',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-sub-subtítulo sin número',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Cambia el título del encabezado (header)',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Elimina el título del encabezado (header)',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título sin número sin cambiar el título del header',
                                  white_end_block=True)

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '\\newcommand{\\bgtemplatetestimg}{')
    files[fl] = find_delete_block(files[fl], '\def\\bgtemplatetestcode {d0g3}', white_end_block=True)
    # files[fl] = find_delete_block(files[fl], '% Cambia los márgenes del documento', white_end_block=True, jadd=1)
    files[fl] = find_delete_block(files[fl], '% Cambia márgenes de las páginas [cm]', white_end_block=True)
    ra, _ = find_block(files[fl], '% Imagen de prueba tikz')
    files[fl].pop(ra)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Presentación LaTeX\n'
            data[headersize - 3] = '% Manual template: [{0}]\n'.format(release['WEB']['MANUAL'])
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

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

        # Se exportan los distintos estilos de versiones
        data_mainfile = file_to_list(subrlfolder + mainfile)

        # Se buscan las líneas del departamento y de la imagen
        fl_pos_dp_mainfile = find_line(data_mainfile, '\def\universitydepartment')
        fl_pos_im_mainfile = find_line(data_mainfile, '\def\universitydepartmentimage')

        # Se recorre cada versión y se genera el .zip
        for m in DEPTOS:
            data_mainfile[fl_pos_dp_mainfile] = '\\def\\universitydepartment {' + m[0] + '}\n'
            data_mainfile[fl_pos_im_mainfile] = '\\def\\universitydepartmentimage {departamentos/' + m[1] + '}\n'

            # Se reescriben los archivos
            save_list_to_file(data_mainfile, subrlfolder + mainfile)

            # Se genera el .zip
            czip = release['ZIP']['NORMAL']
            export_normal = Zip(release['ZIP']['OTHERS']['NORMAL'].format(m[1]))
            with Cd(subrlfolder):
                export_normal.set_ghostpath(distfolder)
                export_normal.add_excepted_file(czip['EXCEPTED'])
                export_normal.add_file(czip['ADD']['FILES'])
                export_normal.add_folder(release['ZIP']['OTHERS']['EXPATH'])
                export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(m[1]))
                for k in m[2]:
                    export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(k))
            export_normal.save()

        # Rollback archivo principal. Necesario para subtemplates
        data_mainfile[fl_pos_dp_mainfile] = replace_argument(data_mainfile[fl_pos_dp_mainfile], 1,
                                                             'Departamento de la Universidad')
        data_mainfile[fl_pos_im_mainfile] = replace_argument(data_mainfile[fl_pos_im_mainfile], 1,
                                                             'departamentos/fcfm')
        save_list_to_file(data_mainfile, subrlfolder + mainfile)

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')

    # Retorna a root
    os.chdir(mainroot)


# noinspection PyBroadException
def export_cv(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
              plotstats=False, doclean=True, addstat=True, savepdf=True,
              mainroot=None, backtoroot=False, statsroot=None):
    """
    Exporta Professional-CV.

    :param addstat: Añade estadísticas
    :param backtoroot: Devuelve al root
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
    :return: None
    """
    # Tipo release
    reltag = REL_PROFESSIONALCV
    release = RELEASES[reltag]

    # Se cambia de carpeta
    os.chdir(release['ROOT'])

    # Obtiene archivos
    configfile = 'src/config.tex'
    files = release['FILES']
    initconffile = 'src/initconf.tex'
    mainfile = release['MAINFILE']
    stat = release['STATS']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
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
    l_tdate, d_tdate = find_line(initconf_data, 'Template.Date', True)
    l_thash, d_thash = find_line(initconf_data, 'Template.Version.Hash', True)
    l_ttype, d_ttype = find_line(initconf_data, 'Template.Type', True)
    l_tvdev, d_tvdev = find_line(initconf_data, 'Template.Version.Dev', True)
    l_tvrel, d_tvrel = find_line(initconf_data, 'Template.Version.Release', True)
    l_vcmtd, d_vcmtd = find_line(initconf_data, 'pdfproducer', True)
    initconf_data.close()

    # Se actualizan líneas de hyperref
    d_tdate = replace_argument(d_tdate, 1, dia)
    d_thash = replace_argument(d_thash, 1, versionhash)
    d_ttype = replace_argument(d_ttype, 1, 'Normal')
    d_tvdev = replace_argument(d_tvdev, 1, versiondev)
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
        # Mueve el archivo de configuraciones
        copyfile(configfile, 'template_config.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['source_template.tex'], configfile, '', headersize, files)

    printfun(MSG_FOKTIMER.format(time.time() - t))

    # Compila el archivo
    if docompile and dosave:
        compile_template(None, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

    # Se exporta el proyecto normal
    if dosave:
        czip = release['ZIP']['NORMAL']
        export_normal = Zip(mainroot + czip['FILE'])
        export_normal.add_excepted_file(czip['EXCEPTED'])
        export_normal.add_file(czip['ADD']['FILES'])
        export_normal.add_folder(czip['ADD']['FOLDER'])
        export_normal.save()

    # Se borra la información generada en las listas
    if doclean:
        clear_dict(RELEASES[reltag], 'FILES')

    # Se cambia a carpeta root
    if backtoroot:
        os.chdir(mainroot)


# noinspection PyUnboundLocalVariable
def export_tesis(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                 plotstats=True, addstat=True, doclean=True,
                 savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta las tesis.

    :param addstat: Agrega las estadísticas
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
    :return: None
    """
    # Tipo release
    release = RELEASES[REL_TESIS]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_informe(version, versiondev, versionhash, dosave=False, docompile=False,
                   plotstats=False, printfun=nonprint, addstat=False, savepdf=False, informeroot=informeroot)

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')
    mainf = RELEASES[REL_INFORME]['FILES']
    files = release['FILES']
    files['main.tex'] = file_to_list('main_tesis.tex')
    files['template.tex'] = file_to_list('template_tesis.tex')
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/page/portrait.tex'] = file_to_list('src/page/portrait_tesis.tex')
    files['src/page/index.tex'] = copy.copy(mainf['src/page/index.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_tesis.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'
    distfolder = release['DIST']

    # Constantes
    main_data = open(mainfile)
    main_data.read()
    # initdocumentline = find_line(main_data, '\\usepackage[utf8]{inputenc}') + 1
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'
    main_data.close()

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'

    # Añade configuraciones
    cfg = '\\def\\objectchaptermargin {false}   % Activa margen de objetos entre capítulos\n'
    ra, _ = find_block(files[fl], 'objectindexindent', True)
    nl = [cfg, files[fl][ra]]
    files[fl] = add_block_from_list(files[fl], nl, ra)

    # Modifica configuraciones
    ra, _ = find_block(files[fl], 'addemptypagetwosides', True)
    files[fl][ra] = '\\def\\addemptypagespredoc {false}   % Añade pag. en blanco después de portada,etc.\n'
    ra, _ = find_block(files[fl], 'showsectioncaptioncode', True)
    nconf = replace_argument(files[fl][ra], 1, 'chap')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showsectioncaptioneqn', True)
    nconf = replace_argument(files[fl][ra], 1, 'chap')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showsectioncaptionfig', True)
    nconf = replace_argument(files[fl][ra], 1, 'chap')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showsectioncaptionmat', True)
    nconf = replace_argument(files[fl][ra], 1, 'chap')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showsectioncaptiontab', True)
    nconf = replace_argument(files[fl][ra], 1, 'chap')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentinterline', True)
    nconf = replace_argument(files[fl][ra], 1, '1.0').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '2').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontsizetitle', True)
    nconf = replace_argument(files[fl][ra], 1, '\\Large')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontsizesubtitle', True)
    nconf = replace_argument(files[fl][ra], 1, '\\large')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontsizesubsubtitle', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'indexstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'tf').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '12')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '3').replace('%', '   %')
    nl = [nconf,
          '\\def\\pagemarginleftportrait {2.5}  % Margen izquierdo página portada [cm]\n']
    files[fl] = add_block_from_list(files[fl], nl, ra)
    ra, _ = find_block(files[fl], 'pagemarginright', True)
    nconf = replace_argument(files[fl][ra], 1, '2').replace('%', '   %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\pagemargintop', True)  # Por alguna extraña razón requiere el \\
    nconf = replace_argument(files[fl][ra], 1, '2')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style7')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgbookmarksopenlevel', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    # ra, _ = find_block(files[fl], 'cfgpdfsecnumbookmarks', True)
    # nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    # files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'addindexsubtobookmarks', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('{', ' {')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showappendixsecindex', True)
    nconf = replace_argument(files[fl][ra], 1, 'false')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    # ra, _ = find_block(files[fl], 'natbibrefstyle', True)
    # nconf = replace_argument(files[fl][ra], 1, 'plainnat').replace('  %', '%')
    # files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'stylecitereferences', True)
    nconf = replace_argument(files[fl][ra], 1, 'natbib')
    files[fl][ra] = nconf
    # ra, _ = find_block(files[fl], 'addindextobookmarks', True)
    # nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    # files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'addindexsubtobookmarks', True)
    nl = ['\\def\\addabstracttobookmarks {true} % Añade el resumen a los marcadores del pdf\n',
          '\\def\\addagradectobookmarks {true}  % Añade el agradecimiento a los marcadores\n',
          files[fl][ra],
          # '\\def\\adddedictobookmarks {true}    % Añade la dedicatoria a los marcadores del pdf\n'
          ]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra - 1)
    ra, _ = find_block(files[fl], 'namereferences', True)
    nconf = replace_argument(files[fl][ra], 1, 'Bibliografía').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'nomltcont', True)
    nconf = replace_argument(files[fl][ra], 1, 'Tabla de Contenido').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'footnotepagetoprule', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'nomltfigure', True)
    nconf = replace_argument(files[fl][ra], 1, 'Índice de Ilustraciones').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'nameabstract', True)
    nl = [files[fl][ra],
          '\\def\\nameagradec {Agradecimientos}    % Nombre del cap. de agradecimientos\n',
          # '\\def\\nameadedic {Dedicatoria}         % Nombre de la dedicatoria\n'
          ]
    files[fl] = add_block_from_list(files[fl], nl, ra, True)

    # Configuraciones que se borran
    cdel = ['portraitstyle', 'firstpagemargintop', 'bibtexenvrefsecnum',
            'predocpageromannumber', 'predocresetpagenumber', 'indexnewpagec', 'indexnewpagef',
            'indexnewpaget', 'showindexofcontents', 'fontsizetitlei', 'styletitlei', 'indexnewpagee',
            'hfpdashcharstyle', 'portraittitlecolor']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    for cdel in []:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    ra, _ = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl][ra] = '% ESTILO HEADER-FOOTER\n'

    # Añade nuevas entradas
    files[fl] = search_append_line(files[fl], '% CONFIGURACIÓN DE LOS COLORES DEL DOCUMENTO',
                                   '\\def\\chaptercolor {black}          % Color de los capítulos\n')
    files[fl] = search_append_line(files[fl], 'anumsecaddtocounter',
                                   '\\def\\fontsizechapter {\\huge}       % Tamaño fuente de los capítulos\n')
    files[fl] = search_append_line(files[fl], 'showdotaftersnum',
                                   '\\def\\stylechapter {\\bfseries}      % Estilo de los capítulos\n')
    files[fl] = search_append_line(files[fl], '% ESTILO HEADER-FOOTER',
                                   '\\def\\chapterstyle {style1}         % Estilo de los capítulos (12 estilos)\n')
    files[fl] = search_append_line(files[fl], '\\senumertiv',
                                   '\\def\\showabstracttable {false}     % Muestra tabla superior derecha de resumen\n')

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['ragged2e']
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl].pop()
    a, _ = find_block(files[fl], '\\usepackage{apacite}', True)
    files[fl][a] = files[fl][a].replace('{apacite}', '[nosectionbib]{apacite}')

    ra, _ = find_block(files[fl], '% En v6.3.7 se desactiva cellspace', True)
    rb, _ = find_block(files[fl], '% \usepackage{subfigure}', True)
    files[fl] = del_block_from_list(files[fl], ra, rb + 1)

    ra, _ = find_block(files[fl], '% Desde v6.2.8 se debe cargar al final para evitar errores:', True)
    rb, _ = find_block(files[fl], '% Desde v6.5.6 se carga después de las referencias ', True)
    files[fl] = del_block_from_list(files[fl], ra, rb)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_tesis = file_to_list('src/cfg/init_tesis.tex')

    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Se crean variables si se borraron', True, iadd=-1)
    ra, _ = find_block(files[fl], '\checkvardefined{\coursecode}', True)

    # Añade bloque de variables definidas
    nl = find_extract(init_tesis, '% Inicialización de variables', white_end_block=True)
    nl.pop(0)
    nl.append(files[fl][ra])
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)
    # ra, _ = find_block(files[fl], 'pdfkeywords', True)
    # files[fl][ra] = '\tpdfkeywords={pdf, \\universityname, \\universitylocation},\n'

    # Elimina referencias en dos columnas
    # files[fl] = find_delete_block(files[fl], '% Referencias en 2 columnas', True)
    ra, _ = find_block(files[fl], '{\\begin{multicols}{2}[\section*{\\refname}', True)
    files[fl][ra] = '\t{\\begin{multicols}{2}[\\chapter*{\\refname}]\n'

    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-THS')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    # Cambia section por chapter en la redefinición de bibliography
    ra, _ = find_block(files[fl], '% bibtex tesis en chapter')
    files[fl][ra] = replace_argument(files[fl][ra], 2, 'chapter')

    # Corrige footnotes
    ra, _ = find_block(files[fl], 'counterwithout*{footnote}{chapter}')
    files[fl][ra] = files[fl][ra].replace('% ', '')

    # Agrega estilos de capítulos
    files[fl].pop()
    nl = find_extract(init_tesis, '% Estilos de capítulos', white_end_block=True)
    nl.insert(0, '% -----------------------------------------------------------------------------\n')
    for i in nl:
        files[fl].append(i)

    # Agrega saltos de líneas
    for i in ['% Crea referencias enumeradas en apacite', '% Desactiva la URL de apacite',
              '% Referencias en 2 columnas']:
        ra, _ = find_block(files[fl], i)
        files[fl][ra] = '\n' + files[fl][ra]

    # -------------------------------------------------------------------------
    # ÍNDICE
    # -------------------------------------------------------------------------
    fl = 'src/page/index.tex'
    index_tesis = file_to_list('src/page/index_tesis.tex')

    # Agrega inicial
    ra, _ = find_block(files[fl], 'Crea nueva página y establece estilo de títulos', True)
    nl = find_extract(index_tesis, '% Inicio índice, desactiva espacio entre objetos', True)
    files[fl] = add_block_from_list(files[fl], nl, ra - 2)

    ra, _ = find_block(files[fl], 'Se añade una página en blanco', True)
    nl = find_extract(index_tesis, '% Final del índice, restablece el espacio', True)
    files[fl] = add_block_from_list(files[fl], nl, ra - 2)

    for j in ['% Inicio índice, desactiva espacio entre objetos', '% Final del índice, restablece el espacio']:
        ra, _ = find_block(files[fl], j, True)
        files[fl].insert(ra, '\n\t% -------------------------------------------------------------------------\n')

    w = '% Configuración del punto en índice'
    nl = find_extract(index_tesis, w, True)
    nl.append('\t% -------------------------------------------------------------------------\n')
    files[fl] = find_replace_block(files[fl], w, nl, True)
    w = '% Cambia tabulación índice de objetos para alinear con contenidos'
    nl = find_extract(index_tesis, w, True)
    nl.append('\t% -------------------------------------------------------------------------\n')
    files[fl] = find_replace_block(files[fl], w, nl, True)

    # Cambia belowpdfbookmark
    ra, _ = find_block(files[fl], 'belowpdfbookmark', True)
    files[fl][ra] = files[fl][ra].replace('belowpdfbookmark', 'pdfbookmark')

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/page.tex'
    page_tesis = file_to_list('src/cfg/page_tesis.tex')
    # ra, _ = find_block(files[fl], '\\renewcommand{\\refname}', True)
    # nl = [files[fl][ra], '\\renewcommand{\\bibname}{\\namereferences}\n']
    # files[fl] = replace_block_from_list(files[fl], nl, ra, ra - 1)
    ra, _ = find_block(files[fl], '\\renewcommand{\\appendixtocname}{\\nameappendixsection}')
    files[fl] = add_block_from_list(files[fl], [files[fl][ra],
                                                '\t\\renewcommand{\chaptername}{\\nomchapter}  % Nombre de los capítulos\n'],
                                    ra)
    ra, rb = find_block(files[fl], '% Muestra los números de línea', True)
    nl = find_extract(page_tesis, '% Añade página en blanco')
    files[fl] = add_block_from_list(files[fl], nl, rb, True)

    files[fl] = search_append_line(files[fl], '\\sectionfont{\\color',
                                   '\t\\chaptertitlefont{\\color{\\chaptercolor} \\fontsizechapter \\stylechapter \\selectfont}\n')

    ra, _ = find_block(files[fl], '% Configura el nombre del abstract', True)
    files[fl].insert(ra - 1, '\n')

    # -------------------------------------------------------------------------
    # ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = 'src/env/environments.tex'
    env_tesis = file_to_list('src/env/environments_tesis.tex')

    # Reemplaza bloques
    w = '% Crea una sección de referencias solo para bibtex'
    nl = find_extract(env_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True)
    w = '% Crea una sección de resumen'
    nl = find_extract(env_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True, jadd=-1)
    _, rb = find_block(files[fl], w, True)
    nl = find_extract(env_tesis, '% Crea una sección de dedicatoria', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)
    _, rb = find_block(files[fl], '% Crea una sección de dedicatoria', True)
    nl = find_extract(env_tesis, '% Crea una sección de agradecimientos', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)

    # Agrega saltos de línea
    for w in ['% Llama al entorno de resumen', '% Crea una sección de dedicatoria',
              '% Crea una sección de agradecimientos']:
        ra, _ = find_block(files[fl], w, True)
        files[fl][ra] = '\n' + files[fl][ra]

    # Reemplaza líneas
    ra, _ = find_block(files[fl], 'counterwithin{equation}')
    files[fl][ra] = '\t\t\t\\counterwithin{equation}{chapter}\n'
    ra, _ = find_block(files[fl], 'counterwithin{figure}')
    files[fl][ra] = '\t\t\t\\counterwithin{figure}{chapter}\n'
    ra, _ = find_block(files[fl], 'counterwithin{lstlisting}')
    files[fl][ra] = '\t\t\t\\counterwithin{lstlisting}{chapter}\n'
    ra, _ = find_block(files[fl], 'counterwithin{table}')
    files[fl][ra] = '\t\t\t\\counterwithin{table}{chapter}\n'

    # Cambia valor de anexos sección
    ra, _ = find_block(files[fl], 'GLOBALsectionalph')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'false')

    # Reemplaza nueva linea en agradecimientos
    # ra, _ = find_block(files[fl], '% EMPTYLINE')
    # files[fl][ra] = '\n'

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '% Imagen de prueba tikz', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Para la compatibilidad con template-tesis se define el capítulo',
                                  white_end_block=True)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Tesis LaTeX\n'
            data[headersize - 3] = '% Manual template: [{0}]\n'.format(release['WEB']['MANUAL'])
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
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
            dostrip = False
            if f == configfile or f == mainfile or f == examplefile or '-config' in f:
                dostrip = False

            # Se escribe el documento
            paste_external_tex_into_file(fl, f, files, headersize, STRIP_ALL_GENERATED_FILES and dostrip, dostrip,
                                         True, configfile, False, dist=True, add_ending_line=False and dostrip)

            # Se elimina la última linea en blanco si hay doble
            fl.close()

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, lc, versionhash, plotstats)

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

        # Se exportan los distintos estilos de versiones
        data_mainfile = file_to_list(subrlfolder + mainfile)

        # Se buscan las líneas del departamento y de la imagen
        fl_pos_dp_mainfile = find_line(data_mainfile, '\def\universitydepartment')
        fl_pos_im_mainfile = find_line(data_mainfile, '\def\universitydepartmentimage')

        # Se recorre cada versión y se genera el .zip
        for m in DEPTOS:
            data_mainfile[fl_pos_dp_mainfile] = '\\def\\universitydepartment {' + m[0] + '}\n'
            data_mainfile[fl_pos_im_mainfile] = '\\def\\universitydepartmentimage {departamentos/uchile2}\n'

            # Se reescriben los archivos
            save_list_to_file(data_mainfile, subrlfolder + mainfile)

            # Se genera el .zip
            czip = release['ZIP']['NORMAL']
            export_normal = Zip(release['ZIP']['OTHERS']['NORMAL'].format(m[1]))
            with Cd(subrlfolder):
                export_normal.set_ghostpath(distfolder)
                export_normal.add_excepted_file(czip['EXCEPTED'])
                export_normal.add_file(czip['ADD']['FILES'])
                export_normal.add_folder(release['ZIP']['OTHERS']['EXPATH'])
                export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(m[1]))
                for k in m[2]:
                    export_normal.add_file(release['ZIP']['OTHERS']['IMGPATH'].format(k))
            export_normal.save()

        # Rollback archivo principal. Necesario para subtemplates
        data_mainfile[fl_pos_dp_mainfile] = replace_argument(data_mainfile[fl_pos_dp_mainfile], 1,
                                                             'Departamento de la Universidad')
        data_mainfile[fl_pos_im_mainfile] = replace_argument(data_mainfile[fl_pos_im_mainfile], 1,
                                                             'departamentos/uchile2')
        save_list_to_file(data_mainfile, subrlfolder + mainfile)

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')

    # Retorna a root
    os.chdir(mainroot)
