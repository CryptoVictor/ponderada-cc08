"""
versao1.py - A4, Versão 1: buffer circular SEM sincronização.

Ponderada CC08 "Do pipeline ao deadlock" - pulseira sensorial Tato.
Autor: Victor Garcia dos Santos (N = 4)

A thread do sensor (produtora) gera as amostras 0, 1, 2, ... e a thread do
motor (consumidora) as retira de um buffer circular de N posições. As duas
usam um contador compartilhado `ocupadas` e espera ocupada (busy waiting).

Não há trava nenhuma. Para a condição de corrida aparecer, cada thread lê o
contador, chama time.sleep(0) (cede a CPU, simulando ser interrompida no pior
momento) e só depois escreve o valor novo. Assim uma atualização pode
sobrescrever a outra (lost update), e o contador deixa de bater com o que
realmente está no buffer.

Uso: python3 versao1.py            (20.000 amostras)
     python3 versao1.py -a 5000 -e 2
"""

import time

from comum import N, LIMITE_TRAVAMENTO_S, Registro, executar, ler_argumentos


class BufferSemSincronizacao:
    """Buffer circular com contador compartilhado e nenhuma exclusão mútua.

    Atributos:
        dados (list): as N posições; None significa "nunca escrita".
        entrada (int): próxima posição onde o produtor escreve.
        saida (int): próxima posição de onde o consumidor lê.
        ocupadas (int): contador compartilhado de posições ocupadas. É a
            variável disputada pelas duas threads (região crítica).
    """

    def __init__(self, tamanho):
        """Cria o buffer vazio.

        Parâmetros:
            tamanho (int): número de posições (N).
        """
        self.dados = [None] * tamanho
        self.entrada = 0
        self.saida = 0
        self.ocupadas = 0


def criar_produtor(buf, reg):
    """Monta a função da thread do sensor.

    Parâmetros:
        buf (BufferSemSincronizacao): buffer compartilhado.
        reg (Registro): registro da execução.
    Retorno:
        função sem argumentos que produz reg.total amostras.
    """

    def produtor():
        """Gera 0..total-1. Espera ocupada enquanto o buffer parece cheio."""
        for amostra in range(reg.total):
            while buf.ocupadas >= N:          # espera ocupada: "está cheio"
                if reg.travou:
                    return
            buf.dados[buf.entrada] = amostra
            buf.entrada = (buf.entrada + 1) % N
            reg.anotar_producao()
            # ---- região crítica: ler-modificar-escrever o contador ----
            valor = buf.ocupadas
            time.sleep(0)                      # interrompida no pior momento
            buf.ocupadas = valor + 1
            # -----------------------------------------------------------
        reg.produtor_terminou = True

    return produtor


def criar_consumidor(buf, reg):
    """Monta a função da thread do motor.

    Parâmetros:
        buf (BufferSemSincronizacao): buffer compartilhado.
        reg (Registro): registro da execução.
    Retorno:
        função sem argumentos que consome até o produtor acabar e o buffer
        parecer vazio, ou até ficar LIMITE_TRAVAMENTO_S sem receber nada.
    """

    def consumidor():
        """Retira amostras do buffer usando espera ocupada."""
        while True:
            while buf.ocupadas <= 0:          # espera ocupada: "está vazio"
                if reg.produtor_terminou:
                    reg.consumidor_terminou = True
                    return                     # fim normal
                if reg.parado_ha() > LIMITE_TRAVAMENTO_S:
                    reg.travou = True          # 1 s sem nada: travamento
                    return
            amostra = buf.dados[buf.saida]
            buf.saida = (buf.saida + 1) % N
            reg.anotar_consumo(amostra)        # "aciona o motor"
            # ---- região crítica: ler-modificar-escrever o contador ----
            valor = buf.ocupadas
            time.sleep(0)
            buf.ocupadas = valor - 1
            # -----------------------------------------------------------

    return consumidor


def main():
    """Ponto de entrada: lê os argumentos, roda uma execução e imprime o relatório."""
    args = ler_argumentos("A4 - Versão 1: sem sincronização (espera ocupada)")
    reg = Registro(args.amostras)
    buf = BufferSemSincronizacao(N)
    executar("Versão 1 (sem sincronização)", criar_produtor(buf, reg),
             criar_consumidor(buf, reg), reg, args.execucao)


if __name__ == "__main__":
    main()
