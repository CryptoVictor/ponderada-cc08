#!/usr/bin/env bash
# rodar_tudo.sh - roda cada versão da A4 três vezes com 20.000 amostras.
#
# Ponderada CC08 - Victor Garcia dos Santos (N = 4)
#
# Salva a saída de cada execução em logs/versaoV_execE.txt e monta a tabela
# logs/tabela.csv (uma linha por execução), usada no ponderada-tato.md.
#
# Uso: bash rodar_tudo.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
echo "versao;execucao;produzidas;consumidas;perdidas;duplicadas;invalidas;travou;duracao_s" > logs/tabela.csv
for v in 1 2 3; do
  for e in 1 2 3; do
    echo ">>> versao$v.py, execução $e"
    {
      echo "\$ python3 versao$v.py -e $e"
      python3 versao$v.py -e "$e" 2> >(grep '^CSV;' | sed 's/^CSV;//' >> logs/tabela.csv)
    } | tee "logs/versao${v}_exec${e}.txt"
    sleep 0.2
  done
done
echo "Tabela em logs/tabela.csv"
