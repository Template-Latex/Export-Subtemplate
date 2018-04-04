# coding=utf-8
"""
EXTLBX
Toolbox para exportar distintos templates y subtemplates

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

# noinspection PyUnresolvedReferences
from releases import REL_PROFESSIONALCV, REL_INFORME, REL_CONTROLES, REL_AUXILIAR, RELEASES
# noinspection PyUnresolvedReferences
import convert
# noinspection PyUnresolvedReferences
from convert import call, CREATE_NO_WINDOW, MSG_FOKTIMER
# noinspection PyUnresolvedReferences
from version import *
# noinspection PyUnresolvedReferences
from sound import Sound
# noinspection PyUnresolvedReferences
from resources import *
# noinspection PyUnresolvedReferences
from export_professionalcv import exportcv

# noinspection PyCompatibility,PyUnresolvedReferences
from Tkinter import *
# noinspection PyCompatibility,PyUnresolvedReferences
import tkFont
# noinspection PyUnresolvedReferences,PyCompatibility
import tkMessageBox

# noinspection PyUnresolvedReferences
from vframe import VerticalScrolledFrame

# noinspection PyUnresolvedReferences
from pyperclip import copy as extlbcbpaste

import sys

# noinspection PyCompatibility
reload(sys)
# noinspection PyUnresolvedReferences
sys.setdefaultencoding('utf8')


# noinspection PyCompatibility
def reload_extlbx():
    """
    Vuelve a cargar funciones.
    """
    reload(convert)
