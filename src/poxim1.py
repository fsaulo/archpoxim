import sys

# Define general purpose registers
# IR -> R[28], PC -> R[29], SP -> R[30], SR -> R[31]
R   = [uint32 * 0 for uint32 in range(32)]
MEM = 0
PC  = 0

def mov(args):
    global R
    if args != 0:
        z    = args >> 21 & 0x1F
        R[z] = args >>  0 & 0x1FFFFF if z != 0 else 0x0
        ins  = 'mov {},{}'.format(__r(z), R[z]).ljust(25)
        cmd  = '{}:\t{}\tR{}={}'.format(__hex(__pc()), ins, z, __hex(R[z]))
        __incaddr()
        return cmd, 0
    else:
        return __nop(), 0

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
    res = 'R{}=R{}+R{}={}'.format(z, x, y, __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}=R{}-R{}={}'.format(z, x, y, __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}:R{}=R{}*R{}={}'.format(l, z, x, y, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}:R{}=R{}:R{}<<{}={}'.format(z, x, z, y, l+1, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()),ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}:R{}=R{}*R{}={}'.format(l, z, x, y, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}:R{}=R{}:R{}<<{}={}'.format(z, x, z, y, l+1, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()),ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def div(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
    except ZeroDivisionError:
        pass
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    R[31] = R[31] | 0x01 if R[l] != 0 else R[31] & ~(1<<0x00)
    ins = 'div {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, __hex(R[l]),z, x, y,__hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}:R{}=R{}:R{}>>{}={}'.format(z, x, z, y, l+1, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()),ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def divs(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
    except ZeroDivisionError:
        pass
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    R[31] = R[31] | 0x08 if R[l] != 0 else R[31] & ~(1<<0x03)
    ins = 'divs {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, __hex(R[l]),z, x, y,__hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}:R{}=R{}:R{}>>{}={}'.format(z, x, z, y, l+1, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()),ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def cmpx(args):
    global R
    (x, y, _) = __get_index(args)
    CMP = R[x] - R[y]
    CMP31 = CMP  >> 31 & 0x1
    Rx31  = R[x] >> 31 & 0x1
    Ry31  = R[y] >> 31 & 0x1
    R[31] = R[31] | 0x40 if CMP   == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if CMP31 == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if Rx31 != Ry31 and CMP31 != Rx31 else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if CMP >> 32 & 0x1 == 1 else R[31] & ~(1<<0x00)
    ins = 'cmp {},{}'.format(__r(x), __r(y)).ljust(25)
    cmd = '{}:\t{}\tSR={}'.format(__hex(__pc()), ins, __hex(R[31]))
    __incaddr()
    return cmd, 0

def andx(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] & R[y] if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'and {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}&R{}={}'.format(z, x, y, __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def orx(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] | R[y] if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'or {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}|R{}={}'.format(z, x, y, __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def notx(args):
    global R
    (x, _, z) = __get_index(args)
    R[z] = ~R[x] & 0xFFFFFFFF if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'not {},{}'.format(__r(z), __r(x)).ljust(25)
    res = 'R{}=~R{}={}'.format(z, x, __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def xor(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] ^ R[y] if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if R[z] >> 31 & 0x1 == 1 else R[31] & ~(1<<0x04)
    ins = 'xor {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}^R{}={}'.format(z, x, y, __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}=R{}+{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

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
    res = 'R{}=R{}-{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def muli(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    R[z] = R[x] * __twos_comp(l) if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[z] >> 32 & 0xFFFFFFFF == 1 else R[31] & ~(1<<0x03)
    ins = 'muli {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}*{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def divi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    try:
        R[z] = R[x] // __twos_comp(l) if z != 0 else 0x0
    except ZeroDivisionError:
        pass
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    R[31] = 0
    ins = 'divi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}/{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def modi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    try:
        R[z] = R[x] % __twos_comp(l) if z != 0 else 0x0
    except ZeroDivisionError:
        R[z] = 0x0
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    R[31] = 0
    ins = 'modi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}%{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def cmpi(args):
    global R
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
    cmd = '{}:\t{}\tSR={}'.format(__hex(__pc()), ins, __hex(R[31]))
    __incaddr()
    return cmd, 0

def l8(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    address = R[x] + l
    R[z] = __read(address) & 0xFF if z != 0 else 0x0
    ins = 'l8 {},[{}+{}]'.format(__r(z), __r(x), l).ljust(25)
    res = 'R{}=MEM[{}]={}'.format(z, __hex(address), __hex(R[z], 4))
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def l16(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    address = R[x] + l << 1
    R[z] = __read(address) & 0xFFFF if z != 0 else 0x0
    ins = 'l16 {},[{}+{}]'.format(__r(z), __r(x), l).ljust(25)
    res = 'R{}=MEM[{}]={}'.format(z, __hex(address), __hex(R[z], 6))
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def l32(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    address = R[x] + l << 2
    R[z] = __read(address) & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'l32 {},[{}+{}]'.format(__r(z), __r(x), l).ljust(25)
    res = 'R{}=MEM[{}]={}'.format(z, __hex(address), __hex(R[z]))
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def s8(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    address = R[x] + l
    __overwrite(address, 1, R[z])
    ins = 's8 [{}+{}],{}'.format(__r(x), l, __r(z)).ljust(25)
    res = 'MEM[{}]=R{}={}'.format(__hex(address), z, __hex(R[z], 4))
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def s16(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    address = R[x] + l << 1
    __overwrite(address, 2, R[z])
    ins = 's16 [{}+{}],{}'.format(__r(x), l, __r(z)).ljust(25)
    res = 'MEM[{}]=R{}={}'.format(__hex(address), z, __hex(R[z], 6))
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def s32(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    address = R[x] + l << 2
    __overwrite(address, 4, R[z])
    ins = 's32 [{}+{}],{}'.format(__r(x), l, __r(z)).ljust(25)
    res = 'MEM[{}]=R{}={}'.format(__hex(address), z, __hex(R[z]))
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def bae(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC = R[29]
    CY = R[31] >> 0 & 0x1
    if CY == 0:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bae {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bat(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    CY = R[31] >> 0 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 0 and CY == 0:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bat {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bbe(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC = R[29]
    CY = R[31] >> 0 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 1 or CY == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bbe {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bbt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    CY = R[31] >> 0 & 0x1
    if CY == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bbt {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def beq(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC = R[29]
    ZN = R[31] >> 6 & 0x1
    if ZN == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'beq {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bge(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    if SN == OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bge {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bgt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 0 and SN == OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bgt {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def biv(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    IV = R[31] >> 2 & 0x1
    PC = R[29]
    jmp = 0
    if IV == 1:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2)
    else:
        __incaddr()
    ins = 'biv {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def ble(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 1 and SN != OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'ble {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def blt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    if SN != OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'blt {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bne(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC  = R[29]
    ZN = R[31] >> 6 & 0x1
    if ZN == 0:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bne {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bni(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    IV = R[31] >> 2 & 0x1
    PC = R[29]
    jmp = 0
    if IV == 0:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2)
    else:
        R[29] + 4
    ins = 'bni {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bnz(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC = R[29]
    ZD = R[31] >> 5 & 0x1
    if ZD == 0:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bnz {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bun(args):
    global R
    addr = __hex(R[29])
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = __twos_comp(reg)
    R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    ins = 'bun {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(addr, ins, __hex(R[29]))
    return cmd, jmp

def bzd(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0xFFFF) & 0x3FFFFFF
    jmp = 0
    PC = R[29]
    ZD = R[31] >> 5 & 0x1
    if ZD == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2)
    else:
        __incaddr()
    ins = 'bzd {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def movs(args):
    global R
    z    = args >> 21 & 0x1F
    sig  = (-1) if args >> 0 & 0x100000 else 1
    R[z] = (args >> 0 & 0x1FFFFF) | 0xFFE00000 if z != 0 else 0x0
    unum = (args >> 0 & 0x1FFFFF) * sig
    ins  = 'movs {},{}'.format(__r(z), unum).ljust(25)
    cmd  = '{}:\t{}\tR{}={}'.format(__hex(__pc()), ins, z, __hex(R[z]))
    __incaddr()
    return cmd, 0

def intx(args):
    global R
    addr  = __hex(R[29])
    if (args >> 0 & 0x3FFFFFF) == 0:
        R[29] = 0
        ins   = 'int 0'.ljust(25)
        cmd   = '{}:\t{}\tCR={},PC={}'.format(addr, ins, __hex(0), __hex(R[29]))
        __write(cmd)
        __interrupt()

def __hex(string, length=10):
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
    except KeyError:
        __badinstr()

def __stdout(output):
    if debug:
        print(output)

def __nop():
    return None # Nothing to do here...

def __pc():
    return R[29]

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
    except KeyError:
        res = 'r{}'.format(reg)
    return res

def __get_index(args):
    z = args >> 21 & 0x1F
    x = args >> 16 & 0x1F
    y = args >> 11 & 0x1F
    return (x, y, z)

def __loadreg(inst):
    global R
    R[28] = inst

def __begin():
    msg = '[START OF SIMULATION]'
    try:
        __write(msg)
    except Exception:
        print('[Errno ?] Error trying to start program')

def __interrupt():
    msg = '[END OF SIMULATION]'
    try:
        __write(msg)
        sys.exit()
    except Exception:
        print('[Errno ?] Exit with status error')

def __badinstr():
    msg = '[INVALID INSTRUCTION @ {}]'.format(__hex(R[29]))
    __write(msg)
    __interrupt()

def __overwrite(address, size, content):
    global MEM
    index = address // 4
    buffer = int(MEM[index], 16)
    byte = {1: 0xFF, 2: 0xFFFF, 3: 0xFFFFFF, 4: 0xFFFFFFFF}
    MEM[index] = __hex(buffer & ~byte[size] | content & byte[size])

def __read(address=None):
    global MEM
    if address is not None:
        index = address // 4
        return int(MEM[index], 16)
    else:
        return int(MEM, 16)

def __load(prog):
    global MEM
    MEM = prog
    print('[Debug: Loaded {} bytes into memory]'.format(len(prog)*4))

def __init(line):
    global bus
    bus = line

def __counter(arg):
    if arg < 0:
        return arg + 1
    elif arg == 0 or arg is None:
        return 1
    else:
        return arg

def __write(line):
    global bus
    if line is not None:
        try:
            __stdout(line)
            bus.write(line)
            bus.write('\n')
        except FileNotFoundError:
            print('[Errno ?] Not possible to access bus')
        except TypeError:
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
        index  = 0
        with open(output, 'w') as bus:
            __init(bus)    # Start bus, if file name provided
            __load(buffer) # Load program into virtual memory
            __begin()      # Write starting sentence
            while index < len(buffer):
                inst = buffer[index]            # Access buffer at referenced address
                call = parse_arg(inst)          # Parse instruction word
                try:
                    word = 0x3FFFFFF            # Define 25-bit extractor
                    arg  = int(inst, 16) & word # Extract 25-bit buffer
                    cmd, jmp = call(arg)        # Call function with args
                    index += __counter(jmp)     # Goes to new address in memory
                    __write(cmd)                # Write result to the bus
                    __loadreg(int(inst, 16))    # Load current instruction to IR
                except TypeError:
                    __badinstr()
            __interrupt()
    except IndexError as ex:
        print(ex)
        print('[Errno ?] Output file not provided')

def parse_arg(content):
    global struct
    signal = int(content, 0x10)   # Convert buffer content to uint64
    op = hex(signal >> 26 & 0x7F) # Get the first 6-bits of the instruction
    try:
        return struct[op]         # Return callable operation
    except KeyError:
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
