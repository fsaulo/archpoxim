// Segmento de codigo
.text
    // Tabela de vetor de interrupcao
    init:
        bun main
        int 0
        int 0
        int 0
        bun isr_hw1
        .align 5
    // Rotina de tratamento de interrupcao
    isr_hw1:
        // Checagem de codigo de interrupcao
        mov r1, cr
        mov r2, ipc
        l32 r3, [codigo]
        cmp r1, r3
        bne 1
        // Interrupcao de software 100
        int 100
        // Retorno de interrupcao
        reti
    // Funcao principal
    main:
        // SP = 32 KiB
        mov sp, 0x7FFC
        // Habilitando interrupcao (IE = 1)
        sbr sr[1]
        // R1 = valor do contador
        l32 r1, [valor]
        // R2 = endereco do contador
        l32 r2, [watchdog]
        sra r2, r2, 2
        // Watchdog = R1
        s32 [r2], r1
        // Laco infinito
        bun -1
        // Finalizacao de execucao
        int 0
// Segmento de dados
.data
    // Codigo de interrupcao
    codigo:
        .4byte 0xE1AC04DA
    // Valor do contador
    valor:
        .4byte 0x80000064
    // Endereco do dispositivo
    watchdog:
        .4byte 0x80808080