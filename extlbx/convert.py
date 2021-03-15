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
    configfile = release['CONFIGFILE']
    examplefile = release['EXAMPLEFILE']
    files = release['FILES']
    initconffile = release['INITCONFFILE']
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
            dostrip = True
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
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t1 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t2 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t3 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t4 = time.time() - t
            # tmean = (t1 + t2) / 2
            tmean = min(t1, t2, t3, t4)
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
        fl_pos_dp_mainfile = find_line(data_mainfile, '\def\departamentouniversidad')
        fl_pos_im_mainfile = find_line(data_mainfile, '\def\imagendepartamento')

        # Se recorre cada versión y se genera el .zip
        for m in DEPTOS:
            data_mainfile[fl_pos_dp_mainfile] = '\\def\\departamentouniversidad {' + m[0] + '}\n'
            data_mainfile[fl_pos_im_mainfile] = '\\def\\imagendepartamento {departamentos/' + m[1] + '}\n'

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
    # files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = file_to_list('src/cmd/auxiliar_title.tex')
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/auxiliar.tex'] = file_to_list('src/cmd/auxiliar.tex')
    files['src/etc/example.tex'] = file_to_list('src/etc/example_auxiliar.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']

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
    for j in range(len(files[mainfile])):
        if get_file_from_input(files[mainfile][j]) == examplefile:
            files[mainfile][j] = '\input{example} % Ejemplo, se puede borrar\n'
    ra = find_line(files[mainfile], 'imagendepartamentoparams')
    files[mainfile][ra] = replace_argument(files[mainfile][ra], 1, 'height=1.75cm')

    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIIONES
    # -------------------------------------------------------------------------
    fl = release['CONFIGFILE']

    # Configuraciones que se borran
    cdel = ['addemptypagetwosides', 'nomlttable', 'nomltsrc', 'nomltfigure',
            'nomltcont', 'nameportraitpage', 'indextitlecolor',
            'portraittitlecolor', 'fontsizetitlei', 'styletitlei',
            'firstpagemargintop', 'romanpageuppercase', 'showappendixsecindex',
            'nomchapter', 'nomnpageof', 'indexforcenewpage', 'predocpageromannumber',
            'predocresetpagenumber', 'margineqnindexbottom', 'margineqnindextop', 'nomlteqn',
            'bibtexindexbibliography']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    ra, rb = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl] = del_block_from_list(files[fl], ra, rb)
    for cdel in ['namereferences', 'nomltwsrc', 'nomltwfigure', 'nomltwtable', 'nameappendixsection',
                 'nomltappendixsection', 'namemathcol', 'namemathdefn', 'namemathej', 'namemathlem',
                 'namemathobs', 'namemathprp', 'namemaththeorem', 'nameabstract']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    # ra, rb = find_block(files[fl], 'showdotaftersnum', True) Desactivado desde v3.3.4
    # nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    # files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'equationrestart', True)
    nconf = replace_argument(files[fl][ra], 1, 'none')
    files[fl][ra] = nconf
    ra, rb = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.30').replace(' %', '%')
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
    fl = release['EQNFILE']
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
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
    # files[fl] = find_delete_block(files[fl], '% Importa la librería tikz', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
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
    files[fl][ra] = '\t\def\\equipodocente {}}{\n'

    ra, _ = find_block(files[fl], '\pdfmetainfotitulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloauxiliar')
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], '\setcounter{tocdepth}')
    files[fl][ra] = replace_argument(files[fl][ra], 2, '1')
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    files[fl] = find_delete_block(files[fl], '% Se añade listings a tocloft', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Se revisa si se importa tikz', white_end_block=True)

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
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
    a, _ = find_block(files[fl], '\\titleclass{\subsubsubsection}{straight}[\subsection]')
    files[fl].pop()
    files[fl].append(files[fl].pop(a))

    # -------------------------------------------------------------------------
    # AUXILIAR FUNCTIONS
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
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

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t3 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t4 = time.time() - t
                # tmean = (t1 + t2) / 2
                tmean = min(t1, t2, t3, t4)
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
    # files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/control.tex'] = copy.copy(mainf['src/cmd/auxiliar.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_control.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']

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
    main_auxiliar = file_to_list(subrelfile['MAIN'])
    nb = find_extract(main_auxiliar, '% EQUIPO DOCENTE')
    nb.append('\n')
    files[mainfile] = find_replace_block(files[mainfile], '% EQUIPO DOCENTE', nb)
    ra = find_line(files[mainfile], 'tituloauxiliar')
    files[mainfile][ra] = '\def\\tituloevaluacion {Título del Control}\n'
    ra = find_line(files[mainfile], 'temaatratar')
    files[mainfile][ra] = '\def\indicacionevaluacion {\\textbf{INDICACIÓN DEL CONTROL}} % Opcional\n'
    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # -------------------------------------------------------------------------
    # CONTROL
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # PAGECONFFILE
    # -------------------------------------------------------------------------
    fl = release['PAGECONFFILE']
    control_pageconf = file_to_list(subrelfile['PAGECONF'])
    nl = find_extract(control_pageconf, '% Se crean los header-footer', True)
    files[fl] = find_replace_block(files[fl], '% Se crean los header-footer', nl, white_end_block=True, jadd=-1)

    # -------------------------------------------------------------------------
    # CONFIGS
    # -------------------------------------------------------------------------
    fl = release['CONFIGFILE']
    ra = find_line(files[fl], 'anumsecaddtocounter')
    files[fl][ra] += '\def\\bolditempto {true}            % Puntaje item en negrita\n'
    cdel = ['templatestyle']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
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

    ra, _ = find_block(files[fl], '\pdfmetainfotitulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloevaluacion')
    ra, _ = find_block(files[fl], '\pdfmetainfotema')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\tituloevaluacion')
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-CTR/EXM')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))
    ra, _ = find_block(files[fl], 'Documento.Tema')
    files[fl].pop(ra)

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

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t3 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t4 = time.time() - t
                # tmean = (t1 + t2) / 2
                tmean = min(t1, t2, t3, t4)
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
    files['src/etc/example.tex'] = file_to_list('src/etc/example_reporte.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']
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
    main_reporte = file_to_list(subrelfile['MAIN'])
    nb = find_extract(main_reporte, '% EQUIPO DOCENTE')
    nb.append('\n')
    files[mainfile] = find_delete_block(files[mainfile], '% INTEGRANTES, PROFESORES Y FECHAS', nb)
    files[mainfile][1] = '% Documento:    Archivo principal\n'
    files[mainfile] = find_delete_block(files[mainfile], '% PORTADA', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% RESUMEN O ABSTRACT', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% TABLA DE CONTENIDOS - ÍNDICE', white_end_block=True)
    files[mainfile] = find_delete_block(files[mainfile], '% IMPORTACIÓN DE ENTORNOS', white_end_block=True)
    ra, _ = find_block(files[mainfile], '\input{src/etc/example}', True)
    files[mainfile] = add_block_from_list(files[mainfile], main_reporte, ra, addnewline=True)
    ra, _ = find_block(files[mainfile], 'imagendepartamentoparams', True)
    files[mainfile].pop(ra)
    # files[mainfile][len(files[mainfile]) - 1] = files[mainfile][len(files[mainfile]) - 1].strip()

    # Cambia las variables del documento principales
    nl = ['% INFORMACIÓN DEL DOCUMENTO\n',
          '\def\\titulodelreporte {Título del reporte}\n',
          '\def\\temaatratar {Tema a tratar}\n',
          '\def\\fechadelreporte {\\today}\n\n']
    files[mainfile] = find_replace_block(files[mainfile], '% INFORMACIÓN DEL DOCUMENTO', nl, white_end_block=True,
                                         jadd=-1)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIIONES
    # -------------------------------------------------------------------------
    fl = release['CONFIGFILE']
    config_reporte = file_to_list(subrelfile['CONFIG'])

    # Configuraciones que se borran
    cdel = ['firstpagemargintop', 'portraitstyle', 'predocpageromannumber', 'predocpageromanupper',
            'predocresetpagenumber', 'fontsizetitlei', 'styletitlei', 'nomltcont', 'nomltfigure', 'nomltsrc',
            'nomlttable', 'nameportraitpage', 'indextitlecolor', 'addindextobookmarks', 'portraittitlecolor',
            'margineqnindexbottom', 'margineqnindextop', 'nomlteqn', 'bibtexindexbibliography']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    for cdel in ['nameabstract', 'nameappendixsection', 'namereferences', 'nomchapter', 'nomltappendixsection',
                 'nomltwfigure', 'nomltwsrc', 'nomltwtable', 'nomnpageof', 'namemathcol', 'namemathdefn', 'namemathej',
                 'namemathlem', 'namemathobs', 'namemathprp', 'namemaththeorem']:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    files[fl] = add_block_from_list(files[fl], [files[fl][ra],
                                                '\def\indexdepth{4}                 % Profundidad de los marcadores\n'],
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
    # files[fl].pop()

    # -------------------------------------------------------------------------
    # CAMBIA LAS ECUACIONES
    # -------------------------------------------------------------------------
    fl = release['EQNFILE']
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = release['IMPORTSFILE']
    idel = []
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% Estilo portada', white_end_block=True)
    ra, _ = find_block(files[fl], '\showappendixsecindex')
    nl = ['\\def\\showappendixsecindex{false}\n',
          files[fl][ra]]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = release['INITCONFFILE']
    init_auxiliar = file_to_list(subrelfile['INIT'])
    nl = find_extract(init_auxiliar, 'Operaciones especiales Template-Reporte', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE)
    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True)
    files[fl] = find_delete_block(files[fl], 'Se crean variables si se borraron', True)
    ra, _ = find_block(files[fl], '\checkvardefined{\\autordeldocumento}', True)

    # Agrega definición de titulodelreporte
    nl = ['\def\\titulodelinforme{\\titulodelreporte}\n',
          files[fl][ra]]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    ra, _ = find_block(files[fl], '\pdfmetainfotitulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\titulodelreporte')
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-REPT')
    ra, _ = find_block(files[fl], 'Template.Tipo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
    # fl = release['PAGECONFFILE']

    # -------------------------------------------------------------------------
    # FINALCONF
    # -------------------------------------------------------------------------
    fl = release['FINALCONF']
    # flfinl = files[fl]  # type: list
    # flfinl.insert(len(flfinl) - 2, '\\renewcommand{\\abstractname}{\\nameabstract}\n')
    a, _ = find_block(files[fl], '\\titleclass{\subsubsubsection}{straight}[\subsection]')
    files[fl].pop()
    files[fl].append(files[fl].pop(a).strip() + '\n')

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
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
            data[0] = '% Template:     Template Reporte LaTeX\n'
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

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t3 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t4 = time.time() - t
                # tmean = (t1 + t2) / 2
                tmean = min(t1, t2, t3, t4)
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
            fl_pos_dp_mainfile = find_line(data_mainfile, '\def\departamentouniversidad')
            fl_pos_im_mainfile = find_line(data_mainfile, '\def\imagendepartamento')

            # Se recorre cada versión y se genera el .zip
            for m in DEPTOS:
                data_mainfile[fl_pos_dp_mainfile] = '\\def\\departamentouniversidad {' + m[0] + '}\n'
                data_mainfile[fl_pos_im_mainfile] = '\\def\\imagendepartamento {departamentos/' + m[1] + '}\n'

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
        clear_dict(RELEASES[REL_AUXILIAR], 'FILES')

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
    configfile = release['CONFIGFILE']
    files = release['FILES']
    initconffile = release['INITCONFFILE']
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
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t1 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t2 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t3 = time.time() - t
            t = time.time()
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL, creationflags=CREATE_NO_WINDOW)
            t4 = time.time() - t
            # tmean = (t1 + t2) / 2
            tmean = min(t1, t2, t3, t4)
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
    files['src/etc/example.tex'] = file_to_list('src/etc/example_tesis.tex')
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/style/color.tex'] = copy.copy(mainf['src/style/color.tex'])
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    mainfile = release['MAINFILE']
    subrelfile = release['SUBRELFILES']
    examplefile = release['EXAMPLEFILE']
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = release['CONFIGFILE']
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
    # MODIFICA CONFIGURACIIONES
    # -------------------------------------------------------------------------
    fl = release['CONFIGFILE']

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
    nconf = replace_argument(files[fl][ra], 1, '2.0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '3.0').replace('%', ' %')
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
    nconf = replace_argument(files[fl][ra], 1, '3.0')
    nl = [nconf,
          '\\def\\pagemarginleftportrait {2.5}  % Margen izquierdo página portada [cm]\n']
    files[fl] = add_block_from_list(files[fl], nl, ra)
    ra, _ = find_block(files[fl], 'pagemarginright', True)
    nconf = replace_argument(files[fl][ra], 1, '2.0').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\pagemargintop', True)  # Por alguna extraña razón requiere el \\
    nconf = replace_argument(files[fl][ra], 1, '2.0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style7')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgbookmarksopenlevel', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgpdfsecnumbookmarks', True)
    nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
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
    ra, _ = find_block(files[fl], 'addindextobookmarks', True)
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
    nconf = replace_argument(files[fl][ra], 1, 'Tabla de Contenidos').replace('%', ' %')
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
            'indexnewpaget', 'showindexofcontents', 'fontsizetitlei', 'styletitlei', 'indexnewpagee']
    for cdel in cdel:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    for cdel in []:
        ra, rb = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    ra, _ = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl][ra] = '% ESTILO HEADER-FOOTER\n'

    # Añade nuevas entradas
    files[fl] = search_append_line(files[fl], 'captiontextcolor',
                                   '\\def\\chaptercolor {black}          % Color de los capítulos\n')
    files[fl] = search_append_line(files[fl], 'anumsecaddtocounter',
                                   '\\def\\fontsizechapter {\\huge}       % Tamaño fuente de los capítulos\n')
    files[fl] = search_append_line(files[fl], 'showdotaftersnum',
                                   '\\def\\stylechapter {\\bfseries}      % Estilo de los capítulos\n')
    files[fl] = search_append_line(files[fl], '% ESTILO HEADER-FOOTER',
                                   '\\def\\chapterstyle {style1}         % Estilo de los capítulos\n')

    # -------------------------------------------------------------------------
    # CAMBIA TÍTULOS
    # -------------------------------------------------------------------------
    # fl = release['TITLE']

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = release['IMPORTSFILE']
    idel = []
    for idel in idel:
        ra, rb = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% Estilo portada', white_end_block=True)
    # _, rb = find_block(files[fl], '% PARCHES DE LIBRERÍAS', True)
    # files[fl] = add_block_from_list(files[fl], ['\\def\\showappendixsecindex{true}\n'], rb, True)
    files[fl].pop()
    a, _ = find_block(files[fl], '\\usepackage{apacite}', True)
    files[fl][a] = files[fl][a].replace('{apacite}', '[nosectionbib]{apacite}')

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = release['INITCONFFILE']
    init_tesis = file_to_list(subrelfile['INIT'])

    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True)
    files[fl] = find_delete_block(files[fl], 'Se crean variables si se borraron', True)
    ra, _ = find_block(files[fl], '\checkvardefined{\\autordeldocumento}', True)

    # Añade bloque de variables definidas
    nl = find_extract(init_tesis, '% Inicialización de variables', white_end_block=True)
    nl.append(files[fl][ra])
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)
    # ra, _ = find_block(files[fl], 'pdfkeywords', True)
    # files[fl][ra] = '\tpdfkeywords={pdf, \\nombreuniversidad, \\localizacionuniversidad},\n'

    # Elimina referencias en dos columnas
    # files[fl] = find_delete_block(files[fl], '% Referencias en 2 columnas', True)
    ra, _ = find_block(files[fl], '{\\begin{multicols}{2}[\section*{\\refname}', True)
    files[fl][ra] = '\t{\\begin{multicols}{2}[\\chapter*{\\refname}]\n'

    ra, _ = find_block(files[fl], '\pdfmetainfotitulo')
    files[fl][ra] = replace_argument(files[fl][ra], 1, '\\titulotesis')
    ra, _ = find_block(files[fl], 'Template.Nombre')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-THS')
    ra, _ = find_block(files[fl], 'Template.Tipo')
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

    # Agrega estilos de capítulos
    files[fl].pop()
    nl = find_extract(init_tesis, '% Estilos de capítulos', white_end_block=True)
    for i in nl:
        files[fl].append(i)

    # -------------------------------------------------------------------------
    # ÍNDICE
    # -------------------------------------------------------------------------
    fl = release['INDEX']
    index_tesis = file_to_list(subrelfile['INDEX'])

    # Agrega inicial
    ra, _ = find_block(files[fl], 'Crea nueva página y establece estilo de títulos', True)
    nl = find_extract(index_tesis, '% Inicio índice, desactiva espacio entre objetos', True)
    files[fl] = add_block_from_list(files[fl], nl, ra)

    ra, _ = find_block(files[fl], 'Se añade una página en blanco', True)
    nl = find_extract(index_tesis, '% Final del índice, reestablece el espacio', True)
    files[fl] = add_block_from_list(files[fl], nl, ra)

    w = '% Configuración del punto en índice'
    nl = find_extract(index_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True)
    w = '% Cambia tabulación índice de objetos para alinear con contenidos'
    nl = find_extract(index_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True)

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
    fl = release['PAGECONFFILE']
    page_tesis = file_to_list(subrelfile['PAGE'])
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

    # -------------------------------------------------------------------------
    # ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = release['ENVIRONMENTS']
    env_tesis = file_to_list(subrelfile['ENVIRONMENTS'])

    # Reemplaza bloques
    w = '% Crea una sección de referencias solo para bibtex'
    nl = find_extract(env_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True)
    w = '% Crea una sección de resumen'
    nl = find_extract(env_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True)
    _, rb = find_block(files[fl], w, True)
    nl = find_extract(env_tesis, '% Crea una sección de dedicatoria', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)
    _, rb = find_block(files[fl], '% Crea una sección de dedicatoria', True)
    nl = find_extract(env_tesis, '% Crea una sección de agradecimientos', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)

    # Reemplaza líneas
    ra, _ = find_block(files[fl], 'counterwithin{equation}')
    files[fl][ra] = '\\counterwithin{equation}{chapter}\n'
    ra, _ = find_block(files[fl], 'counterwithin{figure}')
    files[fl][ra] = '\\counterwithin{figure}{chapter}\n'
    ra, _ = find_block(files[fl], 'counterwithin{lstlisting}')
    files[fl][ra] = '\\counterwithin{lstlisting}{chapter}\n'
    ra, _ = find_block(files[fl], 'counterwithin{table}')
    files[fl][ra] = '\\counterwithin{table}{chapter}\n'

    # Cambia valor de anexos sección
    ra, _ = find_block(files[fl], 'GLOBALsectionalph')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'false')

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    delfile = release['COREFUN']
    fl = files[delfile]
    files[delfile] = find_delete_block(fl, '\\newcommand{\\bgtemplatetestimg}{')
    fl = files[delfile]
    files[delfile] = find_delete_block(fl, '\def\\bgtemplatetestcode {d0g3}', white_end_block=True)
    files[delfile] = find_delete_block(fl, '% Para la compatibilidad con template-tesis se define el capítulo',
                                       white_end_block=True)

    # Cambia encabezado archivos
    for fl in files.keys():
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = '% Template:     Template Tesis LaTeX\n'
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

        # Mueve el archivo de configuraciones
        copyfile(subrlfolder + configfile, subrlfolder + 'template_config.tex')
        copyfile(subrlfolder + examplefile, subrlfolder + 'example.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['template.tex'], configfile, subrlfolder, headersize, files)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        t = time.time()
        with open(os.devnull, 'w') as FNULL:
            printfun(MSG_DCOMPILE, end='')
            with Cd(subrlfolder):
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t1 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t2 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t3 = time.time() - t
                t = time.time()
                call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL,
                     creationflags=CREATE_NO_WINDOW)
                t4 = time.time() - t
                # tmean = (t1 + t2) / 2
                tmean = min(t1, t2, t3, t4)
                printfun(MSG_FOKTIMER.format(t2))

                # Copia a la carpeta pdf_version
                if savepdf:
                    copyfile(mainfile.replace('.tex', '.pdf'), release['PDF_FOLDER'].format(version))

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

            # Se exportan los distintos estilos de versiones
            data_mainfile = file_to_list(subrlfolder + mainfile)

            # Se buscan las líneas del departamento y de la imagen
            fl_pos_dp_mainfile = find_line(data_mainfile, '\def\departamentouniversidad')
            fl_pos_im_mainfile = find_line(data_mainfile, '\def\imagendepartamento')

            # Se recorre cada versión y se genera el .zip
            for m in DEPTOS:
                data_mainfile[fl_pos_dp_mainfile] = '\\def\\departamentouniversidad {' + m[0] + '}\n'
                data_mainfile[fl_pos_im_mainfile] = '\\def\\imagendepartamento {departamentos/uchile2}\n'

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
        clear_dict(RELEASES[REL_AUXILIAR], 'FILES')

    # Retorna a root
    os.chdir(mainroot)
