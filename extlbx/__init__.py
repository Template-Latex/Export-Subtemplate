# coding=utf-8
"""
EXTLBX
Toolbox para exportar distintos templates y subtemplates

Autor: Pablo Pizarro R. @ ppizarror.com
Licencia:
    The MIT License (MIT)

    Copyright 2017-2019 Pablo Pizarro R.

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

__author__ = 'Pablo Pizarro R.'
__version__ = '3.1.0'  # (19/08/2019)

from releases import REL_PROFESSIONALCV, REL_INFORME, REL_CONTROLES, REL_AUXILIAR, RELEASES, REL_REPORTE
import convert
from convert import call, CREATE_NO_WINDOW, MSG_FOKTIMER
from version import *
from sound import Sound
from resources import *
from Tkinter import *
import tkFont
import tkMessageBox
from vframe import VerticalScrolledFrame
from pyperclip import copy as extlbcbpaste
import sys

reload(sys)
sys.setdefaultencoding('utf8')


def reload_extlbx():
    """
    Vuelve a cargar funciones.
    """
    reload(convert)
