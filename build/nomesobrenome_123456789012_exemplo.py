import sys

def main(args):
    #Ilustrando uso de argumentos de programa
    print("#ARGS = %i"%len((args)))
    print("PROGRAMA = %s"%(args[0]))
    print("ARG1 = %s, ARG2 = %s" %(args[1], args[2]))
    #Abrindo Arquivos
    golden_input = open(sys.argv[1],'r')
    golden_output = open(sys.argv[2],'w')
    #
    # ...
    #
    #fechando arquivos
    golden_input.close()
    golden_output.close()
    #Finalizando programa

if __name__ == '__main__':
    main(sys.argv)
