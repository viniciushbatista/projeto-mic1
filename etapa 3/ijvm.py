"""
Projeto Mic-1 modificada - Arquitetura de Computadores II
Etapa 3 - Tarefa 1 (acesso à memória) + Entregável (ILOAD x, DUP, BIPUSH byte)

Este arquivo dá continuidade ao código já escrito nas Etapas 1 e 2 (ULA de 8 bits +
registradores + barramentos B e C). Reaproveita a mesma lógica e convenções já usadas
(mesmo mapeamento de barramento B, mesmo seletor de barramento C, mesma função de ULA)
e adiciona:

  1) Os bits de controle de memória (WRITE, READ) na microinstrução, que passa de 21
     para 23 bits: ULA(8) + Barramento C(9) + Memória(2) + Barramento B(4).
  2) A tradução das instruções de alto nível da IJVM (ILOAD x, DUP, BIPUSH byte) em
     sequências de microinstruções de 23 bits, executadas na mesma máquina.
"""

# ==========================================================
# ULA (mesma lógica da Etapa 2 - Tarefa 1)
# ==========================================================

def simular_ula(A, B, instrucao_8bits):
    """
    Simula a ULA de 8 bits de controle.
    Formato do controle: [SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC]
    """
    SLL8 = (instrucao_8bits >> 7) & 1
    SRA1 = (instrucao_8bits >> 6) & 1
    F0   = (instrucao_8bits >> 5) & 1
    F1   = (instrucao_8bits >> 4) & 1
    ENA  = (instrucao_8bits >> 3) & 1
    ENB  = (instrucao_8bits >> 2) & 1
    INVA = (instrucao_8bits >> 1) & 1
    INC  = (instrucao_8bits >> 0) & 1

    if SLL8 == 1 and SRA1 == 1:
        return None, None, None, None, None

    # --- Filtro de entrada ---
    A_enable = A if ENA == 1 else 0
    A_efetivo = (~A_enable & 0xFFFFFFFF) if INVA == 1 else A_enable
    B_efetivo = B if ENB == 1 else 0

    # --- Processamento paralelo ---
    op_and = A_efetivo & B_efetivo
    op_or = A_efetivo | B_efetivo
    op_not_b = ~B_efetivo & 0xFFFFFFFF
    soma_pura = A_efetivo + B_efetivo + INC
    op_soma = soma_pura & 0xFFFFFFFF

    # --- Seleção da saída S ---
    seletor = (F0 << 1) | F1
    if seletor == 0:
        S = op_and
        vai_um = 0
    elif seletor == 1:
        S = op_or
        vai_um = 0
    elif seletor == 2:
        S = op_not_b
        vai_um = 0
    else:
        S = op_soma
        vai_um = 1 if soma_pura > 0xFFFFFFFF else 0

    # --- Deslocador ---
    if SLL8 == 1:
        Sd = (S << 8) & 0xFFFFFFFF
    elif SRA1 == 1:
        bit_sinal = (S >> 31) & 1
        Sd = (S >> 1) | 0x80000000 if bit_sinal == 1 else S >> 1
    else:
        Sd = S

    Z = 1 if Sd == 0 else 0
    N = 1 if (Sd & 0x80000000) != 0 else 0

    return Sd, vai_um, N, Z, S


# ==========================================================
# Registradores e barramentos (mesma convenção da Etapa 2 - Tarefa 2)
# ==========================================================

REGISTRADORES = {
    'H': 0, 'OPC': 0, 'TOS': 0, 'CPP': 0, 'LV': 0,
    'SP': 0, 'PC': 0, 'MDR': 0, 'MAR': 0, 'MBR': 0
}

NOMES_BARRAMENTO_C = ['H', 'OPC', 'TOS', 'CPP', 'LV', 'SP', 'PC', 'MDR', 'MAR']

MAPA_B = {8: 'TOS', 7: 'OPC', 6: 'CPP', 5: 'LV', 4: 'SP', 3: 'MBRU', 2: 'MBR', 1: 'PC', 0: 'MDR'}
MAPA_B_INVERSO = {v: k for k, v in MAPA_B.items()}


def ler_barramento_b(codigo_b):
    nome_reg = MAPA_B.get(codigo_b)
    if nome_reg is None:
        return 0, "NENHUM"

    if nome_reg == 'MBR':
        return REGISTRADORES['MBR'] & 0x000000FF, 'MBR'
    elif nome_reg == 'MBRU':
        valor = REGISTRADORES['MBR']
        bit_sinal = (valor >> 7) & 1
        if bit_sinal == 1:
            valor = valor | 0xFFFFFF00
        return valor & 0xFFFFFFFF, 'MBRU'
    else:
        return REGISTRADORES[nome_reg], nome_reg


def escrever_barramento_c(codigo_c, valor_sd):
    escritos = []
    for i in range(9):
        bit = (codigo_c >> (8 - i)) & 1
        if bit == 1:
            nome_reg = NOMES_BARRAMENTO_C[i]
            REGISTRADORES[nome_reg] = valor_sd & 0xFFFFFFFF
            escritos.append(nome_reg)
    return escritos


def formatar_estado_registradores():
    ordem = ['mar', 'mdr', 'pc', 'mbr', 'sp', 'lv', 'cpp', 'tos', 'opc', 'h']
    linhas = []
    for reg in ordem:
        val = REGISTRADORES[reg.upper()]
        if reg == 'mbr':
            linhas.append(f"{reg} = {val & 0xFF:08b}")
        else:
            linhas.append(f"{reg} = {val & 0xFFFFFFFF:032b}")
    return "\n".join(linhas) + "\n"


def carregar_registradores(caminho):
    """Lê o arquivo de estado inicial dos registradores (ex.: registradores_etapa3_tarefa1.txt)."""
    with open(caminho, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            partes = linha.replace("=", " ").split()
            if len(partes) >= 2:
                nome = partes[0].upper()
                valor = int(partes[1], 2)
                if nome in REGISTRADORES:
                    REGISTRADORES[nome] = valor


# ==========================================================
# Memória de dados (nova para a Etapa 3)
# ==========================================================

def carregar_memoria(caminho):
    """Lê o arquivo .txt de memória de dados: uma palavra de 32 bits por linha."""
    memoria = []
    with open(caminho, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                memoria.append(int(linha, 2))
    return memoria


def formatar_memoria(memoria):
    return "\n".join(f"{valor & 0xFFFFFFFF:032b}" for valor in memoria) + "\n"


# ==========================================================
# Execução de uma microinstrução de 23 bits
# ==========================================================

def executar_microinstrucao(ir_str, memoria):
    """
    Executa uma única microinstrução de 23 bits sobre REGISTRADORES e a lista `memoria`
    (passada por referência, alterada em-loco quando há WRITE).

    Formato normal:  ULA(8) + C(9) + MEM(2) + B(4)
    Caso especial de "fetch" (usado no BIPUSH): quando os dois bits de memória (WRITE
    e READ) estão em 1 ao mesmo tempo, os 8 bits da ULA não são interpretados como
    sinais de controle, e sim como um byte de dado bruto: esse byte é colocado em MBR
    e, em seguida, H = MBR (estendido com zeros até 32 bits), sem passar pela ULA nem
    pelo barramento C.

    Retorna um dicionário com as informações necessárias para o log.
    """
    ula_str = ir_str[0:8]
    c_str = ir_str[8:17]
    mem_str = ir_str[17:19]
    b_str = ir_str[19:23]

    write_bit = int(mem_str[0])
    read_bit = int(mem_str[1])

    info = {
        'ir_formatado': f"{ula_str} {c_str} {mem_str} {b_str}",
        'b_bus': None,
        'c_bus': [],
        'especial_fetch': False,
    }

    if write_bit == 1 and read_bit == 1:
        # Caso especial: fetch (usado pelo BIPUSH byte)
        byte_valor = int(ula_str, 2)
        REGISTRADORES['MBR'] = byte_valor & 0xFF
        REGISTRADORES['H'] = REGISTRADORES['MBR'] & 0xFF  # extensão com zeros até 32 bits
        info['especial_fetch'] = True
        info['b_bus'] = 'nenhum'
        info['c_bus'] = ['h', 'mbr(fetch)']
        return info

    codigo_ula = int(ula_str, 2)
    codigo_c = int(c_str, 2)
    codigo_b = int(b_str, 2)

    entrada_a = REGISTRADORES['H']
    entrada_b, nome_b = ler_barramento_b(codigo_b)

    Sd, vai_um, N, Z, S = simular_ula(entrada_a, entrada_b, codigo_ula)

    regs_escritos = escrever_barramento_c(codigo_c, Sd)

    info['b_bus'] = nome_b.lower()
    info['c_bus'] = [r.lower() for r in regs_escritos]

    # Acesso à memória: ocorre DEPOIS da escrita no barramento C, usando o valor
    # (já atualizado) de MAR.
    endereco = REGISTRADORES['MAR']
    if write_bit == 1:
        if 0 <= endereco < len(memoria):
            memoria[endereco] = REGISTRADORES['MDR'] & 0xFFFFFFFF
    elif read_bit == 1:
        if 0 <= endereco < len(memoria):
            REGISTRADORES['MDR'] = memoria[endereco] & 0xFFFFFFFF

    return info


# ==========================================================
# Etapa 3 - Tarefa 1: executa um arquivo de microinstruções de 23 bits
# ==========================================================

def executar_etapa3_tarefa1(arquivo_microinstrucoes, arquivo_registradores, arquivo_dados, arquivo_log):
    global REGISTRADORES
    REGISTRADORES = {k: 0 for k in REGISTRADORES}

    carregar_registradores(arquivo_registradores)
    memoria = carregar_memoria(arquivo_dados)

    with open(arquivo_microinstrucoes, 'r') as f:
        instrucoes = [linha.strip() for linha in f if linha.strip()]

    with open(arquivo_log, 'w') as log:
        log.write("=" * 60 + "\n")
        log.write("Initial memory state\n")
        log.write("*" * 31 + "\n")
        log.write(formatar_memoria(memoria))
        log.write("*" * 31 + "\n")
        log.write("Initial register state\n")
        log.write("*" * 31 + "\n")
        log.write(formatar_estado_registradores())
        log.write("=" * 60 + "\n")
        log.write("Start of Program\n")
        log.write("=" * 60 + "\n")

        ciclo = 0
        for ciclo, ir_str in enumerate(instrucoes, start=1):
            log.write(f"Cycle {ciclo}\n")

            ula_str, c_str, mem_str, b_str = ir_str[0:8], ir_str[8:17], ir_str[17:19], ir_str[19:23]
            log.write(f"ir = {ula_str} {c_str} {mem_str} {b_str}\n")

            regs_antes = dict(REGISTRADORES)

            info = executar_microinstrucao(ir_str, memoria)

            log.write(f"b = {info['b_bus']}\n")
            log.write(f"c = {', '.join(info['c_bus']) if info['c_bus'] else 'nenhum'}\n")
            log.write("\n")

            log.write("> Registers before instruction\n")
            log.write("*" * 31 + "\n")
            regs_atuais = dict(REGISTRADORES)
            REGISTRADORES.clear()
            REGISTRADORES.update(regs_antes)
            log.write(formatar_estado_registradores())
            REGISTRADORES.clear()
            REGISTRADORES.update(regs_atuais)
            log.write("\n")

            log.write("> Registers after instruction\n")
            log.write("*" * 31 + "\n")
            log.write(formatar_estado_registradores())
            log.write("\n")

            log.write("> Memory after instruction\n")
            log.write("*" * 31 + "\n")
            log.write(formatar_memoria(memoria))
            log.write("=" * 60 + "\n")

        log.write(f"Cycle {ciclo + 1}\n")
        log.write("No more lines, EOP.\n")

    print(f"Log da Etapa 3 - Tarefa 1 gerado em: '{arquivo_log}'")


# ==========================================================
# Entregável: tradução de ILOAD x / DUP / BIPUSH byte em microinstruções
# ==========================================================

# Códigos de controle da ULA (8 bits) já usados/deduzidos a partir dos exemplos do
# enunciado (mesma lógica da função simular_ula):
#   Sd = B        -> SLL8 SRA1 F0 F1 ENA ENB INVA INC = 0 0 1 1 0 1 0 0
#   Sd = B + 1    -> 0 0 1 1 0 1 0 1
#   Sd = A (H)    -> 0 0 1 1 1 0 0 0
#   Sd = A + 1    -> 0 0 1 1 1 0 0 1
ULA_SD_B = "00110100"
ULA_SD_B_MAIS_1 = "00110101"
ULA_SD_A = "00111000"
ULA_SD_A_MAIS_1 = "00111001"


def bits_c(regs_ativos):
    bits = ['0'] * 9
    for i, nome in enumerate(NOMES_BARRAMENTO_C):
        if nome in regs_ativos:
            bits[i] = '1'
    return "".join(bits)


def bits_b(nome_reg):
    codigo = MAPA_B_INVERSO.get(nome_reg, 0)
    return format(codigo, '04b')


def bits_mem(operacao):
    if operacao == 'rd':
        return '01'
    elif operacao == 'wr':
        return '10'
    elif operacao == 'fetch':
        return '11'
    return '00'


def gerar_microinstrucoes_iload(x):
    """
    H = LV
    H = H+1        (repetido x vezes)
    MAR = H; rd
    MAR = SP = SP+1; wr
    TOS = MDR
    """
    micro = []
    micro.append(ULA_SD_B + bits_c(['H']) + bits_mem('') + bits_b('LV'))
    for _ in range(x):
        micro.append(ULA_SD_A_MAIS_1 + bits_c(['H']) + bits_mem('') + bits_b('MDR'))
    micro.append(ULA_SD_A + bits_c(['MAR']) + bits_mem('rd') + bits_b('MDR'))
    micro.append(ULA_SD_B_MAIS_1 + bits_c(['MAR', 'SP']) + bits_mem('wr') + bits_b('SP'))
    micro.append(ULA_SD_B + bits_c(['TOS']) + bits_mem('') + bits_b('MDR'))
    return micro


def gerar_microinstrucoes_dup():
    """
    MAR = SP = SP+1
    MDR = TOS; wr
    """
    micro = []
    micro.append(ULA_SD_B_MAIS_1 + bits_c(['MAR', 'SP']) + bits_mem('') + bits_b('SP'))
    micro.append(ULA_SD_B + bits_c(['MDR']) + bits_mem('wr') + bits_b('TOS'))
    return micro


def gerar_microinstrucoes_bipush(byte_str):
    """
    SP = MAR = SP+1
    fetch                  (2 bits de memória = 11; primeiros 8 bits = byte)
    MDR = TOS = H; wr
    """
    micro = []
    micro.append(ULA_SD_B_MAIS_1 + bits_c(['SP', 'MAR']) + bits_mem('') + bits_b('SP'))
    micro.append(byte_str + bits_c([]) + bits_mem('fetch') + '0000')
    micro.append(ULA_SD_A + bits_c(['MDR', 'TOS']) + bits_mem('wr') + bits_b('MDR'))
    return micro


def parse_instrucoes_ijvm(caminho):
    """Lê o arquivo de instruções IJVM (ILOAD x, DUP, BIPUSH byte)."""
    instrucoes = []
    with open(caminho, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            partes = linha.split()
            nome = partes[0].upper()
            if nome == 'ILOAD':
                instrucoes.append(('ILOAD', int(partes[1])))
            elif nome == 'DUP':
                instrucoes.append(('DUP', None))
            elif nome == 'BIPUSH':
                instrucoes.append(('BIPUSH', partes[1]))
    return instrucoes


def executar_entregavel(arquivo_instrucoes, arquivo_registradores, arquivo_dados, arquivo_log):
    global REGISTRADORES
    REGISTRADORES = {k: 0 for k in REGISTRADORES}

    carregar_registradores(arquivo_registradores)
    memoria = carregar_memoria(arquivo_dados)
    instrucoes_ijvm = parse_instrucoes_ijvm(arquivo_instrucoes)

    with open(arquivo_log, 'w') as log:
        log.write("=" * 60 + "\n")
        log.write("Initial memory state\n")
        log.write("*" * 31 + "\n")
        log.write(formatar_memoria(memoria))
        log.write("*" * 31 + "\n")
        log.write("Initial register state\n")
        log.write("*" * 31 + "\n")
        log.write(formatar_estado_registradores())
        log.write("=" * 60 + "\n")
        log.write("Start of Program\n")
        log.write("=" * 60 + "\n")

        ciclo_global = 0
        for idx, (tipo, arg) in enumerate(instrucoes_ijvm, start=1):
            if tipo == 'ILOAD':
                micro = gerar_microinstrucoes_iload(arg)
                titulo = f"ILOAD {arg}"
            elif tipo == 'DUP':
                micro = gerar_microinstrucoes_dup()
                titulo = "DUP"
            else:
                micro = gerar_microinstrucoes_bipush(arg)
                titulo = f"BIPUSH {arg}"

            log.write(f"Instruction {idx}: {titulo}\n")
            log.write("-" * 60 + "\n")

            for ir_str in micro:
                ciclo_global += 1
                ula_str, c_str, mem_str, b_str = ir_str[0:8], ir_str[8:17], ir_str[17:19], ir_str[19:23]

                log.write(f"Cycle {ciclo_global}\n")
                log.write(f"ir = {ula_str} {c_str} {mem_str} {b_str}\n")

                regs_antes = dict(REGISTRADORES)
                info = executar_microinstrucao(ir_str, memoria)

                log.write(f"b = {info['b_bus']}\n")
                log.write(f"c = {', '.join(info['c_bus']) if info['c_bus'] else 'nenhum'}\n")
                log.write("\n")

                log.write("> Registers before instruction\n")
                log.write("*" * 31 + "\n")
                regs_atuais = dict(REGISTRADORES)
                REGISTRADORES.clear()
                REGISTRADORES.update(regs_antes)
                log.write(formatar_estado_registradores())
                REGISTRADORES.clear()
                REGISTRADORES.update(regs_atuais)
                log.write("\n")

                log.write("> Registers after instruction\n")
                log.write("*" * 31 + "\n")
                log.write(formatar_estado_registradores())
                log.write("=" * 60 + "\n")

            # Memória de dados é reportada uma vez por instrução IJVM (ILOAD/DUP/BIPUSH),
            # após todas as suas microinstruções terem sido executadas.
            log.write(f"> Data memory after instruction {idx} ({titulo})\n")
            log.write("*" * 31 + "\n")
            log.write(formatar_memoria(memoria))
            log.write("=" * 60 + "\n")
            log.write("\n")

        log.write(f"Cycle {ciclo_global + 1}\n")
        log.write("No more instructions, EOP.\n")

    print(f"Log do Entregável gerado em: '{arquivo_log}'")


if __name__ == "__main__":
    # Teste da Etapa 3 - Tarefa 1 com os arquivos fornecidos
    executar_etapa3_tarefa1(
        "microinstruções_etapa3_tarefa1.txt",
        "registradores_etapa3_tarefa1.txt",
        "dados_etapa3_tarefa1.txt",
        "saida_etapa3_tarefa1_gerada.txt"
    )

    # Exemplo de teste do Entregável (crie um arquivo instrucoes.txt com linhas como:
    # BIPUSH 00110011 / DUP / ILOAD 1)
    import os
    if os.path.exists("instrucoes.txt"):
        executar_entregavel(
            "instrucoes.txt",
            "registradores_etapa3_tarefa1.txt",
            "dados_etapa3_tarefa1.txt",
            "saida_entregavel_gerada.txt"
        )