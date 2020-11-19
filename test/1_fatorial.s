.text
	// Inicializacao
	init:
		bun main
		.align 5
	// Funcao fatorial
	fatorial:
		// Caso base
		cmpi r1, 0
		bne 2
		mov r2, 1
		bun 5
		// Caso recursivo
		push r1
		subi r1, r1, 1
		call fatorial
		pop r1
		mul r2, r2, r1
		// Retorno da funcao
		ret
	// Funcao principal
	main:
		// SP = 32 KiB
		mov sp, 0x7FFC
		// fatorial(3)
		mov r1, 3
		call fatorial
		// Fim
		int 0
