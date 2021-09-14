# coding=utf-8
"""
RESOURCES
Recursos del toolbox

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

__all__ = [
    'EXTLBX_BTN_UPLOAD',
    'EXTLBX_BTN_UPLOAD_DISABLED',
    'EXTLBX_CONFIGS',
    'EXTLBX_ICON',
    'EXTLBX_ICON_MAC',
    'EXTLBX_LICENSE',
    'EXTLBX_UPLOAD'
]

# Importación de librerías
import os

# Obtiene el path actual
__actualpath = str(os.path.abspath(os.path.dirname(__file__))).replace('\\', '/') + '/'
__respath = __actualpath + 'res/'

# Recursos
EXTLBX_BTN_UPLOAD = __respath + 'upload2.png'
EXTLBX_BTN_UPLOAD_DISABLED = __respath + 'upload2_disabled.png'
EXTLBX_CONFIGS = __respath + 'config.json'
EXTLBX_ICON = __respath + 'icon.ico'
EXTLBX_ICON_MAC = __respath + 'icon.gif'
EXTLBX_LICENSE = __respath + 'license'
EXTLBX_UPLOAD = __respath + 'upload.json'
