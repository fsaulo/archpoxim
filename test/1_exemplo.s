.text
	init:
		bun main
		.align 5
	main:
		mov r1, 0x123456
		movs r2, -1048576
		add r3, r1, r2
		sla r0, r2, r2, 11
		sub r4, r2, r3
		mul r5, r4, r3
		sll r6, r5, r5, 1
		muls r7, r6, r5
		sla r8, r7, r7, 2
		div r9, r8, r7
		srl r10, r9, r9, 3
		divs r10, r11, r9, r8
		sra r12, r10, r10, 4
		cmp ir, pc
		and r13, r1, r5
		or r14, r2, r6
		not r15, r7
		xor r16, r16, r8
		addi r17, r17, +1
		subi r18, r18, -1
		muli r19, r17, 2
		divi r20, r19, 2
		modi r21, r19, 3
		cmpi r21, 0x20
		l8 r22, [main + 3]
		l16 r23, [main + 1]
		l32 r24, [main]
		s8 [main + 3], r22
		s16 [main + 1], r23
		s32 [main], r24
		bae 0
		bat 0
		bbe 0
		bbt 0
		beq 0
		bge 0
		bgt 0
		biv 0
		ble 0
		blt 0
		bne 0
		bni 0
		bnz 0
		bun 0
		bzd 0
		int 0
