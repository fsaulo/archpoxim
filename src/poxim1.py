import sys

# Define global registers
# IR -> R[28], PC -> R[29], SP -> R[30], SR -> R[31]
R  = [uint32 * 0 for uint32 in range(32)]

def mov(args):
    global R
    if args != 0:
        z    = args >> 21 & 0x1F
        R[z] = args >>  0 & 0x1FFFFF if z != 0 else 0x0
        ins  = 'mov r{},{}'.format(z, R[z]).ljust(25) 
        cmd  = '{}:\t{}\tR{}={}'.format(phex(R[29]), ins, z, phex(R[z]))
        __stdout(cmd)
        __incaddr()
        return cmd
    else:
        __nop()

def add(args):
    global R
    z = args >> 21 & 0x1F
    x = args >> 16 & 0x1F
    y = args >> 11 & 0x1F
    __clrsr()
    R[z] = R[x] + R[y] if z != 0 else 0x0
    Rx31 = R[x] >> 31 & 0x1
    Ry31 = R[y] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    R[31] |= 0x40 if R[z]  == 0 else 0x0
    R[31] |= 0x10 if Rx31  == 1 else 0x0 
    R[31] |= 0x04 if (Rx31 == Ry31) and (Rx31 != Rz31) else 0x0
    R[31] |= R[z] >> 32 & 0x1
    R[z] = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins  = 'add r{},r{},r{}'.format(z, x, y).ljust(25)
    res  = 'R{}=R{}+R{}={}'.format(z, x, y, phex(R[z]))
    cmd  = '{}:\t{}\t{},SR={}'.format(phex(R[29]), ins, res, phex(R[31]))
    __stdout(cmd)
    __incaddr()
    return cmd

def sub(args):
    global R
    z = args >> 21 & 0x1F
    x = args >> 16 & 0x1F
    y = args >> 11 & 0x1F
    __clrsr()
    R[z] = R[x] - R[y] if z != 0 else 0x0
    Rx31 = R[x] >> 31 & 0x1
    Ry31 = R[y] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    R[31] |= 0x40 if R[z]  == 0 else 0x0
    R[31] |= 0x10 if Rx31  == 1 else 0x0 
    R[31] |= 0x04 if (Rx31 != Ry31) and (Rx31 != Rz31) else 0x0
    R[31] |= R[z] >> 32 & 0x1
    R[z]  &= 0xFFFFFFFF if z != 0 else 0x0
    ins  = 'sub r{},r{},r{}'.format(z, x, y).ljust(25)
    res  = 'R{}=R{}-R{}={}'.format(z, x, y, phex(R[z]))
    cmd  = '{}:\t{}\t{},SR={}'.format(phex(R[29]), ins, res, phex(R[31]))
    __stdout(cmd)
    __incaddr()
    return cmd

def sla(args):
    global R
    z = args >> 21 & 0x1F
    x = args >> 16 & 0x1F
    y = args >> 11 & 0x1F
    l = args >> 0  & 0x1F
    B    = (R[z] << 0x08 | R[y]) << (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    __clrsr()
    R[31] |= 0x40 if B    == 0 else 0x0
    R[31] |= 0x08 if R[z] != 0 else 0x0
    ins = 'sla r{},r{},r{},{}'.format(z, x, x, l).ljust(25)
    A   = (R[z] << 0x08 | R[x])
    res = 'R{}:R{}=R{}:R{}<<{}={}'.format(z, x, z, y, l+1, phex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(phex(R[29]),ins, res, phex(R[31]))
    __stdout(cmd)
    __incaddr()
    return(cmd)

def addi(args):
    if debug: 
        print('addi')
    return 'addi'

def movs(args):
    global R
    z    = args >> 21 & 0x1F
    sig  = (-1) if args >> 0 & 0x100000 else 1
    R[z] = (args >> 0 & 0x1FFFFF) | 0xFFE00000 if z != 0 else 0x0
    unum = (args >> 0 & 0x1FFFFF) * sig
    ins  = 'movs r{},{}'.format(z, unum).ljust(25)
    cmd  = '{}:\t{}\tR{}={}'.format(phex(R[29]), ins, z, phex(R[z]))
    __stdout(cmd)
    __incaddr()
    return cmd

def phex(string, length=10):
    return '{0:#0{1}X}'.format(string, length).replace('X','x')

def bun(args):
    global R
    addr  = phex(R[29])
    ins   = 'bun {}'.format(args).ljust(25)
    R[29] = R[29] + 4 + (args << 2)
    cmd   = '{}:\t{}\tPC={}'.format(addr, ins, phex(R[29]))
    __stdout(cmd)
    return cmd

def inte(args):
    global R
    addr  = phex(R[29])

    if (args >> 0 & 0x3FFFFFF) == 0:
        R[29] = 0
        ins   = 'int 0'.ljust(25)
        CR    = phex(0x0)
        PC    = phex(R[29])
        cmd   = '{}:\t{}\tCR={},PC={}'.format(addr, ins, CR, PC)
        __stdout(cmd)
        __write(cmd)
        __interrupt()

def debug_mode(value=False):
    global debug
    debug = value


def parse_arg(content):
    global struct
    signal = int(content, 0x10)   # Convert buffer content to uint16
    op = hex(signal >> 26 & 0x7F) # Get the instruction first 6 bits  
    return struct[op]             # Return callable operation

def __subarg(args):
    subfunc = {
    '0x3' : sla
    }
    index = args >> 8 & 0x03
    cmd = subfunc[hex(index)](args)
    if cmd is not None: return cmd

def __stdout(output):
    if debug:
        print(output)

def __nop(): 
    pass # Nothing to do here...

def __incaddr():
    R[29] += 4

def __begin():
    global bus
    msg = '[START OF SIMULATION]\n'
    try:
        bus.write(msg)
        __stdout(msg.rstrip('\n'))
    except Exception as ex:
        print('[Errno ?] Error trying to start program')

def __interrupt():
    global bus
    msg = '[END OF SIMULATION]\n'
    try:
        bus.write(msg)
        __stdout(msg.rstrip('\n'))
        sys.exit()
    except Exception as ex:
        print('[Errno ?] Exit with status error')

def __init(line):
    global bus
    bus = line

def __clrsr():
    global R
    R[31] = 0

def __write(line):
    global bus
    try:
        bus.write(line)
        bus.write('\n')
    except FileNotFoundError as ex1:
        print('[Errno ?] Not possible to access bus')
    except TypeError as ex2:
        pass

def main(args):
    for arg in args:
        if arg == '--debug':
            debug_mode(True)

    try:
        file = sys.argv[1]
        with open(file, 'r') as bus:
            buffer = bus.read().splitlines()
    except FileNotFoundError as exception:
        print(exception)
        sys.exit()

    try:
        output = sys.argv[2]
        with open(output, 'w') as bus:
            __init(bus)         # Start bus, if file name provided
            __begin()           # Write starting sentence
            for instruc in buffer:
                call = parse_arg(instruc)           # Parse instruction word
                try:
                    word = 0x3FFFFFF                # Define 25-bit extractor
                    arg = int(instruc, 0x10) & word # Extract 25-bit buffer
                    cmd = call(arg)                 # Call function with args
                    __write(cmd)                    # Write result to the bus
                except Exception as ex2:
                    print(ex2)
                    print('INVALID INSTRUCTION')
            __interrupt()
    except IndexError as ex1:
        print('[Errno ?] Output file not provided')

struct = {
    '0x0' : mov,
    '0x1' : movs,
    '0x2' : add,
    '0x3' : sub,
    '0x4' : __subarg,
    '0x12': addi,
    '0x37': bun,
    '0x3f': inte
}

if __name__ == '__main__':
    debug = True
    bus   = None
    main(sys.argv)
