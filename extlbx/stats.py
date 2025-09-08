"""
STATS
Estadísticas de compilación

Autor: PABLO PIZARRO @ github.com/ppizarror
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
    'add_stat',
    'generate_statline',
    'plot_stats'
]

# Importación de librerías
from extlbx.utils import split_str

SCIPY = True

try:
    # noinspection PyUnresolvedReferences
    from scipy import stats  # type: ignore
except (ImportError, ModuleNotFoundError):
    SCIPY = False


def generate_statline(statid, version, time, date, lc, vh):
    """
    Genera una línea de estadísticas.

    :param statid: ID de la línea
    :param version: Versión
    :param time: Tiempo de compilación
    :param date: Fecha de compilación
    :param lc: Número de líneas
    :param vh: Version hash
    :return:
    """
    statid = str(statid).ljust(6)
    version = str(version).ljust(18)
    time = str(time).ljust(10)
    date = str(date).ljust(14)
    lc = str(lc).ljust(10)
    vh = str(vh).ljust(0)

    return f'{statid}{version}{time}{date}{lc}{vh}'


# noinspection PyBroadException,PyUnboundLocalVariable
def add_stat(statfile, version, time, date, lc, vh, test=False):
    """
    Agrega una entrada al archivo de estadísticas.

    :param test: Indica testeo
    :param statfile: Archivo de estadísticas
    :param version: Versión del template
    :param time: Tiempo de compilación
    :param date: Fecha de compilación
    :param lc: Total de líneas de código
    :param vh: Version hash
    :return:
    """

    # Se carga el archivo y se encuentra la última entrada
    dataarr = []
    try:
        data = open(statfile, encoding='utf8')
        for i in data:
            dataarr.append(i)
        lastentrypos = len(dataarr) - 1
    except:
        data = open(statfile, 'w', encoding='utf8')
        lastentrypos = -1
    if lastentrypos >= 0:
        lastentry = split_str(dataarr[lastentrypos].strip(), ' ')
        lastid = int(lastentry[0])
        lastver = lastentry[1].split('.')
        if len(lastver) == 4:
            lastverid = int(lastver[3])
            lastver = lastentry[1]
            lastver = lastver.replace('.' + str(lastverid), '')
        else:
            lastverid = 0
            lastver = lastentry[1]

        dataarr[lastentrypos] = f'{dataarr[lastentrypos]}\n'
    else:
        lastid = 0
        lastver = ''
        dataarr.append(generate_statline('ID', 'VERSION', 'CTIME', 'FECHA',
                                         'LINEAS', 'HASH\n'))
    data.close()

    # Se comprueba que la version sea distinta
    if version == lastver:
        version = f'{version}.{lastverid + 1}'

    # Se crea una nueva línea
    newentry = generate_statline(lastid + 1, version, str(time)[0:5], date,
                                 lc, vh)
    dataarr.append(newentry)

    # Se guarda el nuevo archivo
    if not test:
        data = open(statfile, 'w', encoding='utf8')
        for i in dataarr:
            data.write(i)
        data.close()


# noinspection PyUnresolvedReferences
def plot_stats(statfile, statplotctime, statplotlcode):
    """
    Grafica las estadísticas.

    :param statplotlcode: Archivo de gráficos línea de código
    :param statplotctime: Archivo de gráficos tiempo de compilación
    :param statfile: Archivo de estadísticas
    :return:
    """
    import matplotlib.pyplot as plt  # type: ignore
    from matplotlib.ticker import MaxNLocator  # type: ignore

    data = open(statfile, encoding='utf8')
    numcomp = []
    timecomp = []
    lcode = []
    k = 0
    for i in data:
        if k > 0:
            j = split_str(i.strip(), ' ')
            numcomp.append(int(j[0]))
            timecomp.append(float(j[2]))
            lcode.append(int(j[4]))
        k += 1
    nlen = len(numcomp)
    lastid = numcomp[nlen - 1]
    if nlen >= 3 and SCIPY:
        # Tiempo de compilación
        tme = stats.tmean(timecomp)
        trc = stats.trim_mean(timecomp, 0.15)

        plt.figure(1)
        fig, ax = plt.subplots()
        ax.plot(numcomp, timecomp, 'c', label=u'Tiempo compilación (s)')
        ax.plot([numcomp[0], numcomp[nlen - 1]], [tme, tme], 'r--',
                label=f'Tiempo medio ({tme:.3g}s)')
        ax.plot([numcomp[0], numcomp[nlen - 1]], [tme, tme], 'b--',
                label=f'Media acotada ({trc:.3g}s)')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_xlabel(u'Número de compilación')
        ax.set_ylabel(u'Tiempo de compilación [s]')
        ax.set_title(u'Estadísticas')
        plt.xlim(1, lastid)
        ax.legend()
        fig.savefig(statplotctime, dpi=600)

        # Líneas de código
        fig, ax = plt.subplots()
        ax.plot(numcomp, lcode)
        ax.set_xlabel(u'Número de compilación')
        ax.set_ylabel(u'Líneas de código')
        ax.set_title(u'Estadísticas')
        plt.ylim([min(lcode) * 0.97, max(lcode) * 1.03])
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        plt.xlim(1, lastid)
        fig.savefig(statplotlcode, dpi=600)

    data.close()
