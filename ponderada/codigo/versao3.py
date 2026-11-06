"""
versao3.py - A4, Versão 3: semáforos com a ordem trocada no produtor.

Ponderada CC08 "Do pipeline ao deadlock" - pulseira sensorial Tato.
Autor: Victor Garcia dos Santos (N = 4)

Igual à versão 2, com uma única diferença: o produtor faz wait(mutex) ANTES de
wait(vazio). Quando o buffer enche, o produtor dorme em `vazio` segurando o
mutex; o consumidor passa por `cheio`, mas dorme em `mutex`. Cada um espera um
sinal que só o outro pode dar: deadlock. O watchdog de comum.py percebe que o
consumidor ficou 1 s sem receber nada e registra o travamento.

Uso: python3 versao3.py            (20.000 amostras)
"""

import threading
import time

from comum import N, Registro, executar, ler_argumentos


class BufferComSemaforos:
    """Buffer circular de N posições protegido por vazio, cheio e mutex.

    Atributos:
        dados (list): as N posições.
        entrada (int): próxima posição de escrita.
        saida (int): próxima posição de leitura.
        vazio (threading.Semaphore): posições livres, começa em N.
        cheio (threading.Semaphore): posições ocupadas, começa em 0.
        mutex (threading.Semaphore): exclusão mútua, começa em 1.
    """

    def __init__(self, tamanho):
        """Cria o buffer e os três semáforos.

        Parâmetros:
            tamanho (int): número de posições (N).
        """
        self.dados = [None] * tamanho
        self.entrada = 0
        self.saida = 0
        self.vazio = threading.Semaphore(tamanho)
        self.cheio = threading.Semaphore(0)
        self.mutex = threading.Semaphore(1)


def criar_produtor(buf, reg):
    """Monta a função da thread do sensor, com a ordem dos waits TROCADA.

    Parâmetros:
        buf (BufferComSemaforos): buffer compartilhado.
        reg (Registro): registro da execução.
    Retorno:
        função sem argumentos que tenta produzir reg.total amostras.
    """

    def produtor():
        """Para cada amostra: wait(mutex), wait(vazio) <- ordem errada, escreve, signals."""
        for amostra in range(reg.total):
            buf.mutex.acquire()                # wait(mutex) PRIMEIRO (errado)
            buf.vazio.acquire()                # wait(vazio): dorme segurando o mutex
            buf.dados[buf.entrada] = amostra
            time.sleep(0)
            buf.entrada = (buf.entrada + 1) % N
            reg.anotar_producao()
            buf.mutex.release()
            buf.cheio.release()
        reg.produtor_terminou = True

    return produtor


def criar_consumidor(buf, reg):
    """Monta a função da thread do motor (idêntica à versão 2).

    Parâmetros:
        buf (BufferComSemaforos): buffer compartilhado.
        reg (Registro): registro da execução.
    Retorno:
        função sem argumentos que tenta consumir reg.total amostras.
    """

    def consumidor():
        """Para cada amostra: wait(cheio), wait(mutex), lê, signal(mutex), signal(vazio)."""
        for _ in range(reg.total):
            buf.cheio.acquire()
            buf.mutex.acquire()                # fica preso aqui no deadlock
            amostra = buf.dados[buf.saida]
            time.sleep(0)
            buf.saida = (buf.saida + 1) % N
            buf.mutex.release()
            buf.vazio.release()
            reg.anotar_consumo(amostra)
        reg.consumidor_terminou = True

    return consumidor


def main():
    """Ponto de entrada: lê os argumentos, roda uma execução e imprime o relatório."""
    args = ler_argumentos("A4 - Versão 3: semáforos com ordem trocada (deadlock)")
    reg = Registro(args.amostras)
    buf = BufferComSemaforos(N)
    executar("Versão 3 (ordem trocada)", criar_produtor(buf, reg),
             criar_consumidor(buf, reg), reg, args.execucao)


if __name__ == "__main__":
    main()
