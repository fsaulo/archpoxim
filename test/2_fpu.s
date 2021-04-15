// Segmento de codigo
.text
    // Tabela de vetor de interrupcao
    init:
        bun main
        int 0
        int 0
        int 0
        int 0
        bun hw
        bun hw
        bun hw
        .align 5
    // ISR de hardware
    hw:
        // Empilhando registradores
        push r1, r2, r3, r4, sr
        // Lendo CR, IPC, X, Y, Z e CONTROL
        mov cr, cr
        mov ipc, ipc
        l32 r1, [r1]
        l32 r2, [r2]
        l32 r3, [r3]
        l8 r4, [r4]
        // Setando r6 (flag de espera)
        mov r6, 1
        // Desempilhando registradores
        pop sr, r4, r3, r2, r1
        // Retorno da ISR
        reti
    // Funcao de espera
    espera:
        // Repete enquanto r6 for zero
        cmpi r6, 0
        beq -2
        // Resetando flag de espera
        mov r6, 0
        // Retorno de funcao
        ret
    // Funcao principal
    main:
        // SP = 32 KiB
        mov sp, 0x7FFC
        // Habilitando interrupcao (IE = 1)
        sbr sr[1]
        // Carregando enderecos de memoria
        l32 r1, [X]
        l32 r2, [Y]
        l32 r3, [Z]
        l32 r4, [CONTROL]
        // X = 1, Y = 1
        mov r5, 1
        s32 [r1], r5
        s32 [r2], r5
        // Operacao de adicao
        mov r5, 1
        s8 [r4], r5
        call espera
        // Operacao de atribuicao (X = Z)
        mov r5, 5
        s8 [r4], r5
        call espera
        // Operacao de subtracao
        mov r5, 2
        s8 [r4], r5
        call espera
        // Operacao de multiplicacao (Y = 9)
        mov r5, 9
        s32 [r2], r5
        mov r5, 3
        s8 [r4], r5
        call espera
        // Operacao de atribuicao (Y = Z)
        mov r5, 6
        s8 [r4], r5
        call espera
        // Operacao de divisao
        mov r5, 4
        s8 [r4], r5
        call espera
        // Operacao de divisao (Y = 0)
        mov r5, 0
        s32 [r2], r5
        mov r5, 4
        s8 [r4], r5
        call espera
        // Operacao de teto (Z = 0.11111111)
        mov r5, 7
        s8 [r4], r5
        call espera
        // Operacao de piso (Z = 0.11111111)
        mov r5, 8
        s8 [r4], r5
        call espera
        // Operacao de arredondamento (Z = 0.11111111)
        mov r5, 9
        s8 [r4], r5
        call espera
        // Operacao invalida
        mov r5, 0xABC
        s8 [r4], r5
        call espera
        // Finalizacao de execucao
        int 0
// Segmento de dados
.data
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
        