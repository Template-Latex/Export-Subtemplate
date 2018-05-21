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