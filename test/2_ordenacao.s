.text
    init:
        bun main
        int 0
        int 0
        int 0
        .align 5
    printf:
        l8 r13, [r2]
        cmpi r13, 0
        beq 3
        s8 [r1], r13
        addi r2, r2, 1
        bun -6
        ret
    generate_rand:
        // Topo da pilha, ou primeira posicao do vetor
        mov r7, r10
        // Leitura de 1 byte de stdin
        l8 r4, [r8]
        subi r5, r5, 1
        cmpi r5, 0
        beq 3
        // Guarda 1 byte no endereco indicado por r7, incrementa o endereco
        s8 [r7], r4
        addi r7, r7, 1
        bun -7
        ret
    print_4byte:
        // Leitura de 1 byte desde o primeiro elemento do vetor
        l8 r3, [r9]
        // Apenas envia para stdout se caracter for diferente de 0
        cmpi r3, 0
        beq 3
        // Escrita de 1 byte em stdout
        s8 [r1], r3
        // Incrementa o apontador de memoria
        addi r9, r9, 1
        bun -6
        ret
    print_array:
        mov r9, r10
        sra r9, r9, 2
        // Leitura do numero de 32 bits na memoria
        l32 r11, [r9]
        // Incrementa o apontador de memoria
        addi r10, r10, 4
        // Limpa memoria apos salvar valor no registrador
        s32 [r9], r0
        // Define endereco na memoria para guardar temporariamente o numero
        mov r9, 0x1FF
        // Fatora numero de 32 bits com divisoes sucessivas por 10
        div r12, r11, r11, r6
        // Converte numero para ascii
        addi r12, r12, 0x30
        // Decrementa apontador
        subi r9, r9, 1
        // Armazena valor em ascii no endereco apontado pelo registrador r9
        s8 [r9], r12
        // Repete ate que o numero fatorado seja 0
        cmpi r11, 0
        beq 1
        bun -7
        // Imprime o numero convertido para ascii. Primeiro byte apontado por r9
        call print_4byte
        // Imprime um espaco entre o proximo numero
        mov r15, 0x20
        s8 [r1], r15
        // Incrementa contador ate que atinja tamanho do vetor
        addi r5, r5, 1
        cmpi r5, 100
        beq 1
        bun -20
        ret
    main:
        // Configuracao
        mov sp, 0x7FFC
        l32 r1, [stdout]
        l32 r8, [randint]
        // Tamanho do vetor multiplicado por 4 bytes
        mov r5, 400
        // Constante de fatoracao
        mov r6, 10
        // Posicao na memoria do primeiro elemento do vetor
        mov r10, 0x200
        // Gera N numeros aleatorios (Leitura de N bytes de stdin)
        call generate_rand
        // Imprime vetor de numeros
        mov r2, minput
        call printf
        call print_array
        mov r2, moutput
        call printf
        int 0
.data
    minput:
        .asciz "Input numbers:\n"
    moutput:
        .asciz "\nSorted numbers:\n"
    stdout:
        .4byte 0x8888888B
    randint:
        .4byte 0x8888888A
