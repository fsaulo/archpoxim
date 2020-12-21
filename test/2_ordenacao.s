.text
    init:
        bun main
		nop
		nop
        bun isr
        .align 5
    isr:
        mov r1, cr
        mov r2, ipc
        reti
    main:
		mov r1, 0x123456
		movs r2, -1048576
		add r3, r1, r2
        mov sp, 0x7FFC
        int 0

