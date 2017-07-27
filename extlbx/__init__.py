# coding=utf-8
"""
Toolbox para exportar el template.

Autor: PABLO PIZARRO @ github.com/ppizarror
Fecha: 2017
Licencia: MIT
"""

# noinspection PyUnresolvedReferences
from releases import RELEASES
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


# noinspection PyCompatibility
def reload_extlbx():
    """
    Vuelve a cargar funciones.
    """
    reload(convert)
