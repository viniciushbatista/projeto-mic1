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


if __name__ == "__main__":
    # Altere aqui para os nomes dos arquivos que você salvou no seu computador
    executar_etapa2_tarefa1("p_etapa2_tarefa1.txt", "saida_etapa2_tarefa1.txt")