"""
EXPORT-SUBTEMPLATE
Genera distintos sub-releases y exporta los templates

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

__all__ = ['CreateVersion']

# Importación de librerías
from extlbx import __author__, __version__
from extlbx.releases import REL_PROFESSIONALCV, REL_INFORME, REL_CONTROLES, REL_AUXILIAR, \
    RELEASES, REL_REPORTE, REL_TESIS, REL_ARTICULO, REL_PRESENTACION, REL_POSTER
from extlbx.convert import *
from extlbx.version import *
from extlbx.sound import Sound
from extlbx.resources import *
from extlbx.utils import *

import ctypes
import tkinter as tk
from tkinter import font
from tkinter import messagebox
from extlbx.vframe import VerticalScrolledFrame

from extlbx.pyperclip import copy as extlbcbpaste
from functools import partial

import json
import logging
import os
import signal
import traceback

PIL_EXIST = True

try:
    # noinspection PyUnresolvedReferences
    from PIL import ImageTk
except ImportError:
    PIL_EXIST = False

# Constantes
GITHUB_PDF_COMMIT = 'Se agrega pdf v{0} de {1}'
GITHUB_PRINT_MSG = 'SUBIENDO v{0} DE {1} ... '
GITHUB_REP_COMMIT = 'Version {0}'
GITHUB_STAT_COMMIT = 'Estadisticas compilacion v{0} de {1}'
GITHUB_UPDATE_COMMIT = 'Update upload.json'
HELP = {
    'ESC': 'Cierra la aplicación',
    'F1': 'Muestra esta ayuda',
    'F2': 'Muestra las configuraciones',
    'F3': 'Muestra el acerca de',
    'F4': 'Limpia la ventana',
    'ENTER': 'Inicia la rutina'
}
LIMIT_MESSAGES_CONSOLE = 1000
LOG_FILE = 'log.txt'
LOG_MSG = {
    'CHANGED': 'Cambiando subrelease a {0} v{1}',
    'CONFIG': 'Estableciendo parametro <{0}> en <{1}>',
    'COPY': 'Copiando version {0} de {1} al portapapeles',
    'CREATE_V': 'Creando version {0} de {1}',
    'CREATE_V_COMPLETE': 'Proceso finalizado',
    'END': 'Programa cerrado',
    'OPEN': 'Inicio Export-Subtemplate v{0}',
    'OTHER': '{0}',
    'PRINTCONFIG': 'Mostrando configuraciones',
    'SHOWABOUT': 'Mostrando acerca de',
    'SHOWHELP': 'Mostrando la ayuda',
    'SUBV+': 'Creando subversion mayor de {0} a {1}',
    'SUBV-': 'Creando subversion menor de {0} a {1}',
    'UPLOAD_COMPLETE': 'Carga completa',
    'UPLOAD_V': 'Subiendo version {0} de {1} a GitHub',
}
TITLE = 'Export-Subtemplate'
TITLE_LOADING = '{0} | Espere ...'
TITLE_UPLOADING = '{0} | Cargando a GitHub ...'


# noinspection PyCompatibility,PyBroadException,PyCallByClass,PyUnusedLocal,PyShadowingBuiltins
class CreateVersion(object):
    """
    Pide la versión al usuario y genera releases.
    """

    def __init__(self):

        def _checkver(*args):
            """
            Función auxiliar que chequea que la versión ingresada sea correcta.

            :param sv: String var de la versión
            :return:
            """
            ver = self._versionstr.get()
            try:
                v, dev, h = mk_version(ver)
                if not validate_ver(dev, self._lastloadedv):
                    raise Exception('Version invalida')
                self._startbutton.configure(state='normal', cursor='hand2')
                self._versiontxt.bind('<Return>', self._start)
                self._validversion = True
            except Exception as exc:
                print(exc)
                self._startbutton.configure(state='disabled', cursor='arrow')
                self._versiontxt.bind('<Return>')
                self._validversion = False

        def _create_ver_d(*args):
            """
            Crea una subversión mayor.

            :param args: Argumentos opcionales
            :return:
            """
            for j in RELEASES.keys():
                if self._release.get() == RELEASES[j]['NAME']:
                    v = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[j]['STATS']['FILE']).split(' ')[0]
                    self._versionstr.set(v_down(v))
                    self._startbutton.focus_force()
                    self._log('SUBV-', text=[RELEASES[j]['NAME'], v])
                    return

        def _create_ver_u(*args):
            """
            Crea una versión mayor.

            :param args: Argumentos opcionales
            :return:
            """
            for j in RELEASES.keys():
                if self._release.get() == RELEASES[j]['NAME']:
                    v = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[j]['STATS']['FILE']).split(' ')[0]
                    self._versionstr.set(v_up(v))
                    self._startbutton.focus_force()
                    self._log('SUBV+', text=[RELEASES[j]['NAME'], v])
                    return

        def _copyver(*args):
            """
            Copia la versión del template seleccionado en el clipboard.

            :param args: Argumentos opcionales
            :return:
            """
            for j in RELEASES.keys():
                if self._release.get() == RELEASES[j]['NAME']:
                    v = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[j]['STATS']['FILE']).split(' ')[0]
                    extlbcbpaste(self._getconfig('CLIPBOARD_FORMAT').format(v))
                    if self._getconfig('INFOCONSOLE'):
                        self._print('INFO: VERSION COPIADA')
                    self._log('COPY', text=[v, RELEASES[j]['NAME']])
                    return
            if self._getconfig('INFOCONSOLE'):
                self._print('ERROR: TEMPLATE NO ESCOGIDO')
            extlbcbpaste('')

        def _clear(*args):
            """
            Limpia la ventana.

            :param args: Argumentos opcionales
            :return:
            """
            self._clearconsole(-1)
            self._release.set('Seleccione template')
            self._versiontxt.delete(0, 'end')
            self._root.focus()

        def _kill(*args):
            """
            Destruye la ventana.

            :return:
            """

            def _oskill():
                if is_windows():
                    os.system('taskkill /PID {0} /F'.format(str(os.getpid())))
                else:
                    os.kill(os.getpid(), signal.SIGKILL)

            self._log('END')
            self._root.destroy()
            exit()

        def _printconfig(*args):
            """
            Imprime las configuraciones.

            :param args: Argumentos opcionales
            :return: None
            """
            self._clearconsole()
            self._print('CONFIGURACIONES')
            maxlen = 0
            key = self._configs.keys()
            key.sort(key=natural_keys)
            for j in key:
                if self._configs[j]['EVENT']:
                    maxlen = max(maxlen, len(j))
            for j in key:
                if self._configs[j]['EVENT']:
                    self._print('\t{0} [{1}]'.format(j.ljust(maxlen), self._getconfig(j)))
            for j in range(5):
                self._print('\n')
            self._log('PRINTCONFIG')

        def _scroll_console(event):
            """
            Función que atrapa el evento del scrolling y mueve los comandos.

            :param event: Evento
            :return: None
            """
            if -175 < event.x < 240 and 38 < event.y < 136:
                if is_windows():
                    if -1 * (event.delta / 100) < 0:
                        move = -1
                    else:
                        move = 2
                elif is_osx():
                    if -1 * event.delta < 0:
                        move = -2
                    else:
                        move = 2
                else:
                    if -1 * (event.delta / 100) < 0:
                        move = -1
                    else:
                        move = 2
                if len(self._console) < 5 and move < 0:
                    return
                self._info_slider.canv.yview_scroll(move, 'units')

        def _set_config(paramname, paramvalue, *args):
            """
            Guarda la configuración.

            :param paramname: Nombre del parámetro
            :param paramvalue: Valor del parámetro
            :return:
            """
            if paramvalue == '!':
                self._configs[paramname]['VALUE'] = not self._configs[paramname]['VALUE']
            else:
                self._configs[paramname]['VALUE'] = paramvalue
            vl = [paramname, self._configs[paramname]['VALUE']]
            self._print('SE ESTABLECIÓ <{0}> EN {1}'.format(*vl))
            self._log('CONFIG', text=vl, mode='CFG')

        def _set_templatever(template_name, *args):
            """
            Establece el tipo de template en la lista.

            :param template_name: ID del template
            :return:
            """
            self._release.set(template_name)

        def _show_about(*args):
            """
            Imprime acerca de en consola.

            :param args: Argumentos opcionales
            :return: None
            """
            self._clearconsole(-1)
            self._print('ACERCA DE')
            self._print('\tExport Template v{0}'.format(__version__))
            self._print('\tAutor: {0}\n'.format(__author__))
            license = file_to_list(EXTLBX_LICENSE)
            for line in license:
                self._print(line.strip(), scrolldir=-1)
            self._log('SHOWABOUT')

        def _show_help(*args):
            """
            Imprime la ayuda en consola.

            :param args: Argumentos opcionales
            :return: None
            """
            self._clearconsole(-1)
            self._print('AYUDA')
            keys = list(HELP.keys())
            keys.sort()
            for k in keys:
                self._print('\t{0}: {1}'.format(k, HELP[k]), scrolldir=-1)
            self._log('SHOWHELP')

        def _update_ver(*args):
            """
            Pasa el foco al campo de versión, carga versiones de cada release.

            :param args: Argumentos opcionales
            :return:
            """
            self._versiontxt.focus()
            self._versionstr.trace_vdelete('w', self._versiontrace)
            self._versionstr.set('')
            self._versiontrace = self._versionstr.trace('w', self._checkver)
            self._clearconsole()
            for j in RELEASES.keys():
                if self._release.get() == RELEASES[j]['NAME']:
                    v = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[j]['STATS']['FILE'])
                    self._versiontxt.configure(state='normal')
                    self._print('SELECCIONADO: {0}'.format(RELEASES[j]['NAME']))
                    self._print('ÚLTIMA VERSIÓN: {0}'.format(v))
                    if self._uploaded[j] != v.split(' ')[0]:
                        self._uploadstatebtn('on')
                    else:
                        self._uploadstatebtn('off')
                    self._lastloadedv = v.split(' ')[0]
                    self._log('CHANGED', text=[RELEASES[j]['NAME'], v])
                    return

        if os.name == 'nt':
            # noinspection PyBroadException
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        self._root = tk.Tk()
        self._root.protocol('WM_DELETE_WINDOW', _kill)

        self._sounds = Sound()

        # Se obtienen configuraciones
        with open(EXTLBX_CONFIGS, encoding='utf8') as json_data:
            d = json.load(json_data)
            self._configs = d
        self._lascpdf = True
        self._lastsav = True

        # Se obtiene el root del archivo actual
        self._configs["MAIN_ROOT"]["VALUE"] = str(os.path.abspath(os.path.dirname(__file__))).replace('\\', '/') + '/'

        # Ajusta tamaño ventana
        size = [self._configs['WINDOW_SIZE']['WIDTH'], self._configs['WINDOW_SIZE']['HEIGHT']]
        self._root.minsize(width=size[0], height=size[1])
        self._root.geometry('%dx%d+%d+%d' % (size[0], size[1], (self._root.winfo_screenwidth() - size[0]) / 2,
                                             (self._root.winfo_screenheight() - size[1]) / 2))
        self._root.resizable(width=False, height=False)
        self._root.focus_force()

        # Estilo ventana
        self._root.title(TITLE)
        if is_osx():
            self._root.iconbitmap(EXTLBX_ICON_MAC)
            img = tk.Image('photo', file=EXTLBX_ICON_MAC)
            # noinspection PyProtectedMember,PyUnresolvedReferences
            self._root.tk.call('wm', 'iconphoto', self._root._w, img)
        else:
            self._root.iconbitmap(EXTLBX_ICON)
        fonts = [font.Font(family='Courier', size=13 if is_osx() else 8),
                 font.Font(family='Verdana', size=6),
                 font.Font(family='Times', size=10),
                 font.Font(family='Times', size=10, weight=font.BOLD),
                 font.Font(family='Verdana', size=6, weight=font.BOLD),
                 font.Font(family='Verdana', size=10),
                 font.Font(family='Verdana', size=7)]

        f1 = tk.Frame(self._root, border=4)
        f1.pack(fill=tk.X)
        f2 = tk.Frame(self._root)
        f2.pack(fill=tk.BOTH)

        # Selección versión a compilar
        rels = []
        p = 1
        ky = list(RELEASES.keys())
        ky.sort()
        for b in ky:
            rels.append(RELEASES[b]['NAME'])
            self._root.bind('<Control-Key-{0}>'.format(p), partial(_set_templatever, RELEASES[b]['NAME']))
            p += 1
        self._release = tk.StringVar(self._root)
        self._release.set('Seleccione template')
        w = tk.OptionMenu(f1, self._release, *tuple(rels))
        w['width'] = 20
        w['relief'] = tk.GROOVE
        w['anchor'] = tk.W
        w['cursor'] = 'hand2'
        w.pack(side=tk.LEFT)
        self._release.trace('w', _update_ver)

        # Campo de texto para versión
        tk.Label(f1, text='Nueva versión:').pack(side=tk.LEFT, padx=(30, 0))
        self._checkver = _checkver
        self._versionstr = tk.StringVar(self._root)
        self._versiontrace = self._versionstr.trace('w', self._checkver)
        self._versiontxt = tk.Entry(f1, relief=tk.GROOVE, width=8,
                                    font=fonts[5], textvariable=self._versionstr)
        self._versiontxt.configure(state='disabled')
        self._versiontxt.pack(side=tk.LEFT, padx=5, pady=2)
        self._versiontxt.focus()
        self._validversion = False
        self._lastloadedv = ''

        # Botón iniciar
        self._startbutton = tk.Button(f1, text='Iniciar', state='disabled', relief=tk.GROOVE, command=self._start)
        self._startbutton.pack(side=tk.LEFT, padx=3, anchor=tk.W)

        # Uploads
        if PIL_EXIST:
            self._upload_imgs = [
                ImageTk.PhotoImage(file=EXTLBX_BTN_UPLOAD),
                ImageTk.PhotoImage(file=EXTLBX_BTN_UPLOAD_DISABLED)
            ]
            # noinspection PyTypeChecker
            self._uploadbutton = tk.Button(f1, image=self._upload_imgs[0], relief=tk.GROOVE, height=30, width=30,
                                           command=self._upload_github, border=0)
        else:
            self._uploadbutton = tk.Button(f1, relief=tk.GROOVE, height=20, width=20,
                                           command=self._upload_github, border=0)
            self._upload_imgs = None
        self._uploadbutton.pack(side=tk.RIGHT, padx=0, anchor=tk.E)
        self._uploadstatebtn('off')
        self._checkuploaded()

        # Consola
        self._info_slider = VerticalScrolledFrame(f2)
        self._info_slider.canv.config(bg='#000000')
        self._info_slider.pack(pady=2, anchor=tk.NE, fill=tk.BOTH, padx=1)
        self._info = tk.Label(self._info_slider.interior, text='', justify=tk.LEFT, anchor=tk.NW, bg='black',
                              fg='white',
                              wraplength=self._configs['WINDOW_SIZE']['WIDTH'],
                              font=fonts[0], relief=tk.FLAT, border=2,
                              cursor='arrow')
        self._info.pack(anchor=tk.NW, fill=tk.BOTH)
        self._info_slider.scroller.pack_forget()
        self._console = []
        self._cnextnl = False

        # Eventos
        self._root.bind('<Control-q>', _kill)
        self._root.bind('<Control-z>', _copyver)
        self._root.bind('<Down>', _create_ver_d)
        self._root.bind('<Escape>', _kill)
        self._root.bind('<F1>', _show_help)
        self._root.bind('<F2>', _printconfig)
        self._root.bind('<F3>', _show_about)
        self._root.bind('<F4>', _clear)
        self._root.bind('<MouseWheel>', _scroll_console)
        self._root.bind('<Return>', self._start)
        self._root.bind('<Up>', _create_ver_u)
        for i in self._configs.keys():
            if self._configs[i]['EVENT']:
                self._root.bind(self._configs[i]['KEY'], partial(_set_config, i, '!'))
                HELP[self._configs[i]['KEY'].replace('<', '').replace('>', '')] = 'Activa/Desactiva {0}'.format(i)

        # Se agrega entrada al log
        self._log('OPEN', text=__version__)

    def _checkuploaded(self):
        """
        Chequea los archivos cargados a github.

        :return:
        """
        if os.path.isfile(EXTLBX_UPLOAD):
            with open(EXTLBX_UPLOAD, encoding='utf8') as json_data:
                self._uploaded = json.load(json_data)
        else:
            self._uploaded = {}

        for j in RELEASES.keys():
            if j not in self._uploaded:
                self._uploaded[j] = '0.0.0'

    def _clearconsole(self, scrolldir=1):
        """
        Limpia la consola.

        :param scrolldir: Dirección del scroll
        :return:
        """

        # noinspection PyShadowingNames
        def _slide(*args):
            """
            Mueve el scroll.

            :return: None
            """
            self._info_slider.canv.yview_scroll(1000 * scrolldir, 'units')

        self._console = []
        self._info.config(text='')
        self._root.after(10, _slide)

    def _getconfig(self, paramname):
        """
        Obtiene el valor de la configuración.

        :param paramname: Nombre del parámetro de la configuración
        :return:
        """
        return self._configs[paramname]['VALUE']

    def _print(self, msg, hour=False, end=None, scrolldir=1):
        """
        Imprime mensaje en consola.

        :param msg: Mensaje
        :param hour: Muestra la hora
        :param scrolldir: Dirección del scroll
        :return: None
        """

        def _consoled(c):
            """
            Función que genera un string con una lista.

            :param c: Lista
            :return: Texto
            """
            text = ''
            for i in c:
                text = text + i + '\n'
            return text

        def _get_hour():
            """
            Función que retorna la hora de sistema.

            :return: String
            """
            return time.ctime(time.time())[11:20]

        def _slide(*args):
            """
            Mueve el scroll.

            :return: None
            """
            self._info_slider.canv.yview_scroll(2000 * scrolldir, 'units')

        try:
            msg = str(msg)
            if hour:
                msg = _get_hour() + ' ' + msg
            if len(self._console) == 0 or self._console[len(self._console) - 1] != msg:
                if self._cnextnl:
                    self._console[len(self._console) - 1] += msg
                else:
                    self._console.append(msg)
                if end == '':
                    self._cnextnl = True
                else:
                    self._cnextnl = False

            if len(self._console) > LIMIT_MESSAGES_CONSOLE:
                self._console.pop()

            self._info.config(text=_consoled(self._console))
            self._root.after(50, _slide)
        except:
            self._clearconsole()

    def execute(self):
        """
        Inicia la ventana.

        :return:
        """
        self._root.mainloop()

    @staticmethod
    def _log(msg, mode='INFO', text=''):
        """
        Crea una entrada en el log.

        :type text: str, list
        :return:
        """
        try:
            d = time.strftime('%d/%m/%Y %H:%M:%S')
            with open(LOG_FILE, 'a', encoding='utf8') as logfile:
                if isinstance(text, list):
                    logfile.write('{1} [{0}] {2}\n'.format(d, mode, LOG_MSG[msg].format(*text)))
                else:
                    logfile.write('{1} [{0}] {2}\n'.format(d, mode, LOG_MSG[msg].format(text)))
        except:
            dt = open(LOG_FILE, 'w', encoding='utf8')
            dt.close()

    def _saveupload(self):
        """
        Guarda los uploads en el json.

        :return:
        """
        with open(EXTLBX_UPLOAD, 'w', encoding='utf8') as outfile:
            json.dump(self._uploaded, outfile)

    def _start(self, *args):
        """
        Genera la versión ingresada.

        :return:
        """

        def _scroll():
            self._info_slider.canv.yview_scroll(1000, 'units')

        def _callback():
            t = 0
            lastv = ''
            msg = ''
            relnm = ''
            for j in RELEASES.keys():
                if self._release.get() == RELEASES[j]['NAME']:
                    t = RELEASES[j]['ID']
                    lastv = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[j]['STATS']['FILE']).split(' ')[0]
                    msg = RELEASES[j]['MESSAGE']
                    relnm = RELEASES[j]['NAME']
                    break

            # Se crea la versión
            ver, versiondev, versionhash = mk_version(self._versionstr.get())

            # Se comprueba versiones
            if not validate_ver(versiondev, lastv):
                messagebox.showerror('Error', 'La versión nueva debe ser superior a la actual ({0}).'.format(lastv))
                self._print('ERROR: VERSIÓN INCORRECTA')
            else:
                try:
                    self._print(msg.format(versiondev))
                    self._log('CREATE_V', text=[versiondev, relnm])
                    if t == 1:
                        try:
                            export_informe(ver, versiondev, versionhash,
                                           printfun=self._print,
                                           doclean=True,
                                           dosave=self._getconfig('SAVE'),
                                           docompile=self._getconfig('COMPILE'),
                                           addstat=self._getconfig('SAVE_STAT'),
                                           backtoroot=True,
                                           plotstats=self._getconfig('PLOT_STAT'),
                                           mainroot=self._getconfig('MAIN_ROOT'),
                                           informeroot=self._getconfig('INFORME_ROOT'),
                                           statsroot=self._getconfig('STATS_ROOT'))
                        except:
                            logging.exception('Error al generar informe')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                    elif t == 2:
                        try:
                            export_auxiliares(ver, versiondev, versionhash,
                                              printfun=self._print,
                                              dosave=self._getconfig('SAVE'),
                                              docompile=self._getconfig('COMPILE'),
                                              addstat=self._getconfig('SAVE_STAT'),
                                              plotstats=self._getconfig('PLOT_STAT'),
                                              savepdf=self._getconfig('SAVE_PDF'),
                                              mainroot=self._getconfig('MAIN_ROOT'),
                                              informeroot=self._getconfig('INFORME_ROOT'),
                                              statsroot=self._getconfig('STATS_ROOT'))
                        except:
                            logging.exception('Error al generar auxiliares')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_AUXILIAR], 'FILES')
                    elif t == 3:
                        try:
                            export_controles(ver, versiondev, versionhash,
                                             printfun=self._print,
                                             dosave=self._getconfig('SAVE'),
                                             docompile=self._getconfig('COMPILE'),
                                             addstat=self._getconfig('SAVE_STAT'),
                                             plotstats=self._getconfig('PLOT_STAT'),
                                             savepdf=self._getconfig('SAVE_PDF'),
                                             mainroot=self._getconfig('MAIN_ROOT'),
                                             informeroot=self._getconfig('INFORME_ROOT'),
                                             statsroot=self._getconfig('STATS_ROOT'))
                        except:
                            logging.exception('Error al generar controles')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_AUXILIAR], 'FILES')
                            clear_dict(RELEASES[REL_CONTROLES], 'FILES')
                    elif t == 4:
                        try:
                            export_cv(ver, versiondev, versionhash, printfun=self._print,
                                      dosave=self._getconfig('SAVE'),
                                      docompile=self._getconfig('COMPILE'),
                                      addstat=self._getconfig('SAVE_STAT'),
                                      plotstats=self._getconfig('PLOT_STAT'),
                                      savepdf=self._getconfig('SAVE_PDF'),
                                      mainroot=self._getconfig('MAIN_ROOT'),
                                      statsroot=self._getconfig('STATS_ROOT'),
                                      backtoroot=True)
                        except:
                            logging.exception('Error al generar cv')
                            clear_dict(RELEASES[REL_PROFESSIONALCV], 'FILES')
                    elif t == 5:
                        try:
                            export_reporte(ver, versiondev, versionhash, printfun=self._print,
                                           dosave=self._getconfig('SAVE'),
                                           docompile=self._getconfig('COMPILE'),
                                           addstat=self._getconfig('SAVE_STAT'),
                                           plotstats=self._getconfig('PLOT_STAT'),
                                           savepdf=self._getconfig('SAVE_PDF'),
                                           mainroot=self._getconfig('MAIN_ROOT'),
                                           statsroot=self._getconfig('STATS_ROOT'),
                                           informeroot=self._getconfig('INFORME_ROOT'))
                        except:
                            logging.exception('Error al generar reporte')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_REPORTE], 'FILES')
                    elif t == 6:
                        try:
                            export_tesis(ver, versiondev, versionhash, printfun=self._print,
                                         dosave=self._getconfig('SAVE'),
                                         docompile=self._getconfig('COMPILE'),
                                         addstat=self._getconfig('SAVE_STAT'),
                                         plotstats=self._getconfig('PLOT_STAT'),
                                         savepdf=self._getconfig('SAVE_PDF'),
                                         mainroot=self._getconfig('MAIN_ROOT'),
                                         statsroot=self._getconfig('STATS_ROOT'),
                                         informeroot=self._getconfig('INFORME_ROOT'))
                        except:
                            logging.exception('Error al generar tesis')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_TESIS], 'FILES')
                    elif t == 7:
                        try:
                            export_presentacion(ver, versiondev, versionhash, printfun=self._print,
                                                dosave=self._getconfig('SAVE'),
                                                docompile=self._getconfig('COMPILE'),
                                                addstat=self._getconfig('SAVE_STAT'),
                                                plotstats=self._getconfig('PLOT_STAT'),
                                                savepdf=self._getconfig('SAVE_PDF'),
                                                mainroot=self._getconfig('MAIN_ROOT'),
                                                statsroot=self._getconfig('STATS_ROOT'),
                                                informeroot=self._getconfig('INFORME_ROOT'))
                        except:
                            logging.exception('Error al generar presentacion')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_PRESENTACION], 'FILES')
                    elif t == 8:
                        try:
                            export_articulo(ver, versiondev, versionhash, printfun=self._print,
                                            dosave=self._getconfig('SAVE'),
                                            docompile=self._getconfig('COMPILE'),
                                            addstat=self._getconfig('SAVE_STAT'),
                                            plotstats=self._getconfig('PLOT_STAT'),
                                            savepdf=self._getconfig('SAVE_PDF'),
                                            mainroot=self._getconfig('MAIN_ROOT'),
                                            statsroot=self._getconfig('STATS_ROOT'),
                                            informeroot=self._getconfig('INFORME_ROOT'))
                        except:
                            logging.exception('Error al generar articulo')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_REPORTE], 'FILES')
                            clear_dict(RELEASES[REL_ARTICULO], 'FILES')
                    elif t == 9:
                        try:
                            export_poster(ver, versiondev, versionhash, printfun=self._print,
                                          dosave=self._getconfig('SAVE'),
                                          docompile=self._getconfig('COMPILE'),
                                          addstat=self._getconfig('SAVE_STAT'),
                                          plotstats=self._getconfig('PLOT_STAT'),
                                          savepdf=self._getconfig('SAVE_PDF'),
                                          mainroot=self._getconfig('MAIN_ROOT'),
                                          statsroot=self._getconfig('STATS_ROOT'),
                                          informeroot=self._getconfig('INFORME_ROOT'))
                        except:
                            logging.exception('Error al generar poster')
                            clear_dict(RELEASES[REL_INFORME], 'FILES')
                            clear_dict(RELEASES[REL_PRESENTACION], 'FILES')
                            clear_dict(RELEASES[REL_POSTER], 'FILES')
                    else:
                        raise Exception('ERROR: ID INCORRECTO')
                    self._lastsav = self._getconfig('SAVE')
                    self._lascpdf = self._getconfig('COMPILE') and self._getconfig('SAVE_PDF')
                    self._print(' ')
                    if self._lastsav:
                        self._uploadstatebtn('on')
                except Exception as e:
                    messagebox.showerror('Error fatal', 'Ocurrio un error inesperado al procesar la solicitud.')
                    self._log('OTHER', text=str(e), mode='ERROR')
                    self._print('ERROR: EXCEPCIÓN INESPERADA')
                    self._print(str(e))
                    self._print(traceback.format_exc())
                    self._sounds.alert()

            self._root.configure(cursor='arrow')
            self._root.title(TITLE)
            self._versionstr.trace_vdelete('w', self._versiontrace)
            self._versionstr.set('')
            self._versiontrace = self._versionstr.trace('w', self._checkver)
            self._root.update()
            self._root.after(50, _scroll)
            self._log('CREATE_V_COMPLETE')
            return

        if not self._validversion:
            return
        self._root.title(TITLE_LOADING.format(TITLE))
        self._root.configure(cursor='wait')
        self._root.update()
        self._root.after(500, _callback)
        self._startbutton.configure(state='disabled')
        self._uploadstatebtn('off')
        return

    def _uploadstatebtn(self, state):
        """
        Cambia el estado del botón upload.

        :param state: Estado
        :return:
        """
        if state == 'on':
            self._uploadbutton.configure(state='normal')
            self._uploadbutton.configure(cursor='hand2')
            if self._upload_imgs:
                self._uploadbutton.configure(image=self._upload_imgs[0])
                self._uploadbutton.image = self._upload_imgs[0]
        else:
            self._uploadbutton.configure(state='disabled')
            self._uploadbutton.configure(cursor='arrow')
            if self._upload_imgs:
                self._uploadbutton.configure(image=self._upload_imgs[1])
                self._uploadbutton.image = self._upload_imgs[1]
        self._uploadbutton.update()

    def _upload_github(self, *args):
        """
        Sube la versión a github.

        :param args: Argumentos opcionales
        :return: None
        """

        def _scroll():
            self._info_slider.canv.yview_scroll(1000, 'units')

        def _callback():
            t = 0
            lastv = ''
            jver = ''
            lastvup = ''
            for j in RELEASES.keys():
                if self._release.get() == RELEASES[j]['NAME']:
                    lastv = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[j]['STATS']['FILE']).split(' ')[0]
                    lastvup = lastv.split('-')[0]
                    jver = j
                    self._log('UPLOAD_V', text=[lastvup, RELEASES[j]['NAME']])
                    break

            # Sube el contenido a la plataforma
            try:
                # Se cambia el path
                os.chdir(self._getconfig('MAIN_ROOT'))
                cmsg = GITHUB_REP_COMMIT.format(lastv)

                # Se llama a consola para añadir carpeta a git
                t = time.time()
                with open(os.devnull, 'w') as FNULL:
                    with Cd(RELEASES[jver]['GIT']):
                        call(['git', 'add', '--all'], stdout=FNULL)
                        call(['git', 'commit', '-m', cmsg], stdout=FNULL)
                        call(['git', 'push'], stdout=FNULL, stderr=FNULL)

                # Se sube archivo pdf
                pdf_file = RELEASES[jver]['PDF_FOLDER'].format(lastvup)
                cmsg = GITHUB_PDF_COMMIT.format(lastv, RELEASES[jver]['NAME'])
                if os.path.isfile(pdf_file) and self._lascpdf:
                    with open(os.devnull, 'w') as FNULL:
                        with Cd(self._getconfig('PDF_ROOT')):
                            pdf_file = pdf_file.replace(self._getconfig('PDF_ROOT'), '')
                            call(['git', 'add', pdf_file], stdout=FNULL)
                            call(['git', 'commit', '-m', cmsg], stdout=FNULL)
                            call(['git', 'push'], stdout=FNULL, stderr=FNULL)

                # Se sube estadísticas
                cmsg = GITHUB_STAT_COMMIT.format(lastv, RELEASES[jver]['NAME'])
                with open(os.devnull, 'w') as FNULL:
                    with Cd(self._getconfig('STATS_ROOT') + 'stats/'):
                        call(['git', 'add', RELEASES[jver]['STATS']['GIT_ADD']], stdout=FNULL)
                        call(['git', 'commit', '-m', cmsg], stdout=FNULL)
                        call(['git', 'push'], stdout=FNULL, stderr=FNULL)

                # Se guarda la versión
                self._uploaded[jver] = lastv
                self._saveupload()

                # Se actualiza archivo updates
                # cmsg = GITHUB_UPDATE_COMMIT
                # with open(os.devnull, 'w') as FNULL:
                #     with Cd(self._getconfig('MAIN_ROOT')):
                #         call(['git', 'add', EXTLBX_UPLOAD], stdout=FNULL)
                #         call(['git', 'commit', '-m', cmsg], stdout=FNULL)
                #         call(['git', 'push'], stdout=FNULL, stderr=FNULL)

                # Se muestra tiempo de subida y se termina el proceso
                self._print(MSG_FOKTIMER.format((time.time() - t)))
                self._uploadstatebtn('off')
            except Exception as e:
                messagebox.showerror('Error fatal', 'Ocurrio un error inesperado al procesar la solicitud.')
                self._log('OTHER', text=str(e), mode='ERROR')
                self._print('ERROR: EXCEPCIÓN INESPERADA')
                self._print(str(e))
                self._print(traceback.format_exc())
                self._sounds.alert()
                self._uploadstatebtn('on')

            self._log('UPLOAD_COMPLETE')
            self._root.configure(cursor='arrow')
            self._root.title(TITLE)
            self._root.update()
            self._root.after(50, _scroll)
            return

        self._root.title(TITLE_UPLOADING.format(TITLE))
        self._root.configure(cursor='wait')
        self._root.update()
        for k in RELEASES.keys():
            if self._release.get() == RELEASES[k]['NAME']:
                v = get_last_ver(self._getconfig('STATS_ROOT') + RELEASES[k]['STATS']['FILE']).split(' ')[0]
                self._print(GITHUB_PRINT_MSG.format(v, RELEASES[k]['NAME']), end='')
                break
        self._root.after(500, _callback)
        self._uploadstatebtn('off')


if __name__ == '__main__':
    CreateVersion().execute()
