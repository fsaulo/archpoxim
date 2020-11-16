#include <stdio.h>

int main(int argc, char* argv[]) {
	// Ilustrando uso de argumentos de programa
	printf("#ARGS = %i\n", argc);
	printf("PROGRAMA = %s\n", argv[0]);
	printf("ARG1 = %s, ARG2 = %s\n", argv[1], argv[2]);
	// Abrindo arquivos
	FILE* input = fopen(argv[1], "r");
	FILE* output = fopen(argv[2], "w");
	// Depois de carregamento, o vetor contem as instrucoes e dados do arquivo hex
	// nop
	// nop
	// nop
	// int 0
	unsigned int mem[4] = { 0x00000000, 0x00000000, 0x00000000, 0x7C000000 };
	// Tem que repetir o processo ate o final
	// Lendo 1 opcode
	unsigned int opcode = (mem[0] & 0xFC000000) >> 26;
	// Decodificando 1 instrucao
	switch(opcode) {
		// OP = 000000
		case 0x00:
			printf("nop/mov\n");
			break;
		// OP = 011111
		case 0x3F:
			printf("int\n");
			break;
		// OP = Invalido
		default:
			printf("Codigo invalido!\n");

	}
	// Formatacao de saida em arquivo
	fprintf(output, "0x%08X:\t%-25s\t%s=%s+%s=0x%08X,SR=0x%08X\n", 12, "add r1,r2,r3", "R1", "R2", "R3", 0, 0x40);
	// Fechando arquivos
	fclose(input);
	fclose(output);
	// Finalizando programa
	return 0;
}
