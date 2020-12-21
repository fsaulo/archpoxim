// Segmento de codigo
.text
    // Tabela de vetor de interrupcao
    init:
        bun main
        .align 5
    // Procedimento de impressao
    printf:
        // Leitura de byte da mensagem
        l8 r3, [r2]
        // Comparando com '\0'
        cmpi r3, 0
        // Finalizando se for caractere nulo
        beq 3
        // Escreve no terminal
        s8 [r1], r3
        // Incrementa o ponteiro da mensagem
        addi r2, r2, 1
        // Repete a iteracao
        bun -6
        // Retorno da funcao
        ret
    // Funcao principal
    main:
        // SP = 32 KiB
        mov sp, 0x7FFC
        // R1 = endereco do terminal
        l32 r1, [terminal]
        // R2 = ponteiro da string
        mov r2, mensagem
        // printf
        call printf
        // Finalizacao de execucao
        int 0
// Segmento de dados
.data
    // Mensagem de texto
    mensagem:
        .asciz "\nHello world from Poxim!\n"
    // Endereco do dispositivo (OUT)
    terminal:
        .4byte 0x8888888B