# coding=utf-8
"""
RELEASES
Contiene archivos de cada release

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
import json
import os

# Se carga json
__actualpath = str(os.path.abspath(os.path.dirname(__file__))).replace('\\', '/') + '/'
with open(__actualpath + 'releases.json') as json_data:
    RELEASES = json.load(json_data)
with open(__actualpath + 'deptos.json') as json_data:
    DEPTOS = json.load(json_data)['DEPTOS']

# Constantes
REL_AUXILIAR = 'AUXILIAR'
REL_CONTROLES = 'CONTROLES'
REL_INFORME = 'INFORME'
REL_PROFESSIONALCV = 'PROFESSIONAL-CV'
REL_REPORTE = 'REPORTE'
REL_PRESENTACION = 'PRESENTACION'
REL_TESIS = 'TESIS'
