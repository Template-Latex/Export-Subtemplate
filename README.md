<h1 align="center">
  <img alt="Export-Subtemplate" src="https://latex.ppizarror.com/res/favicon-informe/icon.png" width="200px" height="200px" />
  <br /><br />
  Export-Subtemplate</h1>
<p align="center">Aplicación que permite generar subtemplates a partir de Template-Informe</p>
<div align="center"><a href="https://ppizarror.com"><img alt="@ppizarror" src="https://latex.ppizarror.com/res/badges/autor.svg" /></a>
<a href="https://opensource.org/licenses/MIT/"><img alt="Licencia MIT" src="https://latex.ppizarror.com/res/badges/licenciamit.svg" /></a>
<a href="https://www.python.org/downloads/"><img alt="Python 2.7" src="https://latex.ppizarror.com/res/badges/python27.svg" /></a>
</div><br />

<p align="center">
  <img src="http://latex.ppizarror.com/res/other/export-subtemplate.PNG" width="40%" />
</p>

## Licencia
Este proyecto está licenciado bajo la licencia MIT [https://opensource.org/licenses/MIT]

## API

#### Archivos externos
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

#### Líneas de codigo
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
<a href="https://ppizarror.com" title="ppizarror">Pablo Pizarro R.</a> | 2017 - 2018
