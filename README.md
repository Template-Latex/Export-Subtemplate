<h1 align="center">
  <img alt="Export-Subtemplate" src="https://template-latex.github.io/res/favicon-informe/icon.png" width="200px" height="200px" />
  <br><br>
  Export-Subtemplate</h1>
<p align="center">Aplicación que permite generar subtemplates a partir de Template-Informe</p>
<div align="center"><a href="https://ppizarror.com"><img alt="@ppizarror" src="https://img.shields.io/badge/Autor-Pablo%20Pizarro%20R.-9f9f9f" /></a>
<a href="https://opensource.org/licenses/MIT/"><img alt="Licencia MIT" src="https://img.shields.io/badge/Licencia-MIT-007ec6" /></a>
<a href="https://www.python.org/downloads/"><img alt="Python 2.7+/3.6+" src="https://img.shields.io/badge/Python-2.7+/3.6+-red.svg" /></a>
<br>

<a href="https://github.com/Template-Latex/Template-Articulo/"><img alt="Template-Artículo" src="https://img.shields.io/badge/Template-Articulo-4666ff" /></a>
<a href="https://github.com/Template-Latex/Template-Auxiliares/"><img alt="Template-Auxiliares" src="https://img.shields.io/badge/Template-Auxiliares-fe7d37" /></a>
<a href="https://github.com/Template-Latex/Template-Controles/"><img alt="Template-Controles" src="https://img.shields.io/badge/Template-Controles-e05d44" /></a>
<a href="https://github.com/Template-Latex/Template-Informe/"><img alt="Template-Informe" src="https://img.shields.io/badge/Template-Informe-800080" /></a>
<a href="https://github.com/Template-Latex/Template-Poster/"><img alt="Template-Poster" src="https://img.shields.io/badge/Template-Poster-aa99ff" /></a>
<a href="https://github.com/Template-Latex/Template-Presentacion/"><img alt="Template-Presentación" src="https://img.shields.io/badge/Template-Presentacion-df94a0" /></a>
<a href="https://github.com/Template-Latex/Template-Reporte/"><img alt="Template-Reporte" src="https://img.shields.io/badge/Template-Reporte-ff69b4" /></a>
<a href="https://github.com/Template-Latex/Template-Tesis/"><img alt="Template-Tesis" src="https://img.shields.io/badge/Template-Tesis-a4a61d" /></a>
<a href="https://github.com/Template-Latex/Professional-CV/"><img alt="Professional-CV" src="https://img.shields.io/badge/Professional-CV-993456" /></a>

</div><br>

<p align="center">
  <img src="https://template-latex.github.io/res/other/export-subtemplate.PNG" width="50%" />
</p>

## Licencia

Este proyecto está licenciado bajo la licencia MIT [https://opensource.org/licenses/MIT]

## API

### Archivos externos

Formato de línea:

```bash
\input{file.tex} # !FILE <ARG1,ARG2,...>
```

| Argumento | Descripción |
| :-:|:--|
| DELCOM | Forza borrado de comentarios |
| NODIST | Archivo no se incluye en la distribución |
| NL | Forza una nueva línea al finalizar el archivo |
| STRIP | Forza el *strip* del archivo |

### Líneas de codigo

Formato de línea:

```bash
\latexline # Comment !ARG1 !ARG2
```

| Argumento | Descripción |
| :-:|:--|
| !DELCOM | Forza el borrado del comentario en la línea |
| !DISTNL | Forza una nueva línea solo en la distribución |
| !NL | Forza una nueva línea en cualquier caso |
| !STRIP | Forza el *strip* en la línea |
| !PREVNL | Añade una nueva línea en modo compacto |
| !PREVDISTNL | Añade una nueva línea solo en el modo distribución |

## Autor

[Pablo Pizarro R.](https://ppizarror.com) | 2017 - 2026
