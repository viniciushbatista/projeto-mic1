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

def simular_ula(A, B, instrucao_6bits):
    """
    Simula o comportamento de hardware da ULA da Mic-1 para palavras de 32 bits.
    Instrução de 6 bits no formato: [INVA, ENA, ENB, INC, F0, F1]
    """
    # Isolando cada bit de controle (da esquerda para a direita)
    INVA = (instrucao_6bits >> 5) & 1
    ENA  = (instrucao_6bits >> 4) & 1
    ENB  = (instrucao_6bits >> 3) & 1
    INC  = (instrucao_6bits >> 2) & 1
    F0   = (instrucao_6bits >> 1) & 1
    F1   = (instrucao_6bits >> 0) & 1

    # --- Estágio 1: Filtro de Entrada (Enable e Inversão) ---
    A_enable = A if ENA == 1 else 0
    A_efetivo = (~A_enable & 0xFFFFFFFF) if INVA == 1 else A_enable
    B_efetivo = B if ENB == 1 else 0

    # --- Estágio 2: Processamento Paralelo ---
    op_and   = A_efetivo & B_efetivo
    op_or    = A_efetivo | B_efetivo
    op_not_b = ~B_efetivo & 0xFFFFFFFF
    
    soma_pura = A_efetivo + B_efetivo + INC
    op_soma   = soma_pura & 0xFFFFFFFF

    # --- Estágio 3 e 4: Decodificador e Seleção de Saída ---
    seletor = (F1 << 1) | F0  

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

    return S, vai_um


def executar_etapa1(nome_arquivo_entrada, nome_arquivo_log):
    # Valores iniciais idênticos ao do seu arquivo de exemplo
    B = 0b00000000000000000000000000000001
    A = 0b11111111111111111111111111111111
    
    PC = 1  # No log, o primeiro ciclo começa com PC = 1

    try:
        with open(nome_arquivo_entrada, 'r') as arquivo_in, open(nome_arquivo_log, 'w') as arquivo_log:
            
            # Cabeçalho inicial com os valores de partida
            arquivo_log.write(f"b = {B:032b}\na = {A:032b}\n\nStart of Program\n")
            arquivo_log.write("=" * 60 + "\n")

            for num_ciclo, linha in enumerate(arquivo_in, start=1):
                linha_limpa = linha.strip()
                if not linha_limpa:
                    continue
                
                IR_str = linha_limpa
                IR_int = int(IR_str, 2)

                # Executa a ULA
                S, co = simular_ula(A, B, IR_int)

                # Escreve os dados do ciclo atual formatados estritamente em binário (:032b)
                arquivo_log.write(f"Cycle {num_ciclo}\n\n")
                arquivo_log.write(f"PC = {PC}\n")
                arquivo_log.write(f"IR = {IR_str}\n")
                arquivo_log.write(f"b = {B:032b}\n")
                arquivo_log.write(f"a = {A:032b}\n")
                arquivo_log.write(f"s = {S:032b}\n")
                arquivo_log.write(f"co = {co}\n")
                arquivo_log.write("=" * 60 + "\n")
                
                # Atualização crucial para o próximo ciclo:
                # O registrador A recebe o resultado S gerado pela ULA neste ciclo
                A = S
                PC += 1
                
            # Fim do arquivo (End of Program)
            arquivo_log.write(f"Cycle {PC}\n")
            arquivo_log.write("> Line is empty, EOP.\n")

        print(f"Log binário gerado com sucesso em: '{nome_arquivo_log}'")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{nome_arquivo_entrada}' não encontrado.")

# --- Inicialização ---
if __name__ == "__main__":
    executar_etapa1("etapa1.txt", "saida_etapa1.txt")