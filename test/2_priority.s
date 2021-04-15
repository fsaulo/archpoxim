// Segmento de codigo
.text
    // Tabela de vetor de interrupcao
    init:
        bun main
        int 0
        int 0
        int 0
        bun hw1
        bun hw2
        bun hw3
        bun hw4
        .align 5
    // Hardware 1
    hw1:
        // Procedimento de atraso
        call atraso
        // Retorno da ISR
        reti
    // Hardware 2
    hw2:
        // Hardware 1
        mov r6, 1
        sll r6, r6, 31
        addi r6, r6, 3
        s32 [r1], r6
        // Procedimento de atraso
        call atraso
        // Retorno da ISR
        reti
    // Hardware 3
    hw3:
        // Hardware 2
        mov r6, 123
        s8 [r5], r6
        // Procedimento de atraso
        call atraso
        // Retorno da ISR
        reti
    // Hardware 4
    hw4:
        // Hardware 3
        mov r6, 1
        s8 [r5], r6
        // Procedimento de atraso
        call atraso
        // Retorno da ISR
        reti
    // Procedimento de atraso
    atraso:
        // Empilhando registradores
        push r1, sr
        // Atribuindo R1 = 5
        mov r1, 5
        // Laco de espera
        subi r1, r1, 1
        cmpi r1, 0
        bat -3
        // Desempilhando registradores
        pop sr, r1
        // Retorno do procedimento
        ret
    // Funcao principal
    main:
        // SP = 32 KiB
        mov sp, 0x7FFC
        // Habilitando interrupcao (IE = 1)
        sbr sr[1]
        // Carregando enderecos de memoria
        l32 r1, [WATCHDOG]
        l32 r2, [X]
        l32 r3, [Y]
        l32 r4, [Z]
        l32 r5, [CONTROL]
        // Hardware 4
        mov r6, 9
        s8 [r5], r6
        nop
        // Finalizacao de execucao
        int 8
// Segmento de dados
.data
    // Endereco do watchdog (alinhamento de 32 bits)
    WATCHDOG:
        .4byte 0x20202020
    // Registrador X (alinhamento de 32 bits)
    X:
        .4byte 0x20202220
    // Registrador Y (alinhamento de 32 bits)
    Y:
        .4byte 0x20202221
    // Registrador Z (alinhamento de 32 bits)
    Z:
        .4byte 0x20202222
    // Registrador de controle (alinhamento de 8 bits)
    CONTROL:
        .4byte 0x8080888F
