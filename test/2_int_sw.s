// Segmento de codigo
.text
    // Tabela de vetor de interrupcao
    init:
        bun main
        bun isr
        bun isr
        bun isr
        .align 5
    // Rotina de tratamento de interrupcao
    isr:
        // R1 = CR
        mov r1, cr
        // R2 = IPC
        mov r2, ipc
        // Retorno de ISR
        reti
    // Funcao principal
    main:
        // SP = 32 KiB
        mov sp, 0x7FFC
        // Interrupcao de software 5
        int 5
        // Habilitando interrupcao (IE = 1)
        sbr sr[1]
        // Divisao por zero
        div r1, r2, r0
        // Instrucao invalida
        .4byte 0xF0F0F0F0
        // Finalizacao de execucao
        int 0