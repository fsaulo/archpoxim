.text
    init:
        bun main
        int 0
        int 0
        int 0
        .align 5
    printf:
        l8 r3, [r2]
        cmpi r3, 0
        beq 3
        s8 [r1], r3
        addi r2, r2, 1
        bun -6
        ret
    array_out:
        mov r7, 0x40
        l32 r3, [r7]
        addi r7, r7, 1
        cmpi r7, 0x4A
        bge 1
        bun -5
        ret
    scanf:
        l8 r4, [r8]
        subi r5, r5, 1
        cmpi r5, 0
        beq 3
        s8 [r7], r4
        addi r7, r7, 1
        bun -7
        ret
    main:
        mov sp, 0x7FFC
        l32 r1, [stdout]
        l32 r8, [randint]
        mov r5, 10
        mov r7, 0x100
        mov r2, msg1
        call printf
        call scanf
        call array_out
        mov r2, msg2
        call printf
        int 0
.data
    space:
        .asciz " "
    msg1:
        .asciz "Input numbers:\n"
    msg2:
        .asciz "Sorted numbers:\n"
    stdout:
        .4byte 0x8888888B
    randint:
        .4byte 0x8888888C