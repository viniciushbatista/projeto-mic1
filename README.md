# Simulador Mic-1

Simulação em Python de uma versão modificada da microarquitetura **Mic-1** (Tanenbaum), feita em etapas para a disciplina de Arquitetura de Computadores II da UFPB.

O programa lê instruções e estados de registradores de arquivos `.txt`, executa ciclo a ciclo e grava a saída com o estado da máquina após cada passo.

## Etapas

| Etapa | O que foi implementado |
|---|---|
| **1** | ULA que lê palavras de controle de um arquivo, guarda cada uma no registrador de instrução e executa as operações |
| **2** | ULA com 8 bits de controle (SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC), registradores e barramentos B e C |
| **3** | Controle de memória (READ e WRITE) na microinstrução, que passa a ter 23 bits, e tradução das instruções IJVM `ILOAD x`, `DUP` e `BIPUSH byte` em microinstruções |

Formato da microinstrução na etapa 3: **ULA (8) + Barramento C (9) + Memória (2) + Barramento B (4)**

## Estrutura

```
etapa 1/   ula.py
etapa 2/   tarefa 1/ulaApsTwo.py
           tarefa 2/registradores.py  (+ arquivos de entrada e saída)
etapa 3/   ijvm.py                    (+ instruções, microinstruções, dados e saídas)
```

## Como rodar

```bash
cd "etapa 3"
python ijvm.py
```

Os arquivos de entrada ficam na mesma pasta de cada etapa e as saídas geradas são salvas como `saida_*.txt`.

## O que aprendi

Como uma instrução de alto nível vira uma sequência de microinstruções, como a ULA e os barramentos são controlados bit a bit e como a memória entra no ciclo de busca e execução.
