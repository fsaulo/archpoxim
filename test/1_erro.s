.text
	init:
		bun main
		.align 5
	main:
		mov r1, 2
		mov r2, 3
		divi r2, r1, 0
		mov sp, 0x7FFC
		push r0
		push r0, r1, r2
		push r1, r0, r2
		push r2, r3, r0, r1
		push sr
		pop r0
		pop sr
		pop r3, r2, r1, r0, r0
		.4byte 0xF0F0F0F0
		int 0
