"""
VFRAME
Clase para usar el frame vertical

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

__all__ = ['VerticalScrolledFrame']

# noinspection PyCompatibility
from tkinter import Frame, Scrollbar, Canvas, NW, BOTH, TRUE, LEFT, RIGHT, VERTICAL, FALSE, Y


# noinspection PyUnusedLocal
class VerticalScrolledFrame(Frame):
    """
    Frame Vertical con Scroll.
    https://tkinter.unpythonic.net/wiki/VerticalScrolledFrame
    """

    def __init__(self, parent, *args, **kw):
        # Opciones propias (no se pasan a tkinter)
        scrollbar = kw.pop('scrollbar', True)
        mousewheel = kw.pop('mousewheel', True)

        Frame.__init__(self, parent, *args, **kw)
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        if scrollbar:
            vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)
        self.canv = canvas
        self.scroller = vscrollbar

        def _configure_interior(event):
            # El interior nunca debe ser más angosto que el canvas, así el
            # contenido (la consola) llena todo el ancho disponible.
            req_h = interior.winfo_reqheight()
            # noinspection PyTypeChecker
            canvas.config(scrollregion="0 0 %s %s" % (canvas.winfo_width(), req_h))

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            # Mantiene el interior con el mismo ancho que el canvas.
            canvas.itemconfigure(interior_id, width=canvas.winfo_width())
            canvas.config(scrollregion="0 0 %s %s" % (canvas.winfo_width(),
                                                      interior.winfo_reqheight()))

        canvas.bind('<Configure>', _configure_canvas)

        # Scroll con la rueda del mouse cuando el cursor está sobre la consola.
        # Reemplaza el antiguo hit-test por coordenadas fijas, que dependía del
        # tamaño exacto de la ventana.
        def _on_mousewheel(event):
            if event.num == 4:  # Linux scroll up
                canvas.yview_scroll(-2, 'units')
            elif event.num == 5:  # Linux scroll down
                canvas.yview_scroll(2, 'units')
            elif event.delta:  # Windows / macOS
                step = -1 if event.delta > 0 else 1
                # En Windows el delta viene en múltiplos de 120
                if abs(event.delta) >= 120:
                    step *= 2
                else:
                    step *= 2
                canvas.yview_scroll(step, 'units')
            return 'break'

        def _bind_wheel(_event=None):
            canvas.bind_all('<MouseWheel>', _on_mousewheel)
            canvas.bind_all('<Button-4>', _on_mousewheel)
            canvas.bind_all('<Button-5>', _on_mousewheel)

        def _unbind_wheel(_event=None):
            canvas.unbind_all('<MouseWheel>')
            canvas.unbind_all('<Button-4>')
            canvas.unbind_all('<Button-5>')

        if mousewheel:
            canvas.bind('<Enter>', _bind_wheel)
            canvas.bind('<Leave>', _unbind_wheel)
            interior.bind('<Enter>', _bind_wheel)
