# coding=utf-8
"""
SOUND
Módulo que maneja eventos de sonidos

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
    'DO',
    'DOm',
    'FA',
    'FAm',
    'LA',
    'LAm',
    'MI',
    'RE',
    'REm',
    'SI',
    'SOL',
    'SOLm',
    'Sound'
]

# Importación de librerías
import math

WINSOUND_EXISTS = True

try:
    # noinspection PyUnresolvedReferences
    import winsound
except ImportError:
    WINSOUND_EXISTS = False

# Constantes
DO = 65.406
DOm = 69.296
RE = 73.416
REm = 77.782
MI = 82.407
FA = 87.307
FAm = 92.499
SOL = 97.999
SOLm = 103.826
LA = 110
LAm = 116.541
SI = 123.471


# Sonidos
class Sound(object):
    """
    Crea y ejecuta sonidos.
    """

    def __init__(self):
        pass

    @staticmethod
    def _make(n, e):
        """
        Crea una nota musical <n> con un exponente <e>.

        :param n: Nota
        :param e: Exponente
        :return:
        """
        return int(math.ceil(n * pow(2, e)))

    def _play(self, n, e, t):
        """
        Reproduce una nota musical <n> en escala <e> y tiempo <t>.

        :param n: Nota
        :param e: Escala
        :param t: Tiempo
        :return:
        """
        self._triggersound(self._make(n, e), t)

    @staticmethod
    def alert():
        """
        Sonido de alerta
        :return:
        """
        if not WINSOUND_EXISTS:
            return
        winsound.MessageBeep(winsound.MB_OK)

    @staticmethod
    def _triggersound(freq, time):
        """
        Crea un sonido.

        :param freq: Frecuencia
        :param time: Tiempo
        :return:
        """
        if not WINSOUND_EXISTS:
            return
        winsound.Beep(freq, time)


if __name__ == '__main__':
    Sound().alert()
