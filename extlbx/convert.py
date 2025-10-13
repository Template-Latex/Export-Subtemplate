"""
CONVERT
Convierte los archivos y exporta versiones

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
    'export_articulo',
    'export_auxiliares',
    'export_controles',
    'export_cv',
    'export_informe',
    'export_poster',
    'export_presentacion',
    'export_reporte',
    'export_tesis',
    'MSG_FOKTIMER'
]

# Importación de librerías
from extlbx.latex import *
from extlbx.releases import *
from extlbx.utils import *
from shutil import copyfile
from extlbx.stats import *
from extlbx.ziputils import *
import copy
import time
import os

# Constantes
MSG_DCOMPILE = 'COMPILANDO ... '
MSG_FOKTIMER = 'OK [t {0:.3g}]'
MSG_GEN_FILE = 'GENERANDO ARCHIVOS ... '
MSG_LAST_VER = 'ULTIMA VERSION:\t {0}'
MSG_UPV_FILE = 'ACTUALIZANDO VERSION ...'
STRIP_ALL_GENERATED_FILES = False  # Aplica strip a todos los archivos en dist/
STRIP_TEMPLATE_FILE = False  # Elimina comentarios y aplica strip a archivo del template


def find_extract(data, element, white_end_block=False, iadd=0, jadd=0):
    """
    Encuentra el bloque determinado por <element> y retorna el bloque.

    :param element: Elemento a buscar
    :param data: Lista.
    :param white_end_block: Indica si el bloque termina en espacio en blanco o con llave
    :param iadd: Agrega líneas al inicio del bloque
    :param jadd: Agrega líneas al término del bloque
    :return: Retorna la lista que contiene el elemento
    """
    ia, ja = find_block(data, element, white_end_block)
    return extract_block_from_list(data, ia + iadd, ja + jadd)


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


def find_remove_recursive_line(data, line):
    """
    Elimina de manera recursiva.

    :param data: Datos
    :param line: Bloque a buscar
    :return:
    """
    while True:
        try:
            ra, _ = find_block(data, line)
            data.pop(ra)
        except ValueError:
            break


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
        if '\\input{' == lined.strip()[0:7]:
            ifile = get_file_from_input(lined)
            if ifile == configfile:
                new_template_file.append('\\input{template_config}\n')
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
    save_list_to_file(new_template_file, distfolder + 'template.tex')


def change_header_tex_files(files, release, headersize, headerversionpos, versionhead):
    """
    Cambia el encabezado de los archivos tex.

    :param files: Lista de archivos
    :param release: Datos release
    :param headersize: Tamaño del header
    :param headerversionpos: Posición de la versión
    :param versionhead: String de la versión
    :return: None
    """
    for fl in files.keys():
        if '.tex' not in fl:
            continue
        data = files[fl]
        # noinspection PyCompatibility,PyBroadException
        try:
            data[0] = f"% Template:     {release['NAME_HEADER']}\n"
            data[headersize - 3] = f"% Manual template: [{release['WEB']['MANUAL']}]\n"
            data[headersize - 2] = '% Licencia MIT:    [https://opensource.org/licenses/MIT]\n'
            data[headerversionpos] = versionhead
        except:
            print('Error en archivo ' + fl)


def compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                     release, version, stat, versiondev, dia, versionhash, plotstats, prefixpath=''):
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
    :param versionhash: Hash de la versión
    :param plotstats: Imprime estadísticas
    :param prefixpath: Agrega prefijo al path del pdf
    """
    lc = 1
    with open(os.devnull, 'w') as FNULL:
        printfun(MSG_DCOMPILE, end='')
        with Cd(subrlfolder):
            # print(subrlfolder, mainfile)
            t1 = call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL)
            call(['bibtex', mainfile.replace('.tex', '')], stdout=FNULL)
            t2 = call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL)
            tmean = min(t1, t2)
            printfun(MSG_FOKTIMER.format(tmean))

            # Actualización final para reparar el PDF
            time.sleep(1)
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL)
            time.sleep(1)
            call(['pdflatex', '-interaction=nonstopmode', mainfile], stdout=FNULL)

            # Cuenta el número de líneas
            f = open('template.tex', encoding='utf8')
            for _ in f:
                lc += 1
            f.close()

            # Copia a la carpeta pdf_version
            if savepdf:
                copyfile(mainfile.replace('.tex', '.pdf'), prefixpath + release['PDF_FOLDER'].format(version))

    # Se agregan las estadísticas
    if addstat:
        add_stat(statsroot + stat['FILE'], versiondev, tmean, dia, lc, versionhash)

    # Se plotean las estadísticas
    if plotstats:
        plot_stats(statsroot + stat['FILE'], statsroot + stat['CTIME'], statsroot + stat['LCODE'])


def copy_assemble_template(files, distfolder, headersize, configfile, mainfile, examplefile):
    """
    Copia y ensambla el template.

    :param files: Lista de archivos
    :param distfolder: Carpeta de distribución
    :param headersize: Tamaño del header
    :param configfile: Archivo de configs
    :param mainfile: Archivo principal
    :param examplefile: Archivo de ejemplo
    :return: None
    """
    for f in files.keys():
        fl = open(distfolder + f, 'w', encoding='utf8')

        # Se escribe el header
        if '.tex' in f:
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
        if f == configfile or f == mainfile or f == examplefile or '_config' in f:
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


def export_subdeptos_subtemplate(release, subrlfolder, mainfile, distfolder,
                                 deptimg=None, finalimg='fcfm'):
    """
    Exporta los departamentos.

    :param release: Datos del release
    :param subrlfolder: Carpeta de los releases
    :param mainfile: Archivo principal
    :param distfolder: Carpeta de salida
    :param deptimg: Imagen del departamento fija
    :param finalimg: Imagen final
    :return: None
    """
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
    fl_pos_dp_mainfile = find_line(data_mainfile, '\\def\\universitydepartment')
    fl_pos_im_mainfile = find_line(data_mainfile, '\\def\\universitydepartmentimage')

    # Se recorre cada versión y se genera el .zip
    for m in DEPTOS:
        data_mainfile[fl_pos_dp_mainfile] = '\\def\\universitydepartment {' + m[0] + '}\n'
        if deptimg:
            data_mainfile[fl_pos_im_mainfile] = '\\def\\universitydepartmentimage {departamentos/' + deptimg + '}\n'
        else:
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
                                                         'departamentos/' + finalimg)
    save_list_to_file(data_mainfile, subrlfolder + mainfile)


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
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionheader = '% Versión:      {0} ({1})\n'

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header de la versión
    versionhead = versionheader.format(version, dia)

    # Se buscan números de lineas de hyperref
    initconf_data = file_to_list(initconffile)
    l_tdate, d_tdate = find_line_str(initconf_data, 'Template.Date', True)
    l_thash, d_thash = find_line_str(initconf_data, 'Template.Version.Hash', True)
    l_ttype, d_ttype = find_line_str(initconf_data, 'Template.Type', True)
    l_tvdev, d_tvdev = find_line_str(initconf_data, 'Template.Version.Dev', True)
    l_tvrel, d_tvrel = find_line_str(initconf_data, 'Template.Version.Release', True)
    l_vcmtd, d_vcmtd = find_line_str(initconf_data, 'pdfproducer', True)

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
            fl = open(f, encoding='utf8')
            for line in fl:
                data.append(line)
            fl.close()
        except:
            printfun(f'Error al cargar el archivo {f}')

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
        files_dist = files.copy()
        files_dist['library.bib'] = file_to_list('library.bib')
        files_dist['natnumurl.bst'] = file_to_list('natnumurl.bst')
        copy_assemble_template(files_dist, distfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format(time.time() - t))

    # Compila el archivo
    if docompile and dosave:
        compile_template(distfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats, prefixpath='../')

    # Se exporta el proyecto normal
    if dosave:
        # Se exportan los distintos estilos de versiones
        jmainfilel = 0
        data_mainfile = file_to_list(distfolder + mainfile)
        for j in range(len(data_mainfile)):
            if get_file_from_input(data_mainfile[j]) == examplefile:
                data_mainfile[j] = '\\input{example} % Ejemplo, se puede borrar\n'
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
        fl_pos_dp_mainfile = find_line(data_mainfile, '\\def\\universitydepartment')
        fl_pos_im_mainfile = find_line(data_mainfile, '\\def\\universitydepartmentimage')

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
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/auxiliar.tex'] = file_to_list('src/cmd/auxiliar.tex')
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_auxiliar.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_auxiliar.tex')
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

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
    files[mainfile] = find_delete_block(files[mainfile], '% CONFIGURACIONES FINALES', white_end_block=True)
    ra = find_line(files[mainfile], 'documenttitle')
    files[mainfile][ra] = '\\def\\documenttitle {Título de la auxiliar}\n'
    ra = find_line(files[mainfile], 'documentsubtitle')
    files[mainfile].pop(ra)
    ra = find_line(files[mainfile], 'documentsubject')
    files[mainfile][ra] = '\\def\\documentsubject {Tema de la auxiliar}\n'
    for j in range(len(files[mainfile])):
        if get_file_from_input(files[mainfile][j]) == examplefile:
            files[mainfile][j] = '\\input{example} % Ejemplo, se puede borrar\n'
    ra = find_line(files[mainfile], 'universitydepartmentimagecfg')
    files[mainfile][ra] = replace_argument(files[mainfile][ra], 1, 'height=1.75cm')

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'

    # Configuraciones que se borran
    cdel = ['nameportraitpage', 'indextitlecolor', 'firstpagemargintop',
            'portraittitlecolor', 'indexsectionfontsize', 'indexsectionstyle',
            'namechapter', 'namepageof', 'predocpageromannumber', 'showappendixsecindex',
            'predocresetpagenumber', 'margineqnindexbottom', 'margineqnindextop',
            'bibtexindexbibliography', 'anumsecaddtocounter', 'predocpageromanupper',
            'linkcolorindex']
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    ra, rb = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl] = del_block_from_list(files[fl], ra, rb)
    for cdel in []:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')
    ra, _ = find_block(files[fl], 'equationrestart', True)
    nconf = replace_argument(files[fl][ra], 1, 'none')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'stylecitereferences', True)
    nconf = replace_argument(files[fl][ra], 1, 'bibtex')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'natbibrefstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'ieeetr').replace('%', '   %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.3').replace('  %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgbookmarksopenlevel', True)
    nconf = replace_argument(files[fl][ra], 1, '1')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showlinenumbers', True)
    files[fl].insert(ra + 1, '\\def\\templatestyle {style1}        % Estilo del template: style1 a style4\n')
    ra, _ = find_block(files[fl], '\\sssectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace('    %', '%').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\ssectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\large')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\Large')
    files[fl][ra] = nconf

    # -------------------------------------------------------------------------
    # CAMBIA LAS ECUACIONES
    # -------------------------------------------------------------------------
    fl = 'src/cmd/equation.tex'
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['notoccite', 'ragged2e', 'totpages']
    for idel in idel:
        ra, _ = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    aux_imports = file_to_list('src/env/imports_auxiliar.tex')
    nl = find_extract(aux_imports, '% Anexos/Apéndices', True)
    files[fl] = find_replace_block(files[fl], '\\ifthenelse{\\equal{\\showappendixsecindex}', nl, jadd=-1,
                                   white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    ra, _ = find_block(files[fl], '\\ifthenelse{\\isundefined{\\authortable}}{')
    files[fl][ra] = '\\ifthenelse{\\isundefined{\\teachingstaff}}{\n'
    ra, _ = find_block(files[fl], '\\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\authortable')
    files[fl][ra] = '\t\\errmessage{LaTeX Warning: Se borro la variable \\noexpand\\teachingstaff, creando una vacia}\n'
    ra, _ = find_block(files[fl], '\\def\\authortable {}')
    files[fl][ra] = '\t\\def\\teachingstaff {}}{\n'

    ra, _ = find_block(files[fl], 'Template.Name')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['NAME'])
    ra, _ = find_block(files[fl], 'Template.Version.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, versiondev + '-AUX')
    ra, _ = find_block(files[fl], 'Template.Type')
    files[fl][ra] = replace_argument(files[fl][ra], 1, 'Normal')
    ra, _ = find_block(files[fl], 'Template.Web.Dev')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['SOURCE'])
    ra, _ = find_block(files[fl], '\\setcounter{tocdepth}')
    files[fl][ra] = replace_argument(files[fl][ra], 2, '1')
    ra, _ = find_block(files[fl], 'Template.Web.Manual')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['WEB']['MANUAL'])
    ra, _ = find_block(files[fl], 'pdfproducer')
    files[fl][ra] = replace_argument(files[fl][ra], 1, release['VERLINE'].format(version))

    files[fl] = find_delete_block(files[fl], '% Se revisa si se importa tikz', white_end_block=True, iadd=-1)

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    # Elimina subtitulo
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\documentsubtitle}{}}{', jadd=1)

    # Agrega saltos de líneas
    for i in ['% Crea referencias enumeradas en apacite', '% Desactiva la URL de apacite',
              '% Referencias en 2 columnas']:
        ra, _ = find_block(files[fl], i)
        files[fl][ra] = '\n' + files[fl][ra]

    # Elimina documentsubtitle
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\isundefined{\\documentsubtitle}}{', True)

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
    files[fl].pop()
    _, rb = find_block(files[fl], '% Muestra los números de línea', blankend=True)

    i1, f1 = find_block(aux_pageconf, '% Reestablece los valores del estado de los títulos', True)
    nl = extract_block_from_list(aux_pageconf, i1 - 1, f1)
    nl.insert(0, '\n')
    files[fl] = add_block_from_list(files[fl], nl, rb)

    i1, f1 = find_block(aux_pageconf, '% Establece el estilo de las sub-sub-sub-secciones', True)
    nl = extract_block_from_list(aux_pageconf, i1 - 1, f1)
    nl.insert(0, '\n')
    files[fl] = add_block_from_list(files[fl], nl, rb)

    i1, f1 = find_block(aux_pageconf, '% Reestablece \\cleardoublepage', True)
    nl = extract_block_from_list(aux_pageconf, i1 - 1, f1)
    nl.insert(0, '\n')
    files[fl] = add_block_from_list(files[fl], nl, rb)

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
    nl = find_extract(aux_fun, '% Inserta código fuente sin parámetros', True)  # No borrar...
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Importa código fuente desde un archivo sin parámetros', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Itemize en negrita', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Enumerate en negrita', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Crea una sección de imágenes múltiples', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    nl = find_extract(aux_fun, '% Crea una sección de imágenes múltiples completa dentro de un multicol', True)
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE, addnewline=True)
    files[fl].pop()

    # -------------------------------------------------------------------------
    # TITLE
    # -------------------------------------------------------------------------
    fl = 'src/cmd/title.tex'
    files[fl] = find_delete_block(files[fl], '% Insertar un título sin número y sin indexar', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título sin número sin cambiar el título del header',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl],
                                  '% Insertar un título sin número, sin indexar y sin cambiar el título del header',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un subtítulo sin número y sin indexar', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un sub-sub-subtítulo sin número y sin indexar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título en un índice, sin número de página',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un título en un índice, con número de página',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea una sección en el índice y en el header', white_end_block=True)

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '% Imagen de prueba tikz', white_end_block=True)

    # Cambia encabezado archivos
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

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
    Exporta los controles.

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
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/control.tex'] = copy.copy(mainf['src/cmd/auxiliar.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_control.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_control.tex')
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

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
    files[mainfile][ra] = '\\def\\documenttitle {Título del Control}\n'
    ra = find_line(files[mainfile], 'documentsubject')
    files[mainfile][ra] = '\\def\\evaluationindication {\\textbf{INDICACIÓN DEL CONTROL}}\n'

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
    nl = find_extract(fun_control, '\\newcommand{\\itempto}', white_end_block=True)
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
    files[fl][ra] += '\\def\\bolditempto {true}            % Puntaje item en negrita\n'
    cdel = ['templatestyle']
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    ra, _ = find_block(files[fl], '\\checkvardefined{\\documentsubject}')
    files[fl].pop(ra)
    ra, _ = find_block(files[fl], '\\g@addto@macro\\documentsubject\\xspace')
    files[fl].pop(ra)
    _, rb = find_block(files[fl], '\\ifthenelse{\\isundefined{\\teachingstaff}}', blankend=True)
    files[fl][rb] = '\\ifthenelse{\\isundefined{\\evaluationindication}}{\n\t\\def\\evaluationindication {}\n}{}\n\n'

    ra, _ = find_block(files[fl], '\\pdfmetainfosubject')
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
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

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
    files['library.bib'] = file_to_list('library.bib')
    files['main.tex'] = copy.copy(mainf['main.tex'])
    files['natnumurl.bst'] = file_to_list('natnumurl.bst')
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_reporte.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_reporte.tex')
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'
    distfolder = release['DIST']

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

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
    ra, _ = find_block(files[mainfile], '\\input{src/etc/example}', True)
    files[mainfile] = add_block_from_list(files[mainfile], main_reporte, ra, addnewline=True)
    ra, _ = find_block(files[mainfile], 'universitydepartmentimagecfg', True)
    files[mainfile].pop(ra)

    # Cambia las variables del documento principales
    nl = ['% INFORMACIÓN DEL DOCUMENTO\n',
          '\\def\\documenttitle {Título del reporte}\n',
          '\\def\\documentsubtitle {}\n',
          '\\def\\documentsubject {Tema a tratar}\n',
          '\\def\\documentdate {\\today}\n\n']
    files[mainfile] = find_replace_block(files[mainfile], '% INFORMACIÓN DEL DOCUMENTO', nl, white_end_block=True,
                                         jadd=-1)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'
    config_reporte = file_to_list('src/config_reporte.tex')

    # Configuraciones que se borran
    cdel = ['firstpagemargintop', 'portraitstyle', 'predocpageromannumber', 'predocpageromanupper',
            'predocresetpagenumber', 'indexsectionfontsize', 'indexsectionstyle', 'nameportraitpage',
            'indextitlecolor', 'addindextobookmarks', 'portraittitlecolor', 'margineqnindexbottom',
            'margineqnindextop', 'bibtexindexbibliography', 'linkcolorindex']
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    for cdel in ['pagemargintop']:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('  %', '%')
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    files[fl] = add_block_from_list(files[fl], [files[fl][ra],
                                                '\\def\\indexdepth {4}                % Profundidad de los marcadores\n'],
                                    ra, addnewline=True)
    ra, _ = find_block(files[fl], 'pagemarginbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '2.5')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '3.81')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginright', True)
    nconf = replace_argument(files[fl][ra], 1, '3.81')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2.5')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style7')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\Large')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sssectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace('    %', '%').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\ssectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\large')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'hfwidthwrap', True)
    files[fl] = replace_block_from_list(files[fl], config_reporte, ra, ra)
    ra, _ = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '11')
    files[fl][ra] = nconf

    ra, _ = find_block(files[fl], '% CONFIGURACIÓN DE LAS LEYENDAS - CAPTION', True)
    files[fl][ra] = '\n' + files[fl][ra]

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['ragged2e']
    for idel in idel:
        ra, _ = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    ra, _ = find_block(files[fl], '\\showappendixsecindex')
    nl = ['\\def\\showappendixsecindex {false}\n',
          files[fl][ra]]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_auxiliar = file_to_list('src/cfg/init_reporte.tex')
    nl = find_extract(init_auxiliar, 'Operaciones especiales Template-Reporte', True)
    nl.insert(0, '% -----------------------------------------------------------------------------\n')
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE)
    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\isundefined{\\authortable}}{', True)

    cdel = ['\\author{\\pdfmetainfoauthor}', '\\title{\\pdfmetainfotitle}']
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    # Borra línea definiciones
    ra, _ = find_block(files[fl], '\\checkvardefined{\\universitydepartmentimagecfg}')
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

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '\\newcommand{\\bgtemplatetestimg}{')
    files[fl] = find_delete_block(files[fl], '\\def\\bgtemplatetestcode {d0g3}', white_end_block=True)
    ra, _ = find_block(files[fl], '% Imagen de prueba tikz')
    files[fl].pop(ra)

    # -------------------------------------------------------------------------
    # FINALCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/final.tex'
    files[fl] = find_delete_block(files[fl], '% Agrega páginas dependiendo del formato', iadd=-1, jadd=1)
    ra, _ = find_block(files[fl], '\\setcounter{footnote}{0}')
    files[fl][ra + 1] = '\t\n'

    # Cambia encabezado archivos
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

    # Se exporta el proyecto normal
    if dosave:
        export_subdeptos_subtemplate(release, subrlfolder, mainfile, distfolder)

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
    files['library.bib'] = file_to_list('library.bib')
    files['main.tex'] = file_to_list('main_articulo.tex')
    files['natnumurl.bst'] = file_to_list('natnumurl.bst')
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/articulo.tex'] = file_to_list('src/cmd/articulo.tex')
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_articulo.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_articulo.tex')
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

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
            'hfwidthcourse', 'hfwidthtitle', 'hfwidthwrap', 'disablehfrightmark',
            'marginequationbottom', 'marginequationtop', 'margingatherbottom',
            'margingathertop']
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    ra, _ = find_block(files[fl], 'pagemarginbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '1.91').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '1.27')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemarginright', True)
    nconf = replace_argument(files[fl][ra], 1, '1.27')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '1.91').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '9.5').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontdocument', True)
    nconf = replace_argument(files[fl][ra], 1, 'libertine').replace('  %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentinterline', True)
    nconf = replace_argument(files[fl][ra], 1, '1').replace('%', '    %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontsizerefbibl', True)
    nconf = replace_argument(files[fl][ra], 1, '\\small').replace('%', '     %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'natbibrefsep', True)
    nconf = replace_argument(files[fl][ra], 1, '2')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'apaciterefsep', True)
    nconf = replace_argument(files[fl][ra], 1, '2')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'bibtexrefsep', True)
    nconf = replace_argument(files[fl][ra], 1, '2')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captiontextbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionlrmarginmc', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionlrmargin', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginimagebottom', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.2').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'margingathercapttop', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.7')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginlinenumbers', True)
    nconf = replace_argument(files[fl][ra], 1, '6').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'tablenotesfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\footnotesize').replace('  %', '%').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sectionspacingtop', True)
    nconf = replace_argument(files[fl][ra], 1, '15')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\ssectionspacingbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '8').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sssectionspacingbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '6')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\ssssectionspacingbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '4')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'charappendixsection', True)
    nconf = replace_argument(files[fl][ra], 1, '').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'charaftersectionnum', True)
    nconf = replace_argument(files[fl][ra], 1, '').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmargini {', True)
    nconf = replace_argument(files[fl][ra], 1, '20')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginii {', True)
    nconf = replace_argument(files[fl][ra], 1, '17')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginiii {', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', '   %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginiv {', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'footnoterulepage', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf

    ra, _ = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style1').replace('16 estilos', '19 estilos')
    files[fl][ra] = nconf + '\\def\\titleauthorspacing {0.35}     % Distancia entre autores [cm]\n' \
                            '\\def\\titleauthormarginbottom {0.2} % Margen inferior autores [cm]\n' \
                            '\\def\\titleauthormargintop {0.6}    % Margen superior autores [cm]\n' \
                            '\\def\\titleauthormaxwidth {0.85}    % Tamaño máximo datos autores [linewidth]\n' \
                            '\\def\\titlebold {true}              % Título en negrita\n' \
                            '\\def\\titlestyle {style1}           % Estilo título (5 estilos)\n'
    ra, _ = find_block(files[fl], '% CONFIGURACIONES DE OBJETOS', True)
    files[fl][ra] += '\\def\\abstractmarginbottom {0.5}    % Margen inferior abstract [cm]\n' \
                     '\\def\\abstractmargintop {0}         % Margen superior abstract [cm]\n'

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    ra, _ = find_block(files[fl], '% Muestra los números de línea')
    nl = ['}\n'
          '\\def\\marginequationbottom {0}\n'
          '\\def\\marginequationtop {0}\n'
          '\\def\\margingatherbottom {0}\n'
          '\\def\\margingathertop {0}\n',
          '\\ifthenelse{\\equal{\\showlinenumbers}{true}}{ % Muestra los números de línea\n']
    files[fl] = replace_block_from_list(files[fl], nl, ra - 1, ra - 1)

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
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

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
    ra, _ = find_block(files[fl], '% Define funciones generales')
    rb, _ = find_block(files[fl], '% No se encontró el header-footer, no hace nada')
    nl.pop()
    files[fl] = replace_block_from_list(files[fl], [], ra, rb)
    files[fl] = find_delete_block(files[fl], '% Actualiza headers', white_end_block=True, jadd=-1)

    # -------------------------------------------------------------------------
    # CAMBIA ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = 'src/env/environments.tex'
    files[fl] = find_delete_block(files[fl], '% Crea una sección de resumen', white_end_block=True)

    # Cambia encabezado archivos
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

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
def export_poster(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                  plotstats=True, addstat=True, doclean=True,
                  savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta poster.

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
    release = RELEASES[REL_POSTER]

    # Obtiene archivos
    t = time.time()

    # Genera informe
    # noinspection PyTypeChecker
    export_presentacion(version, versiondev, versionhash, dosave=False, docompile=False,
                        plotstats=False, printfun=nonprint, addstat=False, doclean=False, savepdf=False,
                        informeroot=informeroot, mainroot=mainroot, cfgfile='src/config_poster.tex')

    if dosave:
        printfun(MSG_GEN_FILE, end='')
    else:
        printfun(MSG_UPV_FILE, end='')

    os.chdir(informeroot)
    mainf = RELEASES[REL_PRESENTACION]['FILES']
    files = release['FILES']
    files['library.bib'] = file_to_list('library.bib')
    files['main.tex'] = file_to_list('main_poster.tex')
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/cmd/poster.tex'] = file_to_list('src/cmd/poster.tex')
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_poster.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_poster.tex')

    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header
    versionhead = versionhead.format(version, dia)

    # -------------------------------------------------------------------------
    # MODIFICA CONFIGURACIONES
    # -------------------------------------------------------------------------
    fl = 'src/config.tex'

    # Configuraciones que se borran
    cdel = []
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)

    ra, _ = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '23').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontdocument', True)
    nconf = replace_argument(files[fl][ra], 1, 'ralewaylight').replace('      %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captioncolor', True)
    nconf = replace_argument(files[fl][ra], 1, 'mitred').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captiontbmarginfigure', True)
    nconf = replace_argument(files[fl][ra], 1, '20').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captiontextbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'bibtexstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'ieeetr').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'tablenotesfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\scriptsize').replace('  %', '%').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, 'small').replace('%', '       %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\captionmarginimagesmc', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', '    %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\captionmarginimages', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', '    %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'bibtexrefsep', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodefonts', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace('{', ' {').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodeilfonts', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace(' {', '{').replace('    %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodenumbersep', True)
    nconf = replace_argument(files[fl][ra], 1, '12').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodenumbersize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\scriptsize').replace(' %', '%').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodeskipbelow', True)
    nconf = replace_argument(files[fl][ra], 1, '0.5').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captiontextsubnumbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'false').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmargini {', True)
    nconf = replace_argument(files[fl][ra], 1, '85').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'itemizeitemcolor', True)
    nconf = replace_argument(files[fl][ra], 1, 'mitred').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'enumerateitemcolor', True)
    nconf = replace_argument(files[fl][ra], 1, 'mitred').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sitemizei {', True)
    nconf = replace_argument(files[fl][ra], 1, '\\iitembsquare').replace('  %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sitemizeii {', True)
    nconf = replace_argument(files[fl][ra], 1, '\\iitembcirc').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sitemizeiii {', True)
    nconf = replace_argument(files[fl][ra], 1, '\\iitemdash')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sitemizeiv {', True)
    nconf = replace_argument(files[fl][ra], 1, '\\iitemcirc').replace('%', '   %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginii {', True)
    nconf = replace_argument(files[fl][ra], 1, '50.6')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginiii {', True)
    nconf = replace_argument(files[fl][ra], 1, '43').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginimagemultright', True)
    nconf = replace_argument(files[fl][ra], 1, '1.25')
    files[fl][ra] = nconf

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_poster = file_to_list('src/cfg/init_poster.tex')

    # Elimina
    for i in ['\\def\\pdfmetainfosubject {\\documentsubject}', '\\def\\pdfmetainfosubject {}',
              'Document.Subject={\\pdfmetainfosubject}', 'pdfsubject={\\pdfmetainfosubject}',
              '\\def\\pdfmetainfoauthor {\\documentauthor}', '\\def\\pdfmetainfocoursecode {\\coursecode}',
              '\\def\\pdfmetainfocoursename {\\coursename}', '\\def\\pdfmetainfouniversity {\\universityname}',
              '\\def\\pdfmetainfouniversitydepartment {\\universitydepartment}',
              '\\def\\pdfmetainfouniversityfaculty {\\universityfaculty}',
              '\\def\\pdfmetainfouniversitylocation {\\universitylocation}', '\\def\\pdfmetainfoauthor {}',
              '\\def\\pdfmetainfocoursecode {}', '\\def\\pdfmetainfocoursename {}', '\\def\\pdfmetainfouniversity {}',
              '\\def\\pdfmetainfouniversitydepartment {}', '\\def\\pdfmetainfouniversityfaculty {}',
              '\\def\\pdfmetainfouniversitylocation {}', 'pdfauthor={\\pdfmetainfoauthor},',
              'Course.Code=', 'Course.Name=', 'Document.Author=', 'University.Department=', 'University.Faculty=',
              'University.Location=', 'University.Name='
              ]:
        ra, _ = find_block(files[fl], i)
        files[fl].pop(ra)
    for i in ['% Cambios generales en presentación', '% Se revisa si las variables no han sido borradas',
              '% Se añade \\xspace a las variables', '% Corrige espaciamiento de itemize', '% Establece temas custom']:
        files[fl] = find_delete_block(files[fl], i, iadd=-1, white_end_block=True)
    ra, _ = find_block(files[fl], '% Se activan números en menú marcadores del pdf')
    files[fl].pop(ra + 1)

    # Inserta bloques
    for i in ['% Configura las listas',
              '% Configura las ecuaciones',
              '% Configura los caption',
              '% Configura los colores',
              '% Define el tamaño de página']:
        nl = find_extract(init_poster, i, white_end_block=True)
        nl.insert(0, '% -----------------------------------------------------------------------------\n')
        for j in nl:
            files[fl].append(j)

    # Cambia valores bloques
    for i in [
        '% Padding superior alerta',
        '% Padding izquierdo alerta',
        '% Padding derecho alerta',
        '% Padding inferior alerta',
        '% Margen inferior alerta',
        '% Padding superior ejemplo',
        '% Padding izquierdo ejemplo',
        '% Padding derecho ejemplo',
        '% Padding inferior ejemplo',
        '% Margen inferior ejemplo',
    ]:
        ra, _ = find_block(files[fl], i)
        files[fl][ra] = files[fl][ra].replace('\\block', '\\blockae')

    # -------------------------------------------------------------------------
    # CAMBIO OTHER
    # -------------------------------------------------------------------------
    fl = 'src/cmd/other.tex'
    ra, _ = find_block(files[fl], '\\hbadness=10000 \\vspace{\\baselinestretch\\baselineskip}')
    files[fl][ra] = files[fl][ra].replace('\\baselinestretch', '0.5\\baselinestretch')

    # -------------------------------------------------------------------------
    # CAMBIO ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = 'src/env/environments.tex'
    conv = [
        '\\lstnewenvironment{sourcecodep}[4][]{%',
        '\\newcommand{\\importsourcecodep}[5][]{%',
        '\\lstnewenvironment{sourcecode}[3][]{%',
        '\\newcommand{\\importsourcecode}[4][]{%'
    ]
    for i in conv:
        ra, _ = find_block(files[fl], i)
        number = '#' + i.split('[')[1].split(']')[0]
        files[fl][ra] += '\t\\vspace{-0.75\\baselineskip}%\n'
        files[fl][ra + 1] = files[fl][ra + 1].replace(number, number + '\\vspace{-1.1\\baselineskip}')

    # -------------------------------------------------------------------------
    # PAGECONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/page.tex'
    files[fl] = find_delete_block(files[fl], '% Configura el tabularframe', white_end_block=True, iadd=-1)

    # Cambia encabezado archivos
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

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
        clear_dict(RELEASES[REL_PRESENTACION], 'FILES')

    # Retorna a root
    os.chdir(mainroot)


# noinspection PyUnboundLocalVariable
def export_presentacion(version, versiondev, versionhash, printfun=print, dosave=True, docompile=True,
                        plotstats=True, addstat=True, doclean=True, cfgfile='src/config_presentacion.tex',
                        savepdf=True, informeroot=None, mainroot=None, statsroot=None):
    """
    Exporta la presentacion.

    :param addstat: Agrega las estadísticas
    :param cfgfile: Archivo de configuraciones
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
    files['library.bib'] = file_to_list('library.bib')
    files['main.tex'] = file_to_list('main_presentacion.tex')
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/presentacion.tex'] = file_to_list('src/cmd/presentacion.tex')
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_presentacion.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_presentacion.tex')
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'
    distfolder = release['DIST']

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

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
            'nameltfigure', 'nameltsrc', 'namelttable', 'nameltcont', 'namelteqn',
            'firstpagemargintop', 'nameportraitpage', 'indextitlecolor', 'portraittitlecolor',
            'pdfcompileversion', 'bibtexenvrefsecnum', 'twopagesclearformat',
            'bibtexindexbibliography', 'bibtextextalign', 'showlinenumbers', 'linenumbercolor',
            'namepageof', 'nameappendixsection', 'apacitebothers', 'apaciterefnumber',
            'apaciterefsep', 'apaciterefcitecharclose', 'apaciterefcitecharopen',
            'apaciteshowurl', 'apacitestyle', 'appendixindepobjnum',
            'twocolumnreferences', 'namechapter', 'anumsecaddtocounter', 'fontsizerefbibl',
            'hfpdashcharstyle', 'nameabstract', 'margineqnindexbottom', 'margineqnindextop',
            'natbibrefcitecharclose', 'natbibrefcitecharopen', 'natbibrefcitecompress',
            'natbibrefcitesepcomma', 'natbibrefcitetype', 'natbibrefsep', 'natbibrefstyle',
            'paragcolor', 'paragsubcolor', 'sectioncolor', 'ssectioncolor', 'sssectioncolor',
            'ssssectioncolor', 'backrefpagecite', 'marginlinenumbers',
            'footnotetopmargin', 'linkcolorindex'
            ]
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DEL ÍNDICE', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% MÁRGENES DE PÁGINA', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% CONFIGURACIÓN DE LOS TÍTULOS', white_end_block=True)
    for cdel in ['captionmarginimagesmc', 'captionmarginimages']:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('    %', '%')
    for cdel in ['namemathcol', 'namemathdefn', 'namemathej',
                 'namemathlem', 'namemathobs', 'namemathprp', 'namemaththeorem',
                 'namereferences', 'nameltappendixsection', 'nameltwfigure',
                 'nameltwsrc', 'nameltwtable']:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')
    for cdel in ['cfgpdfpageview', 'bibtexstyle', 'marginimagemultright']:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace(' %', '%')
    for cdel in ['captiontextbold', 'captiontextsubnumbold', 'cfgpdffitwindow']:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('%', ' %')
    for cdel in []:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('%', '  %')
    for cdel in ['documentinterline']:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('%', '    %')
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    files[fl] = add_block_from_list(
        files[fl], [files[fl][ra], '\\def\\indexdepth {4}                % Profundidad de los marcadores\n'],
        ra, addnewline=True)

    files[fl].pop()
    for i in file_to_list(cfgfile):
        files[fl].append(i)

    ra, _ = find_block(files[fl], 'cfgpdfpageview', True)
    nconf = replace_argument(files[fl][ra], 1, 'FitBV')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '9.5').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'bibtexstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'apalike')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodenumbersep', True)
    nconf = replace_argument(files[fl][ra], 1, '4')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginimagemulttop', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', '   %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodeskipbelow', True)
    nconf = replace_argument(files[fl][ra], 1, '1.15')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodebgmarginleft', True)
    nconf = replace_argument(files[fl][ra], 1, '-1').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentparindent', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionlrmarginmc', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionlrmargin', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'documentinterline', True)
    nconf = replace_argument(files[fl][ra], 1, '1')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captiontextbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captiontextsubnumbold', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgpdffitwindow', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginimagebottom', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.50')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginimagemultright', True)
    nconf = replace_argument(files[fl][ra], 1, '0.35')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'marginimagemultbottom', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', '   %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionmarginimagesmc', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.04')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'captionmarginimages', True)
    nconf = replace_argument(files[fl][ra], 1, '-0.04')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sourcecodefonts', True)
    nconf = replace_argument(files[fl][ra], 1, '\\footnotesize').replace(' {', '{').replace('      %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'stylecitereferences', True)
    nconf = replace_argument(files[fl][ra], 1, 'bibtex')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmargini {', True)
    nconf = replace_argument(files[fl][ra], 1, '21.9').replace('  %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginii {', True)
    nconf = replace_argument(files[fl][ra], 1, '21.9').replace('  %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginiii {', True)
    nconf = replace_argument(files[fl][ra], 1, '21.9')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'sitemsmarginiv {', True)
    nconf = replace_argument(files[fl][ra], 1, '0').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'subcaptionfsize', True)
    nconf = replace_argument(files[fl][ra], 1, 'scriptsize').replace('%', ' %').replace('{', ' {')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'fontdocument', True)
    nconf = replace_argument(files[fl][ra], 1, 'roboto').replace('%', ' %')
    files[fl][ra] = nconf

    ra, _ = find_block(files[fl], 'stylecitereferences', True)
    files[fl][ra] = '\\def\\stylecitereferences {bibtex}  % Estilo cita/ref {bibtex,custom}\n'
    ra, _ = find_block(files[fl], 'captionfontsize', True)
    files[fl][ra] = '\\def\\captionfontsize{footnotesize} % Tamaño de fuente de los caption\n'
    ra, _ = find_block(files[fl], 'fonturl', True)
    files[fl][ra] += '\\def\\frametextjustified {true}     % Justifica todos los párrafos de los frames\n'

    # -------------------------------------------------------------------------
    # CAMBIA LAS ECUACIONES
    # -------------------------------------------------------------------------
    fl = 'src/cmd/equation.tex'
    files[fl] = find_delete_block(files[fl], '% Insertar una ecuación en el índice', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = 'src/env/environments.tex'
    files[fl] = find_delete_block(files[fl], '% Crea una sección de resumen', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea una sección de referencias solo para bibtex', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea una sección de anexos', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Crea un entorno para insertar ecuaciones en el índice',
                                  white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA OTROS
    # -------------------------------------------------------------------------
    fl = 'src/cmd/other.tex'
    files[fl] = find_delete_block(files[fl], '% Cambia el tamaño de la página', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Ofrece diferentes formatos de pagina', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Función personalizada \\cleardoublepage', white_end_block=True)

    # -------------------------------------------------------------------------
    # CAMBIA DEFS
    # -------------------------------------------------------------------------
    fl = 'src/defs.tex'
    ra, _ = find_block(files[fl], 'xcolor', True)
    for _ in range(3):
        files[fl].pop(ra)

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['hyperref', 'sectsty', 'tocloft', 'notoccite', 'titlesec', 'graphicx', 'totpages']
    for idel in idel:
        ra, _ = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl] = find_delete_block(files[fl], '% Dimensiones y geometría del documento', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Cambia el estilo de los títulos', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Referencias', white_end_block=True)
    ra, _ = find_block(files[fl], '\\showappendixsecindex')
    nl = ['\\def\\showappendixsecindex {false}\n',
          files[fl][ra]]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    # Agrega variables borradas
    ra, _ = find_block(files[fl], '% Muestra los números de línea')
    nl = ['}\n'
          '\\def\\showlinenumbers {true}\n'
          '\\def\\marginlinenumbers {7.5}\n'
          '\\def\\linenumbercolor {gray}\n',
          '\\ifthenelse{\\equal{\\showlinenumbers}{true}}{ % Muestra los números de línea\n']
    files[fl] = replace_block_from_list(files[fl], nl, ra - 1, ra - 1)

    files[fl].pop()
    files[fl].append('\\usefonttheme{professionalfonts}\n\\usepackage{transparent}\n')

    # Citas post carga de idioma
    ra, _ = find_block(files[fl], '% Formato citas natbib')
    rb, _ = find_block(files[fl], '% Fin carga natbib')
    files[fl] = replace_block_from_list(files[fl], [], ra, rb - 1)
    ra, _ = find_block(files[fl], '% Citado')
    rb, _ = find_block(files[fl], '% Formato citas custom')
    files[fl] = replace_block_from_list(files[fl], [], ra, rb + 1)

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_presentacion = file_to_list('src/cfg/init_presentacion.tex')

    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Agrega compatibilidad de sub-sub-sub-secciones al TOC', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Se crean variables si se borraron', True, iadd=-2, jadd=-1)
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\isundefined{\\documentsubtitle}}{', True)
    files[fl] = find_delete_block(files[fl], 'Actualización margen títulos', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Se añade listings (código fuente) a tocloft', True, iadd=-2)
    files[fl] = find_delete_block(files[fl], '\\pdfminorversion', white_end_block=True, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Configuración anexo', white_end_block=True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Desactiva \\cleardoublepage hasta el inicio del documento',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Modifica el formato de nuevas páginas predoc y \\cleardoublepage',
                                  jadd=1)
    ra, _ = find_block(files[fl], '\\coreintializetitlenumbering')
    files[fl].pop(ra)

    # Borra línea definiciones
    ra, _ = find_block(files[fl], '\\checkvardefined{\\universitydepartmentimagecfg}')
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
              '\\checkvardefined{\\documenttitle}', '\\g@addto@macro\\documenttitle']:
        ra, _ = find_block(files[fl], i)
        files[fl].pop(ra)

    # Elimina cambio del indice en bibtex
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\bibtexindexbibliography}{true}}{')

    # Elimina subtitulo
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\documentsubtitle}{}}{', jadd=1)

    # Color de página
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\equal{\\pagescolor}{white}}{}{', white_end_block=True,
                                  jadd=-1)

    # Estilo de títulos
    files[fl] = find_delete_block(files[fl], '% Configura el número de las secciones', white_end_block=True,
                                  iadd=-1)

    # Cambia las bibliografias
    nl = find_extract(init_presentacion, '% Configuración de referencias y citas', white_end_block=True)
    ra, _ = find_block(files[fl], '% Configuración de referencias y citas')
    _, rb = find_block(files[fl], '% Referencias en 2 columnas', blankend=True)
    files[fl] = replace_block_from_list(files[fl], nl, ra, rb - 1)

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
              '% Establece temas custom',
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
    nl = find_extract(aux_pageconf, '% Configura el tabularframe', True, iadd=-1)
    for _ in range(2):
        files[fl].pop()
    files[fl] = add_block_from_list(files[fl], nl, LIST_END_LINE)
    ra, _ = find_block(files[fl], '% Márgenes de páginas y tablas')
    files[fl][ra] = files[fl][ra].replace('páginas y ', '')
    files[fl].append('}\n')

    # -------------------------------------------------------------------------
    # FINALCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/final.tex'
    files[fl] = find_delete_block(files[fl], '% Se usa número de páginas en arábigo', white_end_block=True, jadd=-1,
                                  iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Reinicia número de página', white_end_block=True, jadd=-1, iadd=-1)
    files[fl] = find_delete_block(files[fl], 'Establece el estilo de las sub-sub-sub-secciones', white_end_block=True,
                                  jadd=-1, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Se restablecen headers y footers', white_end_block=True, jadd=-1,
                                  iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Reestablece los valores del estado de los títulos',
                                  white_end_block=True, iadd=-1)
    ra, _ = find_block(files[fl], '% Crea funciones para numerar objetos')
    files[fl].pop(ra - 2)
    ra, _ = find_block(files[fl], '% Se restablecen números de página y secciones')
    files[fl][ra + 1] = '\t% -------------------------------------------------------------------------\n'
    files[fl] = find_delete_block(files[fl], '% Muestra los números de línea', white_end_block=True, jadd=1, iadd=-1)
    files[fl] = find_delete_block(files[fl], '% Agrega páginas dependiendo del formato', iadd=-1, jadd=1)
    files[fl] = find_delete_block(files[fl], '% Reestablece \\cleardoublepage', iadd=-1,
                                  white_end_block=True)
    ra, _ = find_block(files[fl], '\\setcounter{footnote}{0}')
    files[fl][ra + 1] = '\t\n'

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
    files[fl] = find_delete_block(files[fl], '% Activa la numeración en las secciones',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Chequea si los capítulos han sido iniciados',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Chequea si una sección han sido iniciada',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Chequea si una subsección han sido iniciada',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Chequea si una subsubsección han sido iniciada',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Parcha sub-sub-subsecciones',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Insertar un capítulo sin número',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Configura textos a añadir antes de secciones',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Configura que entornos pueden funcionar',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Parcha el formato de capítulos',
                                  white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Chequea si los capítulos están activados',
                                  white_end_block=True)

    ra, _ = find_block(files[fl], '% Parcha el formato de secciones al pasar desde una anum')
    files[fl].pop(ra - 1)

    find_remove_recursive_line(files[fl], '\\coreintializetitlenumbering')
    find_remove_recursive_line(files[fl], '\\GLOBALchapternumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALsectionanumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALsubsectionanumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALsubsubsectionanumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALtitlerequirechapter')
    find_remove_recursive_line(files[fl], '\\GLOBALtitleinitchapter')
    find_remove_recursive_line(files[fl], '\\GLOBALtitleinitsection')
    find_remove_recursive_line(files[fl], '\\GLOBALtitleinitsubsection')
    find_remove_recursive_line(files[fl], '\\GLOBALtitleinitsubsubsection')
    find_remove_recursive_line(files[fl], '\\GLOBALtitleinitsubsubsubsection')
    find_remove_recursive_line(files[fl], '\\corecheckchapterinitialized')
    find_remove_recursive_line(files[fl], '\\corechecksectioninitialized')
    find_remove_recursive_line(files[fl], '\\corechecksubsectioninitialized')
    find_remove_recursive_line(files[fl], '\\corechecksubsubsectioninitialized')

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '\\newcommand{\\bgtemplatetestimg}{')
    files[fl] = find_delete_block(files[fl], '% Definición de formato de secciones', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '\\def\\bgtemplatetestcode {d0g3}', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Cambia márgenes de las páginas [cm]', white_end_block=True)
    ra, _ = find_block(files[fl], '% Imagen de prueba tikz')
    files[fl].pop(ra)

    find_remove_recursive_line(files[fl], '\\GLOBALchapternumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALsectionanumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALsubsectionanumenabled')
    find_remove_recursive_line(files[fl], '\\GLOBALsubsubsectionanumenabled')

    ra, rb = find_block(files[fl], '% Definición de variables globales', blankend=True)
    for i in range(ra, rb):
        files[fl][i] = files[fl][i].replace('    %', '%')

    # Cambia encabezado archivos
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

    # Se exporta el proyecto normal
    if dosave:
        export_subdeptos_subtemplate(release, subrlfolder, mainfile, distfolder)

    # Limpia el diccionario
    if doclean:
        clear_dict(RELEASES[REL_INFORME], 'FILES')

    # Retorna a root
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
    files['library.bib'] = file_to_list('library.bib')
    files['main.tex'] = file_to_list('main_tesis.tex')
    files['natnumurl.bst'] = file_to_list('natnumurl.bst')
    files['src/cfg/final.tex'] = copy.copy(mainf['src/cfg/final.tex'])
    files['src/cfg/init.tex'] = copy.copy(mainf['src/cfg/init.tex'])
    files['src/cfg/page.tex'] = copy.copy(mainf['src/cfg/page.tex'])
    files['src/cmd/column.tex'] = copy.copy(mainf['src/cmd/column.tex'])
    files['src/cmd/core.tex'] = copy.copy(mainf['src/cmd/core.tex'])
    files['src/cmd/equation.tex'] = copy.copy(mainf['src/cmd/equation.tex'])
    files['src/cmd/image.tex'] = copy.copy(mainf['src/cmd/image.tex'])
    files['src/cmd/math.tex'] = copy.copy(mainf['src/cmd/math.tex'])
    files['src/cmd/other.tex'] = copy.copy(mainf['src/cmd/other.tex'])
    files['src/cmd/title.tex'] = copy.copy(mainf['src/cmd/title.tex'])
    files['src/config.tex'] = copy.copy(mainf['src/config.tex'])
    files['src/defs.tex'] = copy.copy(mainf['src/defs.tex'])
    files['src/env/environments.tex'] = copy.copy(mainf['src/env/environments.tex'])
    files['src/env/imports.tex'] = copy.copy(mainf['src/env/imports.tex'])
    files['src/etc/example.tex'] = file_to_list('src/etc/example_tesis.tex')
    files['src/page/index.tex'] = copy.copy(mainf['src/page/index.tex'])
    files['src/page/portrait.tex'] = file_to_list('src/page/portrait_tesis.tex')
    files['src/style/code.tex'] = copy.copy(mainf['src/style/code.tex'])
    files['src/style/other.tex'] = copy.copy(mainf['src/style/other.tex'])
    files['template.tex'] = file_to_list('template_tesis.tex')
    mainfile = release['MAINFILE']
    examplefile = 'src/etc/example.tex'
    subrlfolder = release['ROOT']
    stat = release['STATS']
    configfile = 'src/config.tex'
    distfolder = release['DIST']

    # Constantes
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionhead = '% Versión:      {0} ({1})\n'

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
    ra, _ = find_block(files[fl], '\\sssectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\normalsize').replace('    %', '%').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\ssectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\large')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], '\\sectionfontsize', True)
    nconf = replace_argument(files[fl][ra], 1, '\\Large')
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
    ra, _ = find_block(files[fl], '\\pagemargintop', True)
    nconf = replace_argument(files[fl][ra], 1, '2')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'hfstyle', True)
    nconf = replace_argument(files[fl][ra], 1, 'style7')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgbookmarksopenlevel', True)
    nconf = replace_argument(files[fl][ra], 1, '0')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'addindexsubtobookmarks', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('{', ' {')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'showappendixsecindex', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'formatnumapchapter', True)
    nconf = replace_argument(files[fl][ra], 1, '\\Alph').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'formatnumapsection', True)
    nconf = replace_argument(files[fl][ra], 1, '\\arabic').replace('  %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'cfgshowbookmarkmenu', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'addindexsubtobookmarks', True)
    nl = ['\\def\\addabstracttobookmarks {true} % Añade el resumen a los marcadores del pdf\n',
          '\\def\\addagradectobookmarks {true}  % Añade el agradecimiento a los marcadores\n',
          files[fl][ra]
          ]
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra - 1)
    ra, _ = find_block(files[fl], 'namereferences', True)
    nconf = replace_argument(files[fl][ra], 1, 'Bibliografía').replace(' %', '%')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'nameltcont', True)
    nconf = replace_argument(files[fl][ra], 1, 'Tabla de Contenido').replace('%', '  %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'footnoterulepage', True)
    nconf = replace_argument(files[fl][ra], 1, 'true').replace('%', ' %')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'nameltfigure', True)
    nconf = replace_argument(files[fl][ra], 1, 'Índice de Ilustraciones').replace(' {', '{')
    files[fl][ra] = nconf
    ra, _ = find_block(files[fl], 'nameabstract', True)
    nl = [files[fl][ra],
          '\\def\\nameagradec {Agradecimientos}    % Nombre del cap. de agradecimientos\n',
          ]
    files[fl] = add_block_from_list(files[fl], nl, ra, True)

    # Configuraciones que se borran
    cdel = ['portraitstyle', 'firstpagemargintop', 'bibtexenvrefsecnum',
            'predocpageromannumber', 'predocresetpagenumber', 'indexnewpagec', 'indexnewpagef',
            'indexnewpaget', 'showindexofcontents', 'indexsectionfontsize', 'indexsectionstyle', 'indexnewpagee',
            'hfpdashcharstyle', 'portraittitlecolor']
    for cdel in cdel:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl].pop(ra)
    for cdel in []:
        ra, _ = find_block(files[fl], cdel, True)
        files[fl][ra] = files[fl][ra].replace('   %', '%')  # Reemplaza espacio en comentarios de la lista
    ra, _ = find_block(files[fl], '% ESTILO PORTADA Y HEADER-FOOTER', True)
    files[fl][ra] = '% ESTILO HEADER-FOOTER\n'

    # Añade nuevas entradas
    files[fl] = search_append_line(files[fl], '% CONFIGURACIÓN DE LOS COLORES DEL DOCUMENTO',
                                   '\\def\\chaptercolor {black}          % Color de los capítulos\n')
    files[fl] = search_append_line(files[fl], 'anumsecaddtocounter',
                                   '\\def\\chapterfontsize {\\huge}       % Tamaño fuente de los capítulos\n')
    files[fl] = search_append_line(files[fl], 'chapterfontsize',
                                   '\\def\\chapterfontstyle {\\bfseries}  % Estilo fuente de los capítulos\n')
    files[fl] = search_append_line(files[fl], '% ESTILO HEADER-FOOTER',
                                   '\\def\\chapterstyle {style1}         % Estilo de los capítulos (12 estilos)\n')

    # -------------------------------------------------------------------------
    # CAMBIA IMPORTS
    # -------------------------------------------------------------------------
    fl = 'src/env/imports.tex'
    idel = ['ragged2e']
    for idel in idel:
        ra, _ = find_block(files[fl], idel, True)
        files[fl].pop(ra)
    files[fl].pop()
    a, _ = find_block(files[fl], '\\usepackage{apacite}', True)
    files[fl][a] = files[fl][a].replace('{apacite}', '[nosectionbib]{apacite}')

    # -------------------------------------------------------------------------
    # CAMBIO INITCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/init.tex'
    init_tesis = file_to_list('src/cfg/init_tesis.tex')

    files[fl] = find_delete_block(files[fl], 'Se revisa si se importa tikz', True, iadd=-1)
    files[fl] = find_delete_block(files[fl], '\\ifthenelse{\\isundefined{\\authortable}}{', True)
    ra, _ = find_block(files[fl], '\\checkvardefined{\\coursecode}', True)

    # Añade bloque de variables definidas
    nl = find_extract(init_tesis, '% Inicialización de variables', white_end_block=True)
    nl.pop(0)
    nl.append(files[fl][ra])
    files[fl] = replace_block_from_list(files[fl], nl, ra, ra)

    # Elimina referencias en dos columnas
    ra, _ = find_block(files[fl], '{\\begin{multicols}{2}[\\section*{\\refname}', True)
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

    # Configura estilo capítulos
    files[fl] = search_append_line(files[fl], '\\titlespacing*{\\subsubsubsection}',
                                   '\\chaptertitlefont{\\color{\\chaptercolor} \\chapterfontsize \\chapterfontstyle \\selectfont}\n')

    # -------------------------------------------------------------------------
    # ÍNDICE
    # -------------------------------------------------------------------------
    fl = 'src/page/index.tex'
    index_tesis = file_to_list('src/page/index_tesis.tex')

    # Agrega inicial
    ra, _ = find_block(files[fl], 'Crea nueva página y establece estilo de títulos', True)
    nl = find_extract(index_tesis, '% Inicio índice, desactiva espacio entre objetos', True)
    files[fl] = add_block_from_list(files[fl], nl, ra - 2)

    ra, _ = find_block(files[fl], '% Termina el bloque de índice', True)
    nl = find_extract(index_tesis, '% Final del índice, restablece el espacio', True)
    files[fl] = add_block_from_list(files[fl], nl, ra + 13)
    files[fl][ra + 12] += '\t'
    files[fl][ra + 17] += '\t'

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
    ra, _ = find_block(files[fl], '\\renewcommand{\\appendixtocname}{\\nameappendixsection}')
    files[fl] = add_block_from_list(files[fl], [files[fl][ra],
                                                '\t\\renewcommand{\\chaptername}{\\namechapter}  % Nombre de los capítulos\n'],
                                    ra)
    ra, rb = find_block(files[fl], '% Muestra los números de línea', True)
    nl = find_extract(page_tesis, '% Añade página en blanco')
    files[fl] = add_block_from_list(files[fl], nl, rb, True)

    # -------------------------------------------------------------------------
    # ENVIRONMENTS
    # -------------------------------------------------------------------------
    fl = 'src/env/environments.tex'
    env_tesis = file_to_list('src/env/environments_tesis.tex')

    # Reemplaza bloques
    w = '% Crea una sección de referencias solo para bibtex'
    nl = find_extract(env_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True, jadd=-1)
    w = '% Crea una sección de resumen'
    nl = find_extract(env_tesis, w, True)
    files[fl] = find_replace_block(files[fl], w, nl, True, jadd=-1)
    _, rb = find_block(files[fl], w, True)
    nl = find_extract(env_tesis, '% Crea una sección de dedicatoria', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)
    _, rb = find_block(files[fl], '% Crea una sección de dedicatoria', True)
    nl = find_extract(env_tesis, '% Crea una sección de agradecimientos', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)
    _, rb = find_block(files[fl], '\\newenvironment{appendixd}{%', True)
    nl = find_extract(env_tesis, '% Entorno simple de apéndices', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)
    _, rb = find_block(files[fl], '% Entorno simple de apéndices', True)
    nl = find_extract(env_tesis, '% Entorno capítulos apéndices con título', True)
    files[fl] = add_block_from_list(files[fl], nl, rb, True)

    # Agrega saltos de línea
    for w in ['% Llama al entorno de resumen', '% Crea una sección de dedicatoria',
              '% Crea una sección de agradecimientos', '% Entorno simple de apéndices',
              '% Entorno capítulos apéndices con título']:
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
    for _ in range(2):
        ra, _ = find_block(files[fl], '\\global\\def\\GLOBALtitlerequirechapter {false}')
        files[fl][ra] = files[fl][ra].replace('{false}', '{true}')

    # -------------------------------------------------------------------------
    # FINALCONF
    # -------------------------------------------------------------------------
    fl = 'src/cfg/final.tex'
    ra, _ = find_block(files[fl], '\\global\\def\\GLOBALtitlerequirechapter {false}')
    files[fl][ra] = files[fl][ra].replace('{false}', '{true}')

    # -------------------------------------------------------------------------
    # CORE FUN
    # -------------------------------------------------------------------------
    fl = 'src/cmd/core.tex'
    files[fl] = find_delete_block(files[fl], '% Imagen de prueba tikz', white_end_block=True)
    files[fl] = find_delete_block(files[fl], '% Para la compatibilidad con template-tesis se define el capítulo',
                                  white_end_block=True)

    # -------------------------------------------------------------------------
    # TITLE
    # -------------------------------------------------------------------------
    fl = 'src/cmd/title.tex'
    ra, _ = find_block(files[fl], 'GLOBALtitlechapterenabled', True)
    nconf = replace_argument(files[fl][ra], 1, 'true')
    files[fl][ra] = nconf

    # Cambia encabezado archivos
    change_header_tex_files(files, release, headersize, headerversionpos, versionhead)

    # Guarda los archivos
    os.chdir(mainroot)
    if dosave:
        copy_assemble_template(files, subrlfolder, headersize, configfile, mainfile, examplefile)

    printfun(MSG_FOKTIMER.format((time.time() - t)))

    # Compila el archivo
    if docompile and dosave:
        compile_template(subrlfolder, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

    # Se exporta el proyecto normal
    if dosave:
        export_subdeptos_subtemplate(release, subrlfolder, mainfile, distfolder,
                                     deptimg='uchile2', finalimg='uchile2')

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
    main_data = file_to_list(mainfile)
    headersize = find_line(main_data, '% Licencia MIT:') + 2
    headerversionpos = find_line(main_data, '% Versión:      ')
    versionheader = '% Versión:      {0} ({1})\n'

    # Se obtiene el día
    dia = time.strftime('%d/%m/%Y')

    # Se crea el header de la versión
    versionhead = versionheader.format(version, dia)

    # Se buscan números de lineas de hyperref
    initconf_data = file_to_list(initconffile)
    l_tdate, d_tdate = find_line_str(initconf_data, 'Template.Date', True)
    l_thash, d_thash = find_line_str(initconf_data, 'Template.Version.Hash', True)
    l_ttype, d_ttype = find_line_str(initconf_data, 'Template.Type', True)
    l_tvdev, d_tvdev = find_line_str(initconf_data, 'Template.Version.Dev', True)
    l_tvrel, d_tvrel = find_line_str(initconf_data, 'Template.Version.Release', True)
    l_vcmtd, d_vcmtd = find_line_str(initconf_data, 'pdfproducer', True)

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
            fl = open(f, encoding='utf8')
            for line in fl:
                data.append(line)
            fl.close()
        except:
            printfun(f'Error al cargar el archivo {f}')

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
            newfl = open(f, 'w', encoding='utf8')
            for j in data:
                newfl.write(j)
            newfl.close()

    if dosave:
        # Mueve el archivo de configuraciones
        copyfile(configfile, 'template_config.tex')

        # Ensambla el archivo del template
        assemble_template_file(files['source_template.tex'], configfile, '', headersize, files)

    printfun(MSG_FOKTIMER.format(time.time() - t))

    # Compila el archivo
    if docompile and dosave:
        compile_template(None, printfun, mainfile, savepdf, addstat, statsroot,
                         release, version, stat, versiondev, dia, versionhash, plotstats)

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
