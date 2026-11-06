"""
comum.py - Infraestrutura compartilhada pelas três versões da questão A4.

Ponderada CC08 "Do pipeline ao deadlock" - pulseira sensorial Tato.
Autor: Victor Garcia dos Santos (D1 = 6, D2 = 1, N = 4)

Este módulo NÃO contém sincronização do buffer: cada versão (versao1.py,
versao2.py, versao3.py) implementa o próprio produtor e consumidor. Aqui ficam
só as partes que precisam ser iguais nas três para que a comparação seja justa:

  * os parâmetros (N, total de amostras, limite de travamento);
  * o registro do que foi produzido e consumido (classe Registro);
  * o vigia (watchdog) que encerra a execução se o consumidor ficar 1 s sem
    receber nada;
  * o cálculo de consumidas / perdidas / duplicadas e a impressão do relatório.
"""

import argparse
import os
import sys
import threading
import time
from collections import Counter

# Parâmetros individuais: N = 3 + (D2 mod 5) = 3 + (1 mod 5) = 4.
N = 4
# Quantidade de amostras pedida no enunciado para cada execução.
TOTAL_AMOSTRAS = 20_000
# Se o consumidor ficar este tempo sem receber nada, a execução é encerrada e
# registrada como travamento.
LIMITE_TRAVAMENTO_S = 1.0


class Registro:
    """Guarda tudo o que aconteceu numa execução, para o relatório final.

    Atributos:
        total (int): quantas amostras o produtor deve gerar.
        produzidas (int): quantas amostras o produtor já colocou no buffer.
        consumidos (list[int]): valores recebidos pelo consumidor, em ordem.
        ultimo_progresso (float): instante (time.monotonic) do último
            recebimento do consumidor, ou do início da execução.
        produtor_terminou (bool): True quando o produtor gerou todas as amostras.
        consumidor_terminou (bool): True quando o consumidor saiu do laço.
        travou (bool): True se a execução foi encerrada por travamento.
    """

    def __init__(self, total):
        """Cria um registro vazio.

        Parâmetros:
            total (int): número de amostras que o produtor vai gerar.
        """
        self.total = total
        self.produzidas = 0
        self.consumidos = []
        self.ultimo_progresso = time.monotonic()
        self.produtor_terminou = False
        self.consumidor_terminou = False
        self.travou = False

    def anotar_producao(self):
        """Conta uma amostra colocada no buffer pelo produtor. Sem retorno."""
        self.produzidas += 1

    def anotar_consumo(self, valor):
        """Guarda um valor recebido pelo consumidor e marca o progresso.

        Parâmetros:
            valor: o que o consumidor leu do buffer (normalmente um int).
        Retorno:
            None.
        """
        self.consumidos.append(valor)
        self.ultimo_progresso = time.monotonic()

    def parado_ha(self):
        """Retorna há quantos segundos (float) o consumidor não recebe nada."""
        return time.monotonic() - self.ultimo_progresso


def ler_argumentos(descricao):
    """Lê os argumentos de linha de comando comuns às três versões.

    Parâmetros:
        descricao (str): texto exibido em --help.
    Retorno:
        argparse.Namespace com os campos `amostras` (int) e `execucao` (int,
        só usado como rótulo no relatório).
    """
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument("-a", "--amostras", type=int, default=TOTAL_AMOSTRAS,
                        help=f"amostras por execução (padrão {TOTAL_AMOSTRAS})")
    parser.add_argument("-e", "--execucao", type=int, default=1,
                        help="número da execução, só para o rótulo do relatório")
    return parser.parse_args()


def executar(nome_versao, produtor, consumidor, registro, numero_execucao=1):
    """Roda produtor e consumidor em threads, vigia travamento e imprime o relatório.

    Funcionamento: cria as duas threads como daemon (assim um deadlock não
    impede o programa de terminar), e a thread principal vira um watchdog que
    acorda a cada 50 ms. A execução termina quando o consumidor sai do laço
    ou quando ele passa LIMITE_TRAVAMENTO_S sem receber nada (travamento).

    Parâmetros:
        nome_versao (str): rótulo da versão, por exemplo "Versão 2".
        produtor (callable): função sem argumentos executada pela thread
            produtora.
        consumidor (callable): função sem argumentos executada pela thread
            consumidora.
        registro (Registro): registro compartilhado com as duas funções.
        numero_execucao (int): rótulo da execução no relatório.
    Retorno:
        dict com o resumo (ver `resumir`).
    """
    inicio = time.monotonic()
    t_prod = threading.Thread(target=produtor, name="sensor", daemon=True)
    t_cons = threading.Thread(target=consumidor, name="motor", daemon=True)
    t_prod.start()
    t_cons.start()

    while t_cons.is_alive():
        t_cons.join(timeout=0.05)
        if t_cons.is_alive() and registro.parado_ha() > LIMITE_TRAVAMENTO_S:
            registro.travou = True
            break

    resumo = resumir(registro, time.monotonic() - inicio)
    imprimir_relatorio(nome_versao, numero_execucao, resumo, t_prod, t_cons)
    return resumo


def resumir(registro, duracao_s):
    """Calcula as métricas pedidas no enunciado.

    Definições usadas:
        consumidas: quantas leituras o consumidor fez (contando repetições).
        duplicadas: leituras a mais de um valor que já tinha sido lido
            (consumidas - valores distintos válidos - leituras inválidas).
        perdidas: valores que o produtor gerou e o consumidor nunca recebeu.
        invalidas: leituras de uma posição que nunca foi escrita (None) ou de
            um valor fora da faixa produzida.

    Parâmetros:
        registro (Registro): registro da execução.
        duracao_s (float): tempo total da execução em segundos.
    Retorno:
        dict com as chaves produzidas, consumidas, perdidas, duplicadas,
        invalidas, travou, duracao_s e fora_de_ordem.
    """
    validos = [v for v in registro.consumidos
               if isinstance(v, int) and 0 <= v < registro.produzidas]
    invalidas = len(registro.consumidos) - len(validos)
    contagem = Counter(validos)
    distintos = len(contagem)
    duplicadas = len(validos) - distintos
    perdidas = registro.produzidas - distintos
    fora_de_ordem = sum(1 for a, b in zip(validos, validos[1:]) if b <= a)
    return {
        "produzidas": registro.produzidas,
        "consumidas": len(registro.consumidos),
        "perdidas": perdidas,
        "duplicadas": duplicadas,
        "invalidas": invalidas,
        "fora_de_ordem": fora_de_ordem,
        "travou": registro.travou,
        "duracao_s": duracao_s,
    }


def imprimir_relatorio(nome_versao, numero_execucao, resumo, t_prod, t_cons):
    """Imprime o relatório de uma execução no terminal.

    Parâmetros:
        nome_versao (str): rótulo da versão.
        numero_execucao (int): rótulo da execução.
        resumo (dict): saída de `resumir`.
        t_prod, t_cons (threading.Thread): usados para mostrar se as threads
            ainda estavam vivas (presas) no fim.
    Retorno:
        None. Também escreve uma linha CSV em stderr com prefixo "CSV;", que o
        script rodar_tudo.sh usa para montar a tabela.
    """
    r = resumo
    linha = "=" * 60
    print(linha)
    print(f"{nome_versao} - execução {numero_execucao}   (N = {N}, "
          f"Python {sys.version.split()[0]}, PID {os.getpid()})")
    print(linha)
    print(f"  amostras produzidas : {r['produzidas']:>6}")
    print(f"  amostras consumidas : {r['consumidas']:>6}")
    print(f"  perdidas            : {r['perdidas']:>6}")
    print(f"  duplicadas          : {r['duplicadas']:>6}")
    print(f"  leituras inválidas  : {r['invalidas']:>6}")
    print(f"  fora de ordem       : {r['fora_de_ordem']:>6}")
    print(f"  travou?             : {'SIM' if r['travou'] else 'não'}")
    if r["travou"]:
        print(f"    -> consumidor ficou {LIMITE_TRAVAMENTO_S:.0f} s sem receber "
              f"nada; thread sensor viva={t_prod.is_alive()}, "
              f"thread motor viva={t_cons.is_alive()}")
    print(f"  duração             : {r['duracao_s']:.2f} s")
    print(linha)
    sys.stdout.flush()
    print(f"CSV;{nome_versao};{numero_execucao};{r['produzidas']};"
          f"{r['consumidas']};{r['perdidas']};{r['duplicadas']};"
          f"{r['invalidas']};{'sim' if r['travou'] else 'não'};"
          f"{r['duracao_s']:.2f}", file=sys.stderr)
