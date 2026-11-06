"""
versao2.py - A4, Versão 2: buffer circular com três semáforos.

Ponderada CC08 "Do pipeline ao deadlock" - pulseira sensorial Tato.
Autor: Victor Garcia dos Santos (N = 4)

Solução clássica do produtor-consumidor com buffer limitado:
  vazio  = Semaphore(N)  -> conta posições livres; produtor espera nele
  cheio  = Semaphore(0)  -> conta posições ocupadas; consumidor espera nele
  mutex  = Semaphore(1)  -> só uma thread mexe no buffer por vez

Ordem correta: cada thread espera primeiro o semáforo de CONTAGEM (vazio ou
cheio) e só depois pega o mutex. O time.sleep(0) da versão 1 foi mantido dentro
da região crítica de propósito: mesmo com a thread cedendo a CPU no pior
momento, nada se perde, porque a outra thread não entra enquanto o mutex está
ocupado.

Uso: python3 versao2.py            (20.000 amostras)
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
    """Monta a função da thread do sensor.

    Parâmetros:
        buf (BufferComSemaforos): buffer compartilhado.
        reg (Registro): registro da execução.
    Retorno:
        função sem argumentos que produz reg.total amostras.
    """

    def produtor():
        """Para cada amostra: wait(vazio), wait(mutex), escreve, signal(mutex), signal(cheio)."""
        for amostra in range(reg.total):
            buf.vazio.acquire()                # wait(vazio): espera vaga
            buf.mutex.acquire()                # wait(mutex): entra na região crítica
            buf.dados[buf.entrada] = amostra
            time.sleep(0)                      # mesma interrupção da versão 1
            buf.entrada = (buf.entrada + 1) % N
            reg.anotar_producao()
            buf.mutex.release()                # signal(mutex)
            buf.cheio.release()                # signal(cheio): avisa que tem item
        reg.produtor_terminou = True

    return produtor


def criar_consumidor(buf, reg):
    """Monta a função da thread do motor.

    Parâmetros:
        buf (BufferComSemaforos): buffer compartilhado.
        reg (Registro): registro da execução.
    Retorno:
        função sem argumentos que consome reg.total amostras.
    """

    def consumidor():
        """Para cada amostra: wait(cheio), wait(mutex), lê, signal(mutex), signal(vazio)."""
        for _ in range(reg.total):
            buf.cheio.acquire()                # wait(cheio): espera item
            buf.mutex.acquire()                # wait(mutex)
            amostra = buf.dados[buf.saida]
            time.sleep(0)
            buf.saida = (buf.saida + 1) % N
            buf.mutex.release()                # signal(mutex)
            buf.vazio.release()                # signal(vazio): libera a vaga
            reg.anotar_consumo(amostra)        # "aciona o motor"
        reg.consumidor_terminou = True

    return consumidor


def main():
    """Ponto de entrada: lê os argumentos, roda uma execução e imprime o relatório."""
    args = ler_argumentos("A4 - Versão 2: três semáforos (vazio, cheio, mutex)")
    reg = Registro(args.amostras)
    buf = BufferComSemaforos(N)
    executar("Versão 2 (semáforos)", criar_produtor(buf, reg),
             criar_consumidor(buf, reg), reg, args.execucao)


if __name__ == "__main__":
    main()
