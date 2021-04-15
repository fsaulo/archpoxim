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
        addi r5, r5, 1
        // Topo da pilha, ou primeira posicao do vetor
        mov r7, r10
        // Leitura de 1 byte de stdin (R14 indica endereco do gerador pseudoaleatorio)
        l8 r4, [r14]
        // Decrementa contador
        subi r5, r5, 1
        cmpi r5, 0
        beq 3
        // Guarda 1 byte no endereco indicado por r7
        s8 [r7], r4
        // Incrementa o endereco de r7
        addi r7, r7, 1
        bun -7
        ret
    print_4byte:
        // Limpa registrador r3 para evitar leitura de lixo
        mov r3, r0
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
        mov r5, 0
        mov r6, 10
        mov r9, r10
        sra r9, r9, 2
        // Leitura do numero de 32 bits na memoria
        l32 r11, [r9]
        // Incrementa o apontador de memoria
        addi r10, r10, 4
        // Limpa memoria apos salvar valor no registrador
        mov r0, 0
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
        cmp r5, r20
        beq 1
        bun -20
        ret
    bsort:
        // Bubble sort um array de inteiros de 32-bits
        // Argumentos R8 -> Primeira posicao do array, R9 -> Tamanho do array
        mov r16, r8
        mov r17, r8
    bsort_next:
        mov r6, 0
        mov r2, 0
    bsort_loop:
        addi r3, r2, 1
        cmp r3, r9
        bge 11
        add r16, r8, r2
        add r17, r8, r3
        l32 r18, [r16]
        l32 r19, [r17]
        cmp r19, r18
        bat 3
        s32 [r16], r19
        s32 [r17], r18
        addi r6, r6, 1
        mov r2, r3
        bun -14
        call bsort_check
    bsort_check:
        cmpi r6, 0
        bgt 1
        bun 2
        subi r9, r9, 1
        call bsort_next
        ret
    main:
        // Carrega endereco do stack
        mov sp, 0x7FFC
        l32 r1, [stdout]
        l32 r14, [randint]
        mov r20, 5
        mov r21, 0x200
        // Tamanho do vetor multiplicado por 4 bytes
        muli r5, r20, 4
        // Posicao na memoria do primeiro elemento do vetor
        mov r10, r21
        // Gera N numeros aleatorios (leitura de N bytes de stdin)
        call generate_rand
        // Carrega r2 com mensagem de entrada
        mov r2, minput
        // Imprime conteudo de r2
        call printf
        // Imprime array no stdout, byte a byte
        call print_array
        // Carrega r2 com mensagem de saida
        mov r2, moutput
        // Imprime conteudo de r2
        call printf
        mov r8, r21
        mov r9, r20
        sra r8, r8, 2
        call bsort
        mov r10, r21
        call print_array
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
