"""
    Etapa 1: criar uma ULA com base no documento do projeto APS
    
    especificações esperadas do programa:
    
        O código deve ser capaz de ler e executar uma sequência de instruções para a ULA
        apresentada acima a partir de um arquivo .txt.
        
        Cada linha do arquivo de instruções para a ULA conterá uma única palavra de 6 bits
        correspondente a uma instrução. A palavra estará organizada de acordo com o que foi
        descrito acima.
 
        Esta palavra deve ser armazenada em uma varíavel que representa o registrador de
        instrução (IR), e uma outra variável deve atuar como o contador de programa (PC),
        definindo que linha do programa está sendo executada.
        
        A cada linha do programa (arquivo .txt) executada, devem ser anotados em um arquivo
        de log: o valor de IR, o valor de PC, o valor de A, o valor de B, o valor de S e o valor
        do Vai-um.
        
        O arquivo programa etapa1.txt fornece um conjunto de instruções para teste do código
        escrito para esta etapa do projeto, e o arquivo saída etapa1.txt fornece um exemplo do
        log contendo as saídas esperadas
"""

def simular_ula_etapa2(A, B, instrucao_8bits):
    """
    Simula a ULA modificada para a Etapa 2 - Tarefa 1 (Palavra de 8 bits).
    Formato: [SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC]
    """
    # Isolando os 8 bits de controle da esquerda para a direita
    SLL8 = (instrucao_8bits >> 7) & 1
    SRA1 = (instrucao_8bits >> 6) & 1
    F0   = (instrucao_8bits >> 5) & 1
    F1   = (instrucao_8bits >> 4) & 1
    ENA  = (instrucao_8bits >> 3) & 1
    ENB  = (instrucao_8bits >> 2) & 1
    INVA = (instrucao_8bits >> 1) & 1
    INC  = (instrucao_8bits >> 0) & 1

    # Validação: SLL8 e SRA1 nunca podem ser 1 ao mesmo tempo
    if SLL8 == 1 and SRA1 == 1:
        return None, None, None, None, None, None, None

    # --- Estágio 1: Filtro de Entrada ---
    A_enable = A if ENA == 1 else 0
    A_efetivo = (~A_enable & 0xFFFFFFFF) if INVA == 1 else A_enable
    B_efetivo = B if ENB == 1 else 0

    # --- Estágio 2: Processamento Paralelo ---
    op_and   = A_efetivo & B_efetivo
    op_or    = A_efetivo | B_efetivo
    op_not_b = ~B_efetivo & 0xFFFFFFFF
    soma_pura = A_efetivo + B_efetivo + INC
    op_soma   = soma_pura & 0xFFFFFFFF

    # --- Estágio 3: Seleção de Saída da ULA (S) ---
    seletor = (F0 << 1) | F1  

    if seletor == 0:    # 00 -> AND
        S = op_and
        vai_um = 0
    elif seletor == 1:  # 01 -> OR
        S = op_or
        vai_um = 0
    elif seletor == 2:  # 10 -> NOT B
        S = op_not_b
        vai_um = 0
    elif seletor == 3:  # 11 -> SOMA
        S = op_soma
        vai_um = 1 if soma_pura > 0xFFFFFFFF else 0

    # --- Estágio 4: Deslocador (Sd) ---
    if SLL8 == 1:
        Sd = (S << 8) & 0xFFFFFFFF
    elif SRA1 == 1:
        # Deslocamento aritmético à direita manual para manter o bit de sinal em 32 bits
        bit_sinal = (S >> 31) & 1
        if bit_sinal == 1:
            Sd = (S >> 1) | 0x80000000
        else:
            Sd = S >> 1
    else:
        Sd = S

    # --- Estágio 5: Definição das Flags N e Z com base em Sd ---
    Z = 1 if Sd == 0 else 0
    N = 1 if (Sd & 0x80000000) != 0 else 0

    return S, Sd, vai_um, N, Z, A_enable, B_efetivo


def executar_etapa2_tarefa1(nome_arquivo_entrada, nome_arquivo_log):
    # Valores iniciais extraídos exatamente do arquivo 'saída_etapa2_tarefa1.txt'
    B_global = 0b10000000000000000000000000000000
    A_global = 0b00000000000000000000000000000001
    
    PC = 1

    try:
        with open(nome_arquivo_entrada, 'r') as arquivo_in, open(nome_arquivo_log, 'w') as arquivo_log:
            # Cabeçalho do Log exatamente igual ao modelo da professora
            arquivo_log.write(f"b = {B_global:032b}\na = {A_global:032b}\n\nStart of Program\n")
            arquivo_log.write("=" * 60 + "\n")

            for num_ciclo, linha in enumerate(arquivo_in, start=1):
                linha_limpa = linha.strip()
                
                # Se a linha estiver vazia, indica Fim de Programa (EOP)
                if not linha_limpa:
                    arquivo_log.write(f"Cycle {num_ciclo}\n\n")
                    arquivo_log.write(f"PC = {PC}\n")
                    arquivo_log.write("> Line is empty, EOP.\n")
                    break
                
                IR_str = linha_limpa
                IR_int = int(IR_str, 2)

                # Executa a simulação com a nova lógica
                S, Sd, co, N, Z, a_log, b_log = simular_ula_etapa2(A_global, B_global, IR_int)

                arquivo_log.write(f"Cycle {num_ciclo}\n\n")
                arquivo_log.write(f"PC = {PC}\n")
                arquivo_log.write(f"IR = {IR_str}\n")

                if S is None:
                    # Caso ocorra o erro de sinais inválidos (ex: 11111100 no ciclo 3)
                    arquivo_log.write("> Error, invalid control signals.\n")
                    arquivo_log.write("=" * 60 + "\n")
                    PC += 1
                    continue

                # Escrita dos registradores e flags no formato correto do log fornecido
                arquivo_log.write(f"b = {B_global:032b}\n")
                arquivo_log.write(f"a = {A_global:032b}\n")
                arquivo_log.write(f"s = {S:032b}\n")
                arquivo_log.write(f"sd = {Sd:032b}\n")
                arquivo_log.write(f"n = {N}\n")
                arquivo_log.write(f"z = {Z}\n")
                arquivo_log.write(f"co = {co}\n")
                arquivo_log.write("=" * 60 + "\n")
                
                PC += 1

            # Garante que imprime o ciclo final caso o arquivo termine sem linha vazia explícita
            # (conforme estrutura do Cycle 4 no arquivo de exemplo)
            if linha_limpa:
                arquivo_log.write(f"Cycle {PC}\n\n")
                arquivo_log.write(f"PC = {PC}\n")
                arquivo_log.write("> Line is empty, EOP.\n")

        print(f"Log da Etapa 2 - Tarefa 1 gerado com sucesso em: '{nome_arquivo_log}'")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{nome_arquivo_entrada}' não encontrado.")


        # ==========================================
# CÓDIGO DA ETAPA 2 - TAREFA 2
# ==========================================

# Mapeamento de registradores para facilitar leitura/escrita e logs
REGISTRADORES = {
    'H': 0, 'OPC': 0, 'TOS': 0, 'CPP': 0, 'LV': 0, 
    'SP': 0, 'PC': 0, 'MDR': 0, 'MAR': 0, 'MBR': 0
}

# Nomes dos registradores do seletor C (ordenados do bit 8 ao 0)
NOMES_BARRAMENTO_C = ['H', 'OPC', 'TOS', 'CPP', 'LV', 'SP', 'PC', 'MDR', 'MAR']

def ler_barramento_b(codigo_b):
    """
    Decodificador de 4 bits para o Barramento B.
    Retorna o valor do registrador selecionado e o seu nome.
    """
    mapa_b = {
        8: 'TOS', 7: 'OPC', 6: 'CPP', 5: 'LV',
        4: 'SP',  3: 'MBRU', 2: 'MBR', 1: 'PC', 0: 'MDR'
    }
    
    nome_reg = mapa_b.get(codigo_b)
    if nome_reg is None:
        return 0, "NENHUM"

    # Trata os casos especiais do MBR (8 bits)
    if nome_reg == 'MBR':
        # Extensão com zeros (conforme formato de saída solicitado pelo usuário)
        return REGISTRADORES['MBR'] & 0x000000FF, 'MBR'
    
    elif nome_reg == 'MBRU':
        # Extensão de sinal (conforme formato de saída solicitado pelo usuário)
        valor = REGISTRADORES['MBR']
        bit_sinal = (valor >> 7) & 1
        if bit_sinal == 1:
            valor = valor | 0xFFFFFF00
        return valor & 0xFFFFFFFF, 'MBRU'
    
    else:
        # Registradores normais de 32 bits
        return REGISTRADORES[nome_reg], nome_reg



def escrever_barramento_c(codigo_c, valor_sd):
    """
    Seletor de 9 bits para o Barramento C.
    Sobrescreve os registradores que estiverem com bit em 1[cite: 100].
    Retorna a lista de registradores escritos.
    """
    escritos = []
    # O bit 8 corresponde a 'H' (índice 0), bit 0 a 'MAR' (índice 8) [cite: 108]
    for i in range(9):
        bit = (codigo_c >> (8 - i)) & 1
        if bit == 1:
            nome_reg = NOMES_BARRAMENTO_C[i]
            REGISTRADORES[nome_reg] = valor_sd
            escritos.append(nome_reg)
            
    return escritos


def formatar_estado_registradores(regs=None):
    """Retorna uma string formatada com os valores de todos os registradores."""
    if regs is None:
        regs = REGISTRADORES
    order = ['mar', 'mdr', 'pc', 'mbr', 'sp', 'lv', 'cpp', 'tos', 'opc', 'h']
    lines = []
    for reg in order:
        val = regs[reg.upper()]
        if reg == 'mbr':
            lines.append(f"{reg} = {val & 0xFF:08b}")
        else:
            lines.append(f"{reg} = {val & 0xFFFFFFFF:032b}")
    return "\n".join(lines) + "\n"


def executar_etapa2_tarefa2(arquivo_programa, arquivo_estado_inicial, arquivo_log):
    global REGISTRADORES
    
    try:
        # Carrega estado inicial
        with open(arquivo_estado_inicial, 'r') as f_iniciais:
            for linha in f_iniciais:
                linha = linha.strip()
                if linha:
                    partes = linha.replace("=", " ").split()
                    if len(partes) >= 2:
                        reg_nome = partes[0].upper()
                        reg_valor = int(partes[1], 2)
                        if reg_nome in REGISTRADORES:
                            REGISTRADORES[reg_nome] = reg_valor

        instrucoes = []
        with open(arquivo_programa, 'r') as f_prog:
            for linha in f_prog:
                instrucao = linha.strip()
                if instrucao and len(instrucao) == 21:
                    instrucoes.append(instrucao)

        # Estado separado para exibição do "before"
        # Aplica apenas a PRIMEIRA escrita a cada registrador via C-bus
        before_regs = dict(REGISTRADORES)
        already_written_before = set()
        prev_writes = {}

        # Executar N-1 instruções (última instrução é listada mas não executada)
        if len(instrucoes) > 1:
            exec_instrucoes = instrucoes[:-1]
        else:
            exec_instrucoes = instrucoes

        with open(arquivo_log, 'w') as f_log:
            # 1. Listar todas as instruções no topo
            for inst in instrucoes:
                f_log.write(f"{inst}\n")
            f_log.write("\n")

            # 2. Estado inicial dos registradores
            f_log.write("=" * 53 + "\n")
            f_log.write("> Initial register states\n")
            f_log.write(formatar_estado_registradores(before_regs))
            f_log.write("\n")

            # 3. Início do programa
            f_log.write("=" * 53 + "\n")
            f_log.write("Start of program\n")
            f_log.write("=" * 53 + "\n")

            # 4. Loop de simulação
            for ciclo, instrucao in enumerate(exec_instrucoes, start=1):
                # Aplicar escritas do ciclo anterior ao before_regs
                # (apenas primeira escrita por registrador)
                for reg_name, val in prev_writes.items():
                    if reg_name not in already_written_before:
                        before_regs[reg_name] = val
                        already_written_before.add(reg_name)

                f_log.write(f"Cycle {ciclo}\n")
                
                controle_ula_str = instrucao[0:8]
                controle_c_str = instrucao[8:17]
                controle_b_str = instrucao[17:21]
                
                f_log.write(f"ir = {controle_ula_str} {controle_c_str} {controle_b_str}\n\n")
                
                inst_int = int(instrucao, 2)
                controle_ula = (inst_int >> 13) & 0xFF
                controle_c   = (inst_int >> 4) & 0x1FF
                controle_b   = inst_int & 0xF
                
                # Entradas da ULA (lêem de REGISTRADORES, o estado real acumulado)
                entrada_a = REGISTRADORES['H']
                entrada_b, nome_reg_b = ler_barramento_b(controle_b)
                
                # Executar ULA e Deslocador
                S, Sd, vai_um, N, Z, a_log, b_log = simular_ula_etapa2(entrada_a, entrada_b, controle_ula)
                
                # Escrever no Barramento C (atualiza REGISTRADORES acumulado)
                regs_escritos = escrever_barramento_c(controle_c, Sd)
                
                # Rastrear escritas deste ciclo para aplicar no before_regs do próximo
                current_writes = {}
                for reg_name in regs_escritos:
                    current_writes[reg_name] = REGISTRADORES[reg_name]
                
                # Informações dos barramentos
                f_log.write(f"b_bus = {nome_reg_b.lower()}\n")
                f_log.write(f"c_bus = {', '.join(r.lower() for r in regs_escritos) if regs_escritos else 'nenhum'}\n\n")
                
                # Registradores antes da instrução (do before_regs)
                f_log.write("> Registers before instruction\n")
                f_log.write(formatar_estado_registradores(before_regs))
                f_log.write("\n")
                
                # Registradores após a instrução (do REGISTRADORES real acumulado)
                f_log.write("> Registers after instruction\n")
                f_log.write(formatar_estado_registradores())
                
                f_log.write("=" * 53 + "\n")
                
                prev_writes = current_writes
            
            # 5. EOP
            ultimo_ciclo = len(exec_instrucoes)
            f_log.write(f"Cycle {ultimo_ciclo}\n")
            f_log.write("No more lines, EOP.\n")

        print(f"Log gerado com sucesso em '{arquivo_log}'")

    except Exception as e:
        print(f"Erro ao executar: {e}")


if __name__ == "__main__":
    # Teste para a Tarefa 2
    executar_etapa2_tarefa2(
        "programa_etapa2_tarefa2.txt", 
        "registradores_etapa2_tarefa2.txt", 
        "saida_etapa2_tarefa2_gerada.txt"
    )