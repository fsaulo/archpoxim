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

def mul(args):
    msg = 'op: "mul" NOT IMPLEMENTED'
    __stdout(msg)
    return msg

def sll(args):
    msg = 'op: "sll" NOT IMPLEMENTED'
    return msg

def muls(args):
    msg = 'op: "muls" NOT IMPLEMENTED'
    return msg

def sla(args):
    global R
    z = args >> 21 & 0x1F
    x = args >> 16 & 0x1F
    y = args >> 11 & 0x1F
    l = args >> 0  & 0x1F
    A = (R[z] << 0x08 | R[x])
    B = A << (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    R[31] |= 0x40 if A    == 0 else 0x0
    R[31] |= 0x08 if R[z] != 0 else 0x0
    ins = 'sla r{},r{},r{},{}'.format(l, z, x, l).ljust(25)
    res = 'R{}:R{}=R{}:R{}<<{}={}'.format(z, x, z, y, l+1, phex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(phex(R[29]),ins, res, phex(R[31]))
    __stdout(cmd)
    __incaddr()
    return(cmd)

def div(args):
    msg = 'op: "div" NOT IMPLEMENTED'
    return msg

def srl(args):
    msg = 'op: "srl" NOT IMPLEMENTED'
    return msg

def divs(args):
    msg = 'op: "divs" NOT IMPLEMENTED'
    return msg

def sra(args):
    msg = 'op: "sra" NOT IMPLEMENTED'
    return msg

def cmpx(args):
    msg = 'op: "cmpx" NOT IMPLEMENTED'
    return msg

def andx(args):
    msg = 'op: "andx" NOT IMPLEMENTED'
    return msg

def orx(args):
    msg = 'op: "orx" NOT IMPLEMENTED'
    return msg

def notx(args):
    msg = 'op: "notx" NOT IMPLEMENTED'
    return msg

def xor(args):
    msg = 'op: "xor" NOT IMPLEMENTED'
    return msg

def addi(args):
    msg = 'op: "addi" NOT IMPLEMENTED'
    return msg

def subi(args):
    msg = 'op: "subi" NOT IMPLEMENTED'
    return msg

def muli(args):
    msg = 'op: "muli" NOT IMPLEMENTED'
    return msg

def divi(args):
    msg = 'op: "divi" NOT IMPLEMENTED'
    return msg

def modi(args):
    msg = 'op: "modi" NOT IMPLEMENTED'
    return msg

def cmpi(args):
    msg = 'op: "cmpi" NOT IMPLEMENTED'
    return msg

def l8(args):
    msg = 'op: "l8" NOT IMPLEMENTED'
    return msg

def l16(args):
    msg = 'op: "l16" NOT IMPLEMENTED'
    return msg

def l32(args):
    msg = 'op: "l32" NOT IMPLEMENTED'
    return msg

def s8(args):
    msg = 'op: "s8" NOT IMPLEMENTED'
    return msg

def s16(args):
    msg = 'op: "s16" NOT IMPLEMENTED'
    return msg

def s32(args):
    msg = 'op: "s32" NOT IMPLEMENTED'
    return msg

def bae(args):
    msg = 'op: "bae" NOT IMPLEMENTED'
    return msg

def bat(args):
    msg = 'op: "bat" NOT IMPLEMENTED'
    return msg

def bbe(args):
    msg = 'op: "bbe" NOT IMPLEMENTED'
    return msg

def bbt(args):
    msg = 'op: "bbt" NOT IMPLEMENTED'
    return msg

def beq(args):
    msg = 'op: "beq" NOT IMPLEMENTED'
    return msg

def bge(args):
    msg = 'op: "bge" NOT IMPLEMENTED'
    return msg

def bgt(args):
    msg = 'op: "bgt" NOT IMPLEMENTED'
    return msg

def biv(args):
    msg = 'op: "biv" NOT IMPLEMENTED'
    return msg

def ble(args):
    msg = 'op: "ble" NOT IMPLEMENTED'
    return msg

def blt(args):
    msg = 'op: "blt" NOT IMPLEMENTED'
    return msg

def bne(args):
    msg = 'op: "bne" NOT IMPLEMENTED'
    return msg

def bni(args):
    msg = 'op: "bni" NOT IMPLEMENTED'
    return msg

def bnz(args):
    msg = 'op: "bnz" NOT IMPLEMENTED'
    return msg

def bun(args):
    global R
    addr  = phex(R[29])
    ins   = 'bun {}'.format(args).ljust(25)
    R[29] = R[29] + 4 + (args << 2)
    cmd   = '{}:\t{}\tPC={}'.format(addr, ins, phex(R[29]))
    __stdout(cmd)
    return cmd

def bzd(args):
    msg = 'op: "bzd" NOT IMPLEMENTED'
    return msg

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

def intx(args):
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

def phex(string, length=10):
    return '{0:#0{1}X}'.format(string, length).replace('X','x')

def debug_mode(value=False):
    global debug
    debug = value

def __subarg(args):
    subfunc = {
        '0x0' : mul,
        '0x1' : sll,
        '0x2' : muls,
        '0x3' : sla,
        '0x4' : div,
        '0x5' : srl,
        '0x6' : divs,
        '0x7' : sra
    }
    index = args >> 8 & 0x03
    cmd = subfunc[hex(index)](args)
    if cmd is not None: 
        return cmd

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

def parse_arg(content):
    global struct
    signal = int(content, 0x10)   # Convert buffer content to uint64
    op = hex(signal >> 26 & 0x7F) # Get the first 6-bits of the instruction 
    return struct[op]             # Return callable operation


if __name__ == '__main__':
    struct = {
        '0x0' : mov,
        '0x1' : movs,
        '0x2' : add,
        '0x3' : sub,
        '0x4' : __subarg,
        '0x5' : cmpx,
        '0x6' : andx,
        '0x7' : orx,
        '0x8' : notx,
        '0x9' : xor,
        '0x12': addi,
        '0x13': subi,
        '0x14': muli,
        '0x15': divi,
        '0x16': modi,
        '0x17': cmpi,
        '0x18': l8,
        '0x19': l16,
        '0x1a': l32,
        '0x1b': s8,
        '0x1c': s16,
        '0x1d': s32,
        '0x2a': bae,
        '0x2b': bat,
        '0x2c': bbe,
        '0x2d': bbt,
        '0x2e': beq,
        '0x2f': bge,
        '0x30': bgt,
        '0x31': biv,
        '0x32': ble,
        '0x33': blt,
        '0x34': bne,
        '0x35': bni,
        '0x36': bnz,
        '0x37': bun,
        '0x38': bzd,
        '0x3f': intx
    }

    debug = True
    bus   = None
    main(sys.argv)
