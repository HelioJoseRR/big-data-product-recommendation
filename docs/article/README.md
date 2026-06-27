# Artigo SBC

Base LaTeX para o artigo **Sistema de Recomendacao de Produtos Utilizando Apache Spark**.

## Arquivos

- `main.tex`: texto principal no padrao SBC.
- `referencias.bib`: referencias BibTeX iniciais.

## Dependencias do template SBC

Antes de compilar, coloque nesta pasta os arquivos oficiais do template SBC:

- `sbc-template.sty`
- `sbc.bst`

Esses arquivos sao distribuidos pela Sociedade Brasileira de Computacao no pacote de modelos para publicacao de artigos.

## Compilacao

A partir desta pasta:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Ou, se `latexmk` estiver disponivel:

```bash
latexmk -pdf main.tex
```

As figuras sao referenciadas diretamente de `../../results/figures/`, portanto execute `make benchmark-full` antes da compilacao para garantir que os PNGs estejam atualizados.
