import sys

# Define general purpose registers
# CR -> R[26], IPC -> R[27], IR -> R[28], PC -> R[29], SP -> R[30], SR -> R[31]
R   = [uint32 * 0 for uint32 in range(32)]
MEM = 0
PC  = 0

def mov(args):
    global R
    if args != 0:
        z    = args >> 21 & 0x1F
        R[z] = args >>  0 & 0x1FFFFF if z != 0 else 0x0
        ins  = 'mov {},{}'.format(__r(z), R[z]).ljust(25)
        cmd  = '{}:\t{}\t{}={}'.format(__hex(__pc()), ins, __r(z).upper(), __hex(R[z]))
        __incaddr()
        return cmd, 0
    else:
        return __nop(), 0

def add(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] + R[y] & 0xFFFFFFFF if z != 0 else R[z]
    Rx31 = R[x] >> 31 & 0x1
    Ry31 = R[y] >> 31 & 0x1
    Rz31 = R[z] >> 31 & 0x1
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if Rx31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 == Ry31) and (Rx31 != Rz31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 else R[31] & ~(1<<0x00)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else R[z]
    ins = 'add {},{},{}'.format(__r(z), __r(x), __r(y)).ljust(25)
    res = '{}={}+{}={}'.format(__r(z, True), __r(x, True), __r(y, True), __hex(R[z]))
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
    sw_int = False
    l = args >> 0  & 0x1F
    jmp = 0

    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
        __incaddr()
    except ZeroDivisionError:
        __save_context()
        msg = '\n[SOFTWARE INTERRUPTION]'
        sw_int = True
        PC = R[29]
        if (R[31] >> 1 & 0x1) == 1:
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1

    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    R[31] = R[31] | 0x01 if R[l] != 0 else R[31] & ~(1<<0x00)
    ins = 'div {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, __hex(R[l]),z, x, y,__hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(PC), ins, res, __hex(R[31]))
    if sw_int: cmd += msg
    return cmd, jmp

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
    sw_int = False
    jmp = 0

    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
    except ZeroDivisionError:
        __save_context()
        msg = '\n[SOFTWARE INTERRUPTION]'
        sw_int = True
        PC = R[29]
        if (R[31] >> 1 & 0x1) == 1:
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1

    R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    R[31] = R[31] | 0x08 if R[l] != 0 else R[31] & ~(1<<0x03)
    ins = 'divs {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, __hex(R[l]),z, x, y,__hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    if sw_int: cmd += msg
    return cmd, jmp

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
    jmp = 0
    sw_int = False

    try:
        R[z] = R[x] // __twos_comp(l) if z != 0 else 0x0
    except ZeroDivisionError:
        __save_context()
        msg = '\n[SOFTWARE INTERRUPTION]'
        sw_int = True
        PC = R[29]
        if (R[31] >> 1 & 0x1) == 1:
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1

    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    R[31] = 0
    ins = 'divi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}/{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    if sw_int: cmd += msg
    return cmd, 0

def modi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    jmp = 0
    sw_int = False

    try:
        R[z] = R[x] % __twos_comp(l) if z != 0 else 0x0
    except ZeroDivisionError:
        R[z] = 0x0
        __save_context()
        msg = '\n[SOFTWARE INTERRUPTION]'
        sw_int = True
        PC = R[29]
        if (R[31] >> 1 & 0x1) == 1:
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1

    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    R[31] = 0
    ins = 'modi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = 'R{}=R{}%{}={}'.format(z, x, __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    if sw_int: cmd += msg
    return cmd, jmp

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
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    CY = R[31] >> 0 & 0x1
    if CY == 0:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bae {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bat(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    CY = R[31] >> 0 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 0 and CY == 0:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bat {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bbe(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    CY = R[31] >> 0 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 1 or CY == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bbe {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bbt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    CY = R[31] >> 0 & 0x1
    if CY == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bbt {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def beq(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    ZN = R[31] >> 6 & 0x1
    if ZN == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'beq {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bge(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    if SN == OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bge {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bgt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 0 and SN == OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bgt {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def biv(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    IV = R[31] >> 2 & 0x1
    PC = R[29]
    jmp = 0
    if IV == 1:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'biv {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def ble(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 1 and SN != OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'ble {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def blt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    if SN != OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'blt {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bne(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    ZN = R[31] >> 6 & 0x1
    if ZN == 0:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bne {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bni(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    IV = R[31] >> 2 & 0x1
    PC = R[29]
    jmp = 0
    if IV == 0:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        R[29] + 4
    ins = 'bni {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, reg

def bnz(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    PC = R[29]
    ZD = R[31] >> 5 & 0x1
    jmp = 0
    if ZD == 0:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bnz {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bun(args):
    global R
    addr = __hex(R[29])
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    jmp = __twos_comp(reg)
    R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    ins = 'bun {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(addr, ins, __hex(R[29]))
    return cmd, jmp

def bzd(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x1FFFFFF) & 0xFFFFFFFF
    PC = R[29]
    ZD = R[31] >> 5 & 0x1
    jmp = 0
    if ZD == 1:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bzd {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def movs(args):
    global R
    (x, y, z) = __get_index(args)
    if z != 0:
        l = args >> 0 & 0x7FF
        reg = ((args >> 20 & 0x1) * 0x7FF << 21 | x << 16 | y << 11 | l) & 0xFFFFFFFF
        R[z] = reg
    ins  = 'movs {},{}'.format(__r(z), __twos_comp(reg)).ljust(25)
    cmd  = '{}:\t{}\tR{}={}'.format(__hex(__pc()), ins, z, __hex(R[z]))
    __incaddr()
    return cmd, 0

def intx(args):
    global R
    addr  = __hex(R[29])
    l = args >> 0 & 0x3FFFFFF
    __save_context()
    
    if l == 0:
        R[29] = 0
        ins   = 'int 0'.ljust(25)
        cmd   = '{}:\t{}\tCR={},PC={}'.format(addr, ins, __hex(0), __hex(R[29]))
        __write(cmd)
        __interrupt()
    else:
        PC = R[29]
        R[26] = l
        R[27] = R[29]
        R[29] = 0xC
        ins = 'int 5'.ljust(25)
        res = '{}={},{}={}'.format(__r(26, True), __hex(R[26]), __r(29, True), __hex(R[29]))
        cmd = '{}:\t{}\t{}'.format(__hex(PC), ins, res) + '\n[SOFTWARE INTERRUPTION]'
        jmp = (R[29] - PC) // 4
        return cmd, jmp - 1

def __subcall(args):
    x = args >> 16 & 0x1F   
    op = args >> 26 & 0x3F
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    PC = R[29]
    SP = R[30]
    __overwrite(SP, 4, PC+4)
    R[30] = R[30] - 4
    if op == 0x1E:
        reg = __twos_comp(l) + R[x]
        R[29] = (reg) << 2 & 0xFFFFFFFF
        jmp = (R[29]-PC) // 4 - 1
        ins = 'call [{}+{}]'.format(__r(x), reg).ljust(25)
    elif op == 0x39:
        jmp = __twos_comp(l)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
        jmp = (R[29]-PC) // 4 - 1
        ins = 'call {}'.format(jmp).ljust(25)
    res = 'PC={},MEM[{}]={}'.format(__hex(R[29]), __hex(SP), __hex(PC+4))
    cmd = '{}:\t{}\t{}'.format(__hex(PC), ins, res)
    return cmd, jmp

def ret(args):
    global R
    R[30] = R[30] + 4
    PC = R[29]
    R[29] = __read(R[30])
    jmp = (R[29]-PC) // 4
    ins = 'ret'.ljust(25)
    res = 'PC=MEM[{}]={}'.format(__hex(R[30]), __hex(R[29]))
    cmd = '{}:\t{}\t{}'.format(__hex(PC), ins, res)
    return cmd, jmp - 1

def push(args):
    global R
    (x, y, z) = __get_index(args)
    v = args >> 6 & 0x3F
    w = args >> 0 & 0x3F
    SP = R[30]
    ins = 'push '
    res = ''
    string = ''
    for chunk in [v, w, x, y, z]:
        if chunk != 0:
            __overwrite(R[30], 2, R[chunk])
            R[30] = R[30] - 4
            res += '{},'.format(__hex(R[chunk]))
            string += '{},'.format(__r(chunk))
        else:
            if v == 0:
                cmd = '{}:\tpush -'.format(__hex(__pc())).ljust(25)
                __incaddr()
                return cmd + '\tMEM[{}]{{}}={{}}'.format(R[30])
            break

    fields = string.rstrip(',')
    res = 'MEM[{}]{{'.format(__hex(SP)) + res.rstrip(',') + ('}={') + fields.upper() + '}'
    ins = (ins + fields).ljust(25)
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def pop(args):
    global R
    (x, y, z) = __get_index(args)
    v = args >> 6 & 0x3F
    w = args >> 0 & 0x3F
    SP = R[30]
    ins = 'pop '
    res = ''
    string = ''
    for chunk in [v, w, x, y, z]:
        if chunk != 0:
            R[30] = R[30] + 4
            R[chunk] = __read(R[30])
            res += '{},'.format(__hex(R[chunk]))
            string += '{},'.format(__r(chunk))
        else:
            if v == 0:
                cmd = '{}:\pop -'.format(__hex(__pc())).ljust(25)
                __incaddr()
                return cmd + '\tMEM[{}]{{}}={{}}'.format(R[30])
            break

    fields = string.rstrip(',')
    res = '{' + fields.upper() + '}}=MEM[{}]{{'.format(__hex(SP)) + res.rstrip(',') + ('}')
    ins = (ins + fields).ljust(25)
    cmd = '{}:\t{}\t{}'.format(__hex(__pc()), ins, res)
    __incaddr()
    return cmd, 0

def reti(args):
    global R
    PC  = R[29]
    res = ''
    for index in (27, 26, 29):
        R[30] = R[30] + 4
        R[index] = __read(R[30])
        res += '{}=MEM[{}]={},'.format(__r(index, up=True), __hex(R[30]), __hex(R[index]))
    res = res.rstrip(',')
    ins = 'reti'.ljust(25)
    cmd = '{}:\t{}\t{}'.format(__hex(PC), ins, res)
    jmp = (R[29]-PC) // 4
    return cmd, jmp - 1

def cbr(args):
    _, _, z = __get_index(args)
    R[z] &= ~(1<<0x00) if z != 0 else R[z]
    cmd = ''
    return cmd

def sbr(args):
    x, _, z = __get_index(args)
    R[z] |= (1 << x) if z != 0 else R[z]
    ins = 'sbr {}[{}]'.format(__r(z), x).ljust(25)
    cmd = '{}:\t{}\t{}={}'.format(__hex(__pc()), ins, __r(z, True), __hex(R[z]))
    __incaddr()
    return cmd

def __clear_bit(args):
    l = args >> 0 & 0x1
    cmd = cbr(args) if l == 0 else sbr(args)
    return cmd, 0

def __save_context():
    global R
    for index in (29, 26, 27):
        content = R[index] if index != 29 else R[29] + 4
        __overwrite(R[30], 4, content)
        R[30] -= 4

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
        __badinstr(args)

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

def __r(reg, up=False):
    registers = {
        26 : 'cr',
        27 : 'ipc',
        28 : 'ir',
        29 : 'pc',
        30 : 'sp',
        31 : 'sr'
    }
    try:
        res = registers[reg]
    except KeyError:
        res = 'r{}'.format(reg)
    return res.upper() if up else res

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

def __interrupt(pr=0):
    global R
    if pr == 0:
        msg = '[END OF SIMULATION]'
        try:
            __write(msg)
            sys.exit()
        except Exception:
            print('[Errno ?] Exit with status error')

def __badinstr(args):
    global R
    __save_context()
    msg = '[INVALID INSTRUCTION @ {}]'.format(__hex(R[29]))
    PC = R[29]
    R[26] = args >> 26 & 0x3F
    R[27] = R[29]
    R[29] = 0x4
    R[31] |= 0x04
    cmd = msg + '\n[SOFTWARE INTERRUPTION]'
    return cmd, ((R[29] - PC) // 4) - 1

def __overwrite(address, size, content):
    global MEM
    index = address // 4
    try:
        buffer = int(MEM[index], 16)
    except:
        buffer = 0x0
    byte = {1: 0xFF, 2: 0xFFFF, 3: 0xFFFFFF, 4: 0xFFFFFFFF}
    MEM[index] = __hex(buffer & ~byte[size] | content & byte[size])

def __read(address=None):
    global MEM
    if address is not None:
        index = address // 4
        return int(MEM[index], 16)
    else:
        return MEM

def __load(prog):
    global MEM
    MEM = prog
    for byte in range(0x7FFC - len(prog)):
        MEM.append('0x0')
    print('[Debug: Loaded {} bytes into memory]'.format(len(prog)*4))

def __stack():
    global MEM
    for index, line in enumerate(MEM[::]):
        if line != '':
            if R[30] == (index - 0x7FFC) // 4:
                __stdout('-> {}'.format(line))
            else:    
                __stdout(line)

def __init(line):
    global bus
    bus = line

def __counter(arg):
    if arg == 0 or arg is None:
        return 1
    else:
        return arg + 1

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
            while True:
                inst = buffer[index]            # Access buffer at referenced address
                call = parse_arg(inst)          # Parse instruction word
                try:
                    word = 0xFFFFFFFF           # Define 32-bit extractor
                    arg  = int(inst, 16) & word # Extract 32-bit buffer
                    cmd, jmp = call(arg)        # Call function with args
                    index += __counter(jmp)     # Goes to new address in memory
                    __write(cmd)                # Write result to the bus
                    __loadreg(arg)              # Load current instruction to IR
                except TypeError:
                    __badinstr(arg)
                except Exception as ex1:
                    __stdout(ex1)
                    __interrupt()
            __interrupt()
    except IndexError as ex:
        __stdout(ex)
        __stdout('[Debug: Wrong argument]')

def parse_arg(content):
    global struct
    try:
        signal = int(content, 16)     # Convert buffer content to uint64
        op = hex(signal >> 26 & 0x3F) # Get the first 6-bits of the instruction
        return struct[op]             # Return callable operation
    except KeyError:
        return __badinstr             # Instruction not listed as valid operation
    except ValueError as ex:
        __stdout('[Debug: Error while trying to parse arguments]')

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
        '0x3f': intx,
        '0x39': __subcall,
        '0x1e': __subcall,
        '0x1f': ret,
        '0xa' : push,
        '0xb' : pop,
        '0x20': reti,
        '0x21': __clear_bit
    }

    debug = True
    bus   = None
    main(sys.argv)
