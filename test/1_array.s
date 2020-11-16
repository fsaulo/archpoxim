// Segmento de codigo
.text
    // Tabela de vetor de interrupcao
    init:
        bun main
        .align 5
    // Funcao principal
    main:
        // Finalizacao de execucao
        int 0
// Segmento de dados
.data
    // Exemplos de vetores (alinhamento de 4 bytes)
    V0:
        .byte 0xAA, 0xBB, -1
    V1:
        .2byte 0x1111, -2, 0x3333, 0x4444
    V2:
        .4byte 0xABCDEF01, 0x12345678, 0b11110000111100001111000011110000
    V3:
        .fill 10
    V4:
        .fill 10, 1, -1
    V5:
        .fill 10, 2, 0xABC
    V6:
        .fill 10, 3, 0xABCDEF
    V7:
        .zero 9
