import sys

# Define general purpose registers
# IR -> R[28], PC -> R[29], SP -> R[30], SR -> R[31]
R  = [uint32 * 0 for uint32 in range(32)]
PC = 0

def mov(args):
    global R
    if args != 0:
        z    = args >> 21 & 0x1F
        R[z] = args >>  0 & 0x1FFFFF if z != 0 else 0x0
        ins  = 'mov {},{}'.format(__r(z), R[z]).ljust(25)
        __incaddr()
        return '{}:\t{}\tR{}={}'.format(phex(__pc()), ins, z, phex(R[z]))
    else:
        __nop()

def add(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] + R[y] if z != 0 else 0x0
    Rx31 = R[x] >> 31 & 0x1
    Ry31 = R[y] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if Rx31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 == Ry31) and (Rx31 != Rz31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 else R[31] & ~(1<<0x00)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'add {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res  = 'R{}=R{}+R{}={}'.format(z, x, y, phex(R[z]))
    __incaddr()
    return  '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def sub(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] - R[y] if z != 0 else 0x0
    Rx31 = R[x] >> 31 & 0x1
    Ry31 = R[y] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if Rz31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 != Ry31) and (Rx31 != Rz31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 else R[31] & ~(1<<0x0)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'sub {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}-R{}={}'.format(z, x, y, phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))
    
def mul(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = R[x] * R[y]
    R[l] = B >> 32 & 0xFFFFFFFF if l != 0 else 0x0
    R[z] = B >> 0  & 0xFFFFFFFF if z != 0 else 0x0
    A = (R[l] << 0x08 | R[z])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x01 if R[l] != 0 else R[31] & ~(1<<0x00)
    ins = 'mul {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}:R{}=R{}*R{}={}'.format(l, z, x, y, phex(A, 18))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))
    
def sll(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (R[z] << 0x08 | R[x]) << (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 0x08 | R[x])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x01 if R[z] != 0 else R[31] & ~(1<<0x00)
    ins = 'sll {},{},{},{}'.format(__r(z), __r(x), __r(x), l).ljust(25)
    res = 'R{}:R{}=R{}:R{}<<{}={}'.format(z, x, z, y, l+1, phex(A, 18))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()),ins, res, phex(R[31]))
    
def muls(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = R[x] * R[y]
    R[l] = B >> 32 & 0xFFFFFFFF if l != 0 else 0x0
    R[z] = B >> 0  & 0xFFFFFFFF if z != 0 else 0x0
    A = (R[l] << 0x08 | R[z])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[l] != 0 else R[31] & ~(1<<0x03)
    ins = 'muls {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}:R{}=R{}*R{}={}'.format(l, z, x, y, phex(A, 18))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))
    
def sla(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (R[z] << 0x08 | R[x]) << (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 0x08 | R[x])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[z] != 0 else R[31] & ~(1<<0x03)
    ins = 'sla {},{},{},{}'.format(__r(z), __r(x), __r(x), l).ljust(25)
    res = 'R{}:R{}=R{}:R{}<<{}={}'.format(z, x, z, y, l+1, phex(A, 18))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()),ins, res, phex(R[31]))

def div(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F

    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
    except ZeroDivisionError:
        R[l] = 0
        R[z] = 0

    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    R[31] = R[31] | 0x01 if R[l] != 0 else R[31] & ~(1<<0x00)
    ins = 'div {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, phex(R[l]),z, x, y,phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))
    
def srl(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (R[z] << 0x08 | R[x]) >> (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 0x08 | R[x])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x01 if R[z] != 0 else R[31] & ~(1<<0x00)
    ins = 'srl {},{},{},{}'.format(__r(z), __r(x), __r(x), l).ljust(25)
    res = 'R{}:R{}=R{}:R{}>>{}={}'.format(z, x, z, y, l+1, phex(A, 18))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()),ins, res, phex(R[31]))
    
def divs(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
    except ZeroDivisionError:
        R[l] = 0
        R[z] = 0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    R[31] = R[31] | 0x08 if R[l] != 0 else R[31] & ~(1<<0x03)
    ins = 'divs {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, phex(R[l]),z, x, y,phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))
    
def sra(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (R[z] << 0x08 | R[x]) >> (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 0x08 | R[x])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[z] != 0 else R[31] & ~(1<<0x03)
    ins = 'sra {},{},{},{}'.format(__r(z), __r(x), __r(x), l).ljust(25)
    res = 'R{}:R{}=R{}:R{}>>{}={}'.format(z, x, z, y, l+1, phex(A, 18))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()),ins, res, phex(R[31]))
    
def cmpx(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    CMP = R[x] - R[y]
    CMP31 = CMP  >> 31 & 0x1
    Rx31  = R[x] >> 31 & 0x1
    Ry31  = R[y] >> 31 & 0x1
    R[31] = R[31] | 0x40 if CMP   == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if CMP31 == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if Rx31 != Ry31 and CMP31 != Rx31 else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if CMP >> 32 & 0x1 == 1 else R[31] & ~(1<<0x00)
    ins = 'cmp {},{}'.format(__r(x), __r(y)).ljust(25)
    __incaddr()
    return '{}:\t{}\tSR={}'.format(phex(__pc()), ins, phex(R[31]))

def andx(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] & R[y] if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'and {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}&R{}={}'.format(z, x, y, phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def orx(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] | R[y] if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'or {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}|R{}={}'.format(z, x, y, phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def notx(args):
    global R
    (x, _, z) = __get_index(args)
    R[z] = ~R[x] & 0xFFFFFFFF if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'not {},{}'.format(__r(z), __r(x)).ljust(25)
    res = 'R{}=~R{}={}'.format(z, x, phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def xor(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] ^ R[y] if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'xor {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}^R{}={}'.format(z, x, y, phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def addi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    R[z] = R[x] + __twos_comp(l) if z != 0 else 0x0
    Rx31 = R[x] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    l15  = l >> 15 & 0x1
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if Rx31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 == l15) and (Rz31 != Rx31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 else R[31] & ~(1<<0x00)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'addi {},{},{}'.format(__r(z), __r(z), l).ljust(25)
    res = 'R{}=R{}+{}={}'.format(z, x, phex(l), phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def subi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    R[z] = R[x] - __twos_comp(l) if z != 0 else 0x0
    Rx31 = R[x] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    l15  = l >> 15 & 0x1
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if Rx31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 != l15) and (Rz31 != Rx31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 == 1 else R[31] & ~(1<<0x00)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'subi {},{},{}'.format(__r(z), __r(z), __twos_comp(l, 32)).ljust(25)
    res = 'R{}=R{}-{}={}'.format(z, x, phex(l), phex(R[z]))
    __incaddr()
    return  '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def muli(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    R[z] = R[x] * __twos_comp(l) if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[z] >> 32 & 0xFFFFFFFF == 1 else R[31] & ~(1<<0x03)
    ins = 'muli {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}*{}={}'.format(z, x, phex(l), phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31])) 

def divi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    try:
        R[z] = R[x] // __twos_comp(l) if z != 0 else 0x0
    except ZeroDivisionError as ex:
        R[z] = 0x0
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    R[31] = 0
    ins = 'divi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}/{}={}'.format(z, x, phex(l), phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31])) 

def modi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    try:
        R[z] = R[x] % __twos_comp(l) if z != 0 else 0x0
    except ZeroDivisionError as ex:
        R[z] = 0x0
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    R[31] = 0
    ins = 'modi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}%{}={}'.format(z, x, phex(l), phex(R[z]))
    __incaddr()
    return '{}:\t{}\t{},SR={}'.format(phex(__pc()), ins, res, phex(R[31]))

def cmpi(args):
    (x, _, _) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    CMPI = R[x] - __twos_comp(l)
    CMPI31 = CMPI  >> 31 & 0x1
    Rx31 = R[x] >> 31 & 0x1
    l15  = l >> 15 & 0x1
    R[31] = R[31] | 0x40 if CMPI   == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if CMPI31 == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if Rx31   != l15 and CMPI31 != Rx31 else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if CMPI >> 32 & 0x1 == 1 else R[31] & ~(1<<0x00)
    ins = 'cmpi {},{}'.format(__r(x), __twos_comp(l)).ljust(25)
    __incaddr()
    return '{}:\t{}\tSR={}'.format(phex(__pc()), ins, phex(R[31]))

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
    R[29] =  R[29] + 4 + (args << 2)
    return '{}:\t{}\tPC={}'.format(addr, ins, phex(R[29]))

def bzd(args):
    msg = 'op: "bzd" NOT IMPLEMENTED'
    return msg

def movs(args):
    global R
    z    = args >> 21 & 0x1F
    sig  = (-1) if args >> 0 & 0x100000 else 1
    R[z] = (args >> 0 & 0x1FFFFF) | 0xFFE00000 if z != 0 else 0x0
    unum = (args >> 0 & 0x1FFFFF) * sig
    ins  = 'movs {},{}'.format(__r(z), unum).ljust(25)
    __incaddr()
    return '{}:\t{}\tR{}={}'.format(phex(__pc()), ins, z, phex(R[z]))

def intx(args):
    global R
    addr  = phex(R[29])
    if (args >> 0 & 0x3FFFFFF) == 0:
        R[29] = 0
        ins   = 'int 0'.ljust(25)
        cmd   = '{}:\t{}\tCR={},PC={}'.format(addr, ins, phex(0), phex(R[29]))
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
    index = args >> 8 & 0b111
    try:
        return subfunc[hex(index)](args)
    except KeyError as ex1:
        __badinstr()

def __stdout(output):
    if debug:
        print(output)

def __nop(): 
    pass # Nothing to do here...

def __pc():
    return R[29] - 4

def __incaddr():
    global R
    R[29] += 4

def __twos_comp(value, size=32):
    if (value & (1 << (size - 1))) != 0:
        return value - (1 << size)
    else:
        return value

def __r(reg):
    registers = {
        28 : 'ir',
        29 : 'pc',
        30 : 'sp',
        31 : 'sr'
    }
    try:
        res = registers[reg]
    except KeyError as ex:
        res = 'r{}'.format(reg)
    return res

def __get_index(args):
    z = args >> 21 & 0x1F
    x = args >> 16 & 0x1F
    y = args >> 11 & 0x1F
    return (x, y, z)

def __loadreg(inst):
    R[28] = inst

def __begin():
    msg = '[START OF SIMULATION]\n'
    try:
        bus.write(msg)
        __stdout(msg.rstrip('\n'))
    except Exception as ex:
        print('[Errno ?] Error trying to start program')

def __interrupt():
    msg = '[END OF SIMULATION]\n'
    try:
        bus.write(msg)
        __stdout(msg.rstrip('\n'))
        sys.exit()
    except Exception as ex:
        print('[Errno ?] Exit with status error')

def __badinstr():
    msg = '[INVALID INSTRUCTION @ {}]\n'.format(phex(R[29]))
    __write(msg)
    __stdout(msg.rstrip('\n'))
    __interrupt()

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
                    __stdout(cmd)                   # Write to stdout if debug on
                    __loadreg(arg)                  # Load current instruction to IR
                except KeyError as ex2:
                    __badinstr()
            __interrupt()
    except IndexError as ex1:
        print('[Errno ?] Output file not provided')

def parse_arg(content):
    global struct
    signal = int(content, 0x10)   # Convert buffer content to uint64
    op = hex(signal >> 26 & 0x7F) # Get the first 6-bits of the instruction
    try: 
        return struct[op]         # Return callable operation
    except KeyError as ex1:
        __badinstr()              # Instruction not listed as valid operation

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
