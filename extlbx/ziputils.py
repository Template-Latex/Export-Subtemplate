# coding=utf-8
"""
ZIP UTILS
Herramientas para el uso de archivos ZIP

Autor: Pablo Pizarro R. @ ppizarror.com
Licencia:
    The MIT License (MIT)

    Copyright 2017-2020 Pablo Pizarro R.

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
import zipfile


class Zip(object):
    """
    Clase para administrar archivos zip.
    """

    def __init__(self, filename):
        """
        Constructor, crea un archivo zipfile con un nombre
        :param filename: Nombre del archivo
        """
        if '.zip' not in filename:
            filename += '.zip'

        # Crea un objeto zipfile
        self._zip = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)

        # Lista de excepciones
        self._excptfiles = []

        # Path a descontar
        self.ghostpath = ''

    def add_excepted_file(self, filename):
        """
        Agrega un archivo a la lista de excepciones.

        :param filename: Nombre del archivo
        :type filename: str, list
        :return: None
        """
        if type(filename) is list:
            for f in filename:
                self.add_excepted_file(f)
        else:
            self._excptfiles.append(filename)

    def _check_excepted_file(self, filename):
        """
        Indica si el archivo está dentro de la lista de excepciones.

        :param filename: Nombre del archivo
        :type filename: str
        :return: Booleano
        :rtype: bool
        """
        filebasename = os.path.basename(filename)
        for f in self._excptfiles:
            if f in filebasename:
                return True
        return False

    def save(self):
        """
        Guarda el archivo zip

        :return: None
        """
        self._zip.close()

    def _writefile(self, f, fname):
        """
        Escribe un archivo en el zip.

        :param f: Dirección del archivo
        :param fname: Nombre del archivo
        :return:
        """
        self._zip.write(f, fname)

    def add_file(self, ufile, ghostpath=None):
        """
        Añade un archivo al zip.

        :param ghostpath: Dirección a borrar
        :param ufile: Ubicación del archivo
        :type ufile: str, list
        :return: None
        """
        if type(ufile) is list:
            for f in ufile:
                if ghostpath is None:
                    self._writefile(f, f.replace(self.ghostpath, ''))
                else:
                    self._writefile(f, f.replace(ghostpath, ''))
        else:
            if ghostpath is None:
                self._writefile(ufile, ufile.replace(self.ghostpath, ''))
            else:
                self._writefile(ufile, ufile.replace(ghostpath, ''))

    def add_folder(self, folder):
        """
        Agrega una carpeta al archivo zip.

        :param folder: Carpeta
        :type folder: str, list
        :return: None
        """
        if type(folder) is list:
            for f in folder:
                self.add_folder(f)
        else:
            for f in os.listdir(folder):
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    if not self._check_excepted_file(full_path):
                        self.add_file(full_path)
                elif os.path.isdir(full_path):
                    self.add_folder(full_path)

    def set_ghostpath(self, path):
        """
        Añade path fantasma para eliminar entrada de archivo.

        :param path: Dirección
        :return:
        """
        self.ghostpath = path
