# Ponderada CC08: do pipeline ao deadlock

**Aluno:** Victor Garcia dos Santos (D1 = 6, D2 = 1, N = 4)

Análise de arquitetura, pipeline, processos, semáforos e deadlock da pulseira sensorial Tato, com a decisão do CTO.

- Relatório: [`ponderada/ponderada-tato.md`](ponderada/ponderada-tato.md)
- Código da A4: [`ponderada/codigo/`](ponderada/codigo/)
- Prints: [`ponderada/img/`](ponderada/img/)

## Como rodar as três versões da A4

Precisa só de Python 3.8 ou mais novo (sem bibliotecas externas). Entre na pasta do código:

```bash
cd ponderada/codigo
```

| Versão | Comando | O que mostra | Tempo aproximado |
|---|---|---|---|
| 1, sem sincronização | `python3 versao1.py` | condição de corrida: amostras perdidas e duplicadas | ~1 a 2 min |
| 2, três semáforos | `python3 versao2.py` | 20.000 consumidas, 0 perdidas, 0 duplicadas | ~4 s |
| 3, ordem trocada | `python3 versao3.py` | deadlock, detectado após 1 s sem consumo | ~1 s |

Opções (iguais nas três versões): `-a 5000` muda o número de amostras (padrão 20.000) e `-e 2` muda o rótulo da execução no relatório.

Para repetir as 9 execuções da tabela (3 por versão) e salvar os logs em `ponderada/codigo/logs/`:

```bash
bash ponderada/codigo/rodar_tudo.sh
```
