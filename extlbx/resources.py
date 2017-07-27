# coding=utf-8
"""
RESOURCES
Recursos del toolbox.

Autor: PABLO PIZARRO @ github.com/ppizarror
Fecha: 2017
Licencia: MIT
"""

# Importación de librerías
import os

# Obtiene el path actual
__actualpath = str(os.path.abspath(os.path.dirname(__file__))).replace('\\', '/') + '/'
__respath = __actualpath + 'res/'

# Recursos
EXTLBX_BTN_UPLOAD = __respath + 'upload2.png'
EXTLBX_CONFIGS = __respath + 'config.json'
EXTLBX_ICON = __respath + 'icon.ico'
EXTLBX_LICENSE = __respath + 'lic'
EXTLBX_RELEASE_JSON = __respath + 'releases.json'
EXTLBX_UPLOAD = __respath + 'upload.json'
