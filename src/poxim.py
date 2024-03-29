"""
Copyright (c) 2021 Saulo G. Felix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
import struct
import math
import random

# General purpose registers
# CR -> R[26], IPC -> R[27], IR -> R[28], PC -> R[29], SP -> R[30], SR -> R[31]

R = [uint32 * 0 for uint32 in range(32)] # General purpose registers
X = { 'value' : 0, 'type' : float } # FPU X register
Y = { 'value' : 0, 'type' : float } # FPU Y register
Z = { 'value' : 0, 'type' : float } # FPU Z register
CTR = 0 # FPU control multiplexer device
WDG = 1 # Watchdog flag
MEM = 0 # Memory device
DEV = 0 # Device index register
HDT = 3 # Type of hardware interruption. Default HW constant time (code 3)
CNT = 0x7FFFFFFF # Default value for the wawtchdog counter
INT_QUEUE = []   # Interruption queue
FPU_OP  = 0  # FPU operation flag
FPU_ERR = 0  # FPU error flag
FPU_INT = 0  # Initialize fpu interruption cycle counter
INT_ADR = 0  # Keeps track of generated interruption instruction
TRM_OUT = [] # Terminal output buffer
TRM_IN  = [] # Terminai input buffer

def mov(args):
    global R
    z    = args >> 21 & 0x1F
    R[z] = args >>  0 & 0x1FFFFF if z != 0 else 0x0
    ins  = 'mov {},{}'.format(__r(z), R[z]).ljust(25)
    cmd  = '{}:\t{}\t{}={}'.format(__hex(__pc()), ins, __r(z).upper(), __hex(R[z]))
    __incaddr()
    return cmd, 0

def add(args):
    global R
    (x, y, z) = __get_index(args)
    R[z] = R[x] + R[y] if z != 0 else R[z]
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
    l = args >> 0 & 0x1F
    B = R[x] * R[y]
    R[l] = B >> 32 & 0xFFFFFFFF if l != 0 else 0x0
    R[z] = B >> 0  & 0xFFFFFFFF if z != 0 else 0x0
    A = R[l] << 32 | R[z]
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
    B = (R[z] << 32 | R[x]) << (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 32 | R[x])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x01 if R[z] != 0 else R[31] & ~(1<<0x00)
    ins = 'sll {},{},{},{}'.format(__r(z), __r(x), __r(y), l).ljust(25)
    res = '{}:{}={}:{}<<{}={}'.format(__r(z, True), __r(x, True), __r(z, True), __r(y, True), l+1, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()),ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def muls(args):
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = __twos_comp(R[x]) * __twos_comp(R[y])
    R[l] = B >> 32 & 0xFFFFFFFF if l != 0 else 0x0
    R[z] = B >> 0  & 0xFFFFFFFF if z != 0 else 0x0
    A = (R[l] << 32 | R[z])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[l] != 0 else R[31] & ~(1<<0x03)
    ins = 'muls {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = '{}:{}={}*{}={}'.format(__r(l,True), __r(z,True), __r(x,True), __r(y,True), __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def sla(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (R[z] << 32 | R[x]) << (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 32 | R[x])
    R[31] = R[31] | 0x40 if A    == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[z] != 0 else R[31] & ~(1<<0x03)
    ins = 'sla {},{},{},{}'.format(__r(z), __r(x), __r(x), l).ljust(25)
    res = '{}:{}={}:{}<<{}={}'.format(__r(z, True), __r(x, True), __r(z, True), __r(y, True), l+1, __hex(A, 18))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()),ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def div(args):
    (x, y, z) = __get_index(args)
    sw_int = False
    l = args >> 0  & 0x1F
    jmp = 0
    msg = None
    PC = R[29]

    try:
        R[l] = R[x] %  R[y] if l != 0 else 0
        R[z] = R[x] // R[y] if z != 0 else 0
        R[31] = R[31] | 0x01 if R[l] != 0 else R[31] & ~(1<<0x00)
        __incaddr()
    except ZeroDivisionError:
        R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
        if (R[31] >> 1 & 0x1) == 1:
            __save_context()
            msg = '\n[SOFTWARE INTERRUPTION]'
            sw_int = True
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1
        else:
            __incaddr()

    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    ins = 'div {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, __hex(R[l]),z, x, y,__hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(PC), ins, res, __hex(R[31]))
    if sw_int: cmd += msg
    return cmd, jmp

def srl(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (R[z] << 32 | R[x]) >> (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 32 | R[x])
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
    msg = None
    PC = R[29]

    try:
        R[l] = __twos_comp(R[x])  % __twos_comp(R[y]) if l != 0 else 0
        R[z] = __twos_comp(R[x]) // __twos_comp(R[y]) if z != 0 else 0
        R[l] = R[l] + 2 ** 32 if R[l] < 0 else R[l]
        R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1<<0x06)
        R[31] = R[31] | 0x08 if R[l] != 0 else R[31] & ~(1<<0x03)
        __incaddr()
    except ZeroDivisionError:
        if (R[31] >> 1 & 0x1) == 1:
            __save_context()
            msg = '\n[SOFTWARE INTERRUPTION]'
            sw_int = True
            PC = R[29]
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1
        else:
            __incaddr()

    R[31] = R[31] | 0x20 if R[y] == 0 else R[31] & ~(1<<0x05)
    ins = 'divs {},{},{},{}'.format(__r(l), __r(z), __r(x), __r(y)).ljust(25)
    res = 'R{}=R{}%R{}={},R{}=R{}/R{}={}'.format(l, x, y, __hex(R[l]),z, x, y,__hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(PC), ins, res, __hex(R[31]))
    if sw_int: cmd += msg
    return cmd, jmp

def sra(args):
    global R
    (x, y, z) = __get_index(args)
    l = args >> 0  & 0x1F
    B = (__twos_comp(R[z]) << 32 | (R[y])) >> (l+1)
    R[z] = B >> 32 & 0xFFFFFFFF if z != 0 else 0x0
    R[x] = B >> 0  & 0xFFFFFFFF if x != 0 else 0x0
    A = (R[z] << 32 | R[x])
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
    res = '{}={}&{}={}'.format(__r(z, True), __r(x, True), __r(y, True), __hex(R[z]))
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
    res = '{}={}|{}={}'.format(__r(z, True), __r(x, True), __r(y, True), __hex(R[z]))
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
    res = '{}=~{}={}'.format(__r(z, True), __r(x, True), __hex(R[z]))
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
    res = '{}={}^{}={}'.format(__r(z, True), __r(x, True), __r(y, True), __hex(R[z]))
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
    R[31] = R[31] | 0x40 if R[z] & 0xFFFFFFFF == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x10 if Rz31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 == l15) and (Rz31 != Rx31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 else R[31] & ~(1<<0x00)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'addi {},{},{}'.format(__r(z), __r(x), l).ljust(25)
    res = '{}={}+{}={}'.format(__r(z, True), __r(x, True), __hex(l), __hex(R[z]))
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
    R[31] = R[31] | 0x10 if Rz31  == 1 else R[31] & ~(1<<0x04)
    R[31] = R[31] | 0x08 if (Rx31 != l15) and (Rz31 != Rx31) else R[31] & ~(1<<0x03)
    R[31] = R[31] | 0x01 if R[z] >> 32 & 0x1 == 1 else R[31] & ~(1<<0x00)
    R[z]  = R[z] & 0xFFFFFFFF if z != 0 else 0x0
    ins = 'subi {},{},{}'.format(__r(z), __r(x), __twos_comp(l, 32)).ljust(25)
    res = '{}={}-{}={}'.format(__r(z, True), __r(x, True), __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(__pc()), ins, res, __hex(R[31]))
    __incaddr()
    return cmd, 0

def muli(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    R[z] = __twos_comp(R[x]) * __twos_comp(l) if z != 0 else 0x0
    R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
    R[31] = R[31] | 0x08 if R[z] >> 32 & 0xFFFFFFFF != 0 else R[31] & ~(1<<0x03)
    R[z] = R[z] + 2 ** 32 if R[z] < 0 and z != 0 else R[z]
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
    msg = None
    PC = R[29]
    if l != 0:
        R[z] = int(__twos_comp(R[x]) / __twos_comp(l)) if z != 0 else 0x0
        R[z] = R[z] + 2 ** 32 if R[z] < 0 and z != 0 else R[z]
        R[31] = R[31] | 0x40 if R[z] == 0 else R[31] & ~(1 << 0x06)
        __incaddr()
    else:
        if (R[31] >> 1 & 0x1) == 1:
            __save_context()
            msg = '\n[SOFTWARE INTERRUPTION]'
            sw_int = True
            PC = R[29]
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1
        else:
            __incaddr()

    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    ins = 'divi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = '{}={}/{}={}'.format(__r(z, True), __r(x, True), __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(PC), ins, res, __hex(R[31]))
    if sw_int: cmd += msg
    return cmd, jmp

def modi(args):
    global R
    (x, _, z) = __get_index(args)
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    jmp = 0
    sw_int = False
    msg = None
    PC = R[29]
    try:
        signrx = math.copysign(1, __twos_comp(R[x]))
        signl = math.copysign(1, __twos_comp(l))
        reg = 0x0
        if signl == signrx:
            if signl < 0 and signrx < 0:
                reg = math.remainder(R[x], l) if z != 0 else R[z]
            else:
                reg = R[x] % l
        elif signl < 0:
            reg = math.remainder(R[x], __twos_comp(l)) if z != 0 else R[z]
        elif signrx < 0:
            reg = math.remainder(__twos_comp(R[x]), l) if z != 0 else R[z]
            
        R[z] = int(reg) + 2 ** 32 & 0xFFFFFFFF if z != 0 else R[z]
        R[31] = R[31] | 0x40 if R[z]  == 0 else R[31] & ~(1<<0x06)
        R[31] &= ~(1<<0x03)
        __incaddr()
    except ZeroDivisionError:
        R[z] = 0x0
        if (R[31] >> 1 & 0x1) == 1:
            __save_context()
            msg = '\n[SOFTWARE INTERRUPTION]'
            sw_int = True
            PC = R[29]
            R[27] = R[29]
            R[26] = 0
            R[29] = 0x8
            jmp = ((R[29] - PC) // 4) - 1
        else:
            __incaddr()
    except Exception:
        __stdout('[Error ?] Can not resolve for library imports')
    R[31] = R[31] | 0x20 if args >> 0 & 0xFFFF == 0 else R[31] & ~(1<<0x05)
    ins = 'modi {},{},{}'.format(__r(z), __r(x), __twos_comp(l)).ljust(25)
    res = '{}={}%{}={}'.format(__r(z, True), __r(x, True), __hex(l), __hex(R[z]))
    cmd = '{}:\t{}\t{},SR={}'.format(__hex(PC), ins, res, __hex(R[31]))
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
    R[z] = __read(address) >> 24 - (address % 4) * 8 & 0xFF if z != 0 else 0x0
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
    R[z] = __read(address) >> 16 - (address % 4) * 8 & 0xFFFF if z != 0 else 0x0
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
    res = '{}=MEM[{}]={}'.format(__r(z, True), __hex(address), __hex(R[z]))
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
    res = 'MEM[{}]={}={}'.format(__hex(address), __r(z, True), __hex(R[z] & 0xFF, 4))
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
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
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
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    CY = R[31] >> 0 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 0 and CY == 0:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bat {}'.format(__twos_comp(reg)).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bbe(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    CY = R[31] >> 0 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 1 or CY == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bbe {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bbt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    CY = R[31] >> 0 & 0x1
    if CY == 1:
        jmp = reg
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bbt {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def beq(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    ZN = R[31] >> 6 & 0x1
    if ZN == 1:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'beq {}'.format(__twos_comp(reg)).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bge(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    if SN == OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bge {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bgt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 0 and SN == OV:
        __stdout('[Debug: Branching over condition {A > B}]')
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    reg = __twos_comp(reg) if reg < 0 else reg
    ins = 'bgt {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def biv(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    IV = R[31] >> 2 & 0x1
    PC = R[29]
    jmp = 0
    if IV == 1:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'biv {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def ble(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    ZN = R[31] >> 6 & 0x1
    if ZN == 1 or SN != OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    reg = __twos_comp(reg) if reg < 0 else reg
    ins = 'ble {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def blt(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC  = R[29]
    SN = R[31] >> 4 & 0x1
    OV = R[31] >> 3 & 0x1
    if SN != OV:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    else:
        __incaddr()

    ins = 'blt {}'.format(__twos_comp(reg)).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bne(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = 0
    PC = R[29]
    ZN = R[31] >> 6 & 0x1
    if ZN == 0:
        jmp = __twos_comp(reg)
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bne {}'.format(__twos_comp(reg)).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bni(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    IV = R[31] >> 2 & 0x1
    PC = R[29]
    jmp = 0
    if IV == 0:
        jmp = reg
        R[29] = R[29] + 4 + (reg << 2) & 0xFFFFFFFF
    else:
        __incaddr()
    ins = 'bni {}'.format(reg).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(__hex(PC), ins, __hex(R[29]))
    return cmd, jmp

def bnz(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
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
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
    jmp = __twos_comp(reg)
    R[29] = R[29] + 4 + (jmp << 2) & 0xFFFFFFFF
    ins = 'bun {}'.format(jmp).ljust(25)
    cmd = '{}:\t{}\tPC={}'.format(addr, ins, __hex(R[29]))
    return cmd, jmp

def bzd(args):
    global R
    reg = ((args >> 25 & 0x1) * 0x3F << 26 | args >> 0 & 0x3FFFFFF) & 0xFFFFFFFF
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
    l = args >> 0 & 0x7FF
    reg = ((args >> 20 & 0x1) * 0x7FF << 21 | x << 16 | y << 11 | l) & 0xFFFFFFFF
    R[z] = reg if z != 0 else R[z]
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
        ins = 'int {}'.format(l).ljust(25)
        res = '{}={},{}={}'.format(__r(26, True), __hex(R[26]), __r(29, True), __hex(R[29]))
        cmd = '{}:\t{}\t{}'.format(__hex(PC), ins, res) + '\n[SOFTWARE INTERRUPTION]'
        jmp = (R[29] - PC) // 4
        return cmd, jmp - 1

def __subcall(args):
    global R
    x = args >> 16 & 0x1F
    op = args >> 26 & 0x3F
    l = ((args >> 15 & 0x1) * 0xFFFF << 16 | args >> 0 & 0xFFFF) & 0xFFFFFFFF
    PC = R[29]
    SP = R[30]
    ins = None
    jmp = 0
    __overwrite(SP, 4, PC+4)
    R[30] = R[30] - 4
    if op == 0x1E:
        reg = __twos_comp(l) + R[x]
        R[29] = reg << 2 & 0xFFFFFFFF
        jmp = (R[29]-PC) // 4 - 1
        ins = 'call [{}+{}]'.format(__r(x), l).ljust(25)
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
    v = args >> 6 & 0x1F
    w = args >> 0 & 0x1F
    SP = R[30]
    ins = 'push '
    res = ''
    string = ''
    __stdout('[Debug: Stack pointer (SP) = [{}]]'.format(__hex(SP)))
    for chunk in [v, w, x, y, z]:
        if chunk != 0:
            __overwrite(R[30], 4, R[chunk])
            R[30] = R[30] - 4
            res += '{},'.format(__hex(R[chunk]))
            string += '{},'.format(__r(chunk))
        else:
            if v == 0:
                ins = 'push -'.ljust(25)
                cmd = '{}:\t{}\tMEM[{}]{{}}={{}}'.format(__hex(R[29]), ins, __hex(SP))
                __incaddr()
                return cmd, 0
            break
    fields = string.rstrip(',')
    res = 'MEM[{}]{{'.format(__hex(SP)) + res.rstrip(',') + ('}={') + fields.upper() + '}'
    ins = (ins + fields).ljust(25)
    cmd = '{}:\t{}\t{}'.format(__hex(R[29]), ins, res)
    __incaddr()
    return cmd, 0

def pop(args):
    global R
    (x, y, z) = __get_index(args)
    v = args >> 6 & 0x1F
    w = args >> 0 & 0x1F
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
                ins = 'pop -'.ljust(25)
                cmd = '{}:\t{}\t{{}}=MEM[{}]{{}}'.format(__hex(__pc()), ins, __hex(R[30]))
                __incaddr()
                return cmd, 0
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
    x, _, z = __get_index(args)
    R[z] &= ~(1<<x) if z != 0 else R[z]
    ins = 'cbr {}[{}]'.format(__r(z), x).ljust(25)
    cmd = '{}:\t{}\t{}={}'.format(__hex(__pc()), ins, __r(z, True), __hex(R[z]))
    __incaddr()
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

def __hex(string, length=10):
    return '{0:#0{1}X}'.format(string, length).replace('X','x')

def debug_mode(args):
    global debug
    if '--debug' in args:
        debug = True

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
    
def __stdout(output, end='\n'):
    if debug:
        print(output, end=end)

def __read_stdin(args):
    global TRM_OUT
    if '--stdin' in args:
        fileinput = []
        index = args.index('--stdin') + 1
        try:
            with open(args[index], 'rb') as f:
                while (byte := f.read(1)):
                    fileinput.append(byte)
            __stdout('[Debug: Read from standard input (STDIN)]')
        except FileNotFoundError:
            return
        TRM_IN.append(fileinput)

def __get_stdinbyte():
    global TRM_IN
    if TRM_IN:
        try:
            byte = int.from_bytes(TRM_IN[0].pop(0), "big") & 0xFF
            return byte             
        except IndexError:
            __interrupt(0)
        except TypeError:
            TRM_IN.pop(0)

def __randint():
    import random
    num = random.randint(0, 0xFF)
    return num
    
def __nop():
    pass # Nothing to do here...

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
        __stdout('[Errno ?] Error trying to start program')

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
    global MEM, DEV
    index = address // 4
    bias = ((24-size*8) - (address % 4) * 8)+8 if size != 4 else 0
    mask = {1: 0xFF, 2: 0xFFFF, 3:0xFFFF, 4: 0xFFFFFFFF}
    
    try:
        buffer = int(MEM[index], 16)
    except:
        buffer = 0x0

    # Device multiplexer. Interchange between devices attached to the bus
    # Terminal : address -> 0x88888888
    # Watchdog : address -> 0x80808080
    # Memory   : address -> 0x00000000 : 0x00007FFC
    # FPU      : address -> 0x80808880 : 0x8080888C
    if index <= 0x7FFC:
        old = MEM[index]
        MEM[index] = __hex((buffer & ~(mask[size]<<bias) | (content & mask[size])<<bias) & mask[4])
        msg = '[Debug: Written to memory {} @ {} '.format(__hex(content), __hex(address))
        __stdout(msg + '=> {{{} -> {}}}]'.format(old, MEM[index], bias))
    else:
        devices = { '0x80808080' : __watchdog, '0x20202020' : __watchdog }
        for i in range(0x88888888 >> 2, 0x8888888C >> 2): devices[hex(i)] = __terminal
        for i in range(0x80808880 >> 2, 0x80808890 >> 2): devices[hex(i)] = __fpu
        for i in range(0x88888888, 0x8888888D): devices[hex(i)] = __terminal
        for i in range(0x80808880, 0x80808890): devices[hex(i)] = __fpu
        try:
            DEV = __align(address) # Store pointer that points at the device being accessed
            devices[hex(DEV)](content)
        except IndexError as ex:
            __stdout(ex)

def __read(address=None):
    global MEM
    if address is not None:
        index = address // 4
        if index <= 0x7FFC:
            res = int(MEM[index], 16)
            __stdout('[Debug: Read from memory [{}] @ {}]'.format(__hex(res), __hex(address)))
            return int(MEM[index], 16)
        else:
            random_generator = random.randint(0, 0xFF) << 8
            reg = { '0x8888888a' : random_generator, '0x8888888c' : random_generator }
            for index in range(0x80808880, 0x80808884): reg[hex(index)] = X['value']
            for index in range(0x80808884, 0x80808888): reg[hex(index)] = Y['value']
            for index in range(0x80808888, 0x8080888C): reg[hex(index)] = Z['value']
            for index in range(0x8080888C, 0x80808890): reg[hex(index)] = CTR
            return reg[hex(address)]
    else:
        return MEM

def __load_program(prog):
    global MEM
    MEM = prog
    word_count = 0
    for byte in range(0x7FFC - len(prog)):
        MEM.append(__hex(0))
    for element in MEM:
        if element != '0x00000000':
            word_count += 1
    __stdout('[Debug: Program loaded {} bytes into memory]'.format(word_count*4))

def __init(line):
    global bus
    bus = line

def __termout():
    if TRM_OUT:
        __write('[TERMINAL]')
        __write(''.join([chr(i) for i in TRM_OUT]))

def __align(address):
    if address in range(0x88888888 >> 2, 0x8888888F >> 2): address <<= 2
    elif address in range(0x80808880 >> 2, 0x80808890 >> 2): address <<= 2
    elif address == 0x20202020: address <<= 2
    return address

def goto_intr(code):
    global R
    # Jump to interruption address.
    # HW1 : code == 1 -> address => 0x00000010
    # HW2 : code == 2 -> address => 0x00000014    
    # HW3 : code == 3 -> address => 0x00000018
    # HW4 : code == 4 -> address => 0x0000001C
    address = 0xC + 4*code    # Begins at 0x10 (code >= 1)
    PC  = R[29]               # Save current address
    jmp = (address - PC) // 4 # Branch 'jmp' adresses
    R[29] = address           # Update program counter with new address
    __stdout('[Debug: Branching @ {} -> {}]'.format(__hex(PC), __hex(R[29])))
    return jmp

def goto(arg, irs=0):
    if arg == 0 or arg is None:
        return 1
    else:
        return arg + 1

def __write(line, end='\n'):
    global bus
    if line is not None:
        try:
            __stdout(line, end=end)
            bus.write(line)
            bus.write(end)
        except FileNotFoundError:
            __stdout('[Errno ?] Not possible to access bus')
        except TypeError:
            pass

def __terminal(content):
    global R, DEV, TRM_OUT, TRM_IN
    if DEV == 0x8888888B:
        TRM_OUT.append(content & 0xFF)
    elif DEV == 0x8888888A:
        TRM_IN.append(content & 0xFF)
        
def __watchdog(content):
    global WDG, DEV, CNT
    DEV = 0x80808080
    CNT = content & 0x7FFFFFFF
    WDG = content >> 31 & 0x1

def __fpu(content):
    global R, X, Y, Z, CTR, DEV, FPU_INT, FPU_OP, FPU_ERR, HDT
    
    address = DEV
    operation = {
        0 : __nop,
        1 : __sum,
        2 : __sub,
        3 : __mul,
        4 : __div,
        5 : '__atx',
        6 : '__aty',
        7 : __ceil,
        8 : __floor,
        9 : __round 
    }
    
    if address in range(0x80808880, 0x80808884):
        X = { 'value' : content, 'type' : int }
        __stdout('[Debug: Content of X = [{}]'.format(__hex(X['value'])))
    elif address in range(0x80808884, 0x80808888):  
        Y = { 'value' : content, 'type' : int }
        __stdout('[Debug: Content of Y = [{}]'.format(__hex(Y['value'])))
    elif address in range(0x80808888, 0x8080888C):
        Z = { 'value' : content, 'type' : int }
        __stdout('[Debug: Content of Z = [{}]'.format(__hex(Z['value'])))
    elif address in range(0x8080888C, 0x80808890):
        CTR = content & 0x1F
        FPU_OP = CTR >> 0x0 & 0x1F
        FPU_INT = 1
        
        try:
            __stdout('[Debug: FPU processing. Operation [{}]]'.format(operation[FPU_OP].__name__))
        except:
            __stdout('[Debug: Warning. Invalig operation]')

        __stdout('[Debug: CTR [{}] @ [{}]'.format(__hex(CTR), __hex(DEV)))
        if FPU_OP == 0:
            operation[0]()
        elif FPU_OP == 5:
            X = Z.copy()
            HDT = 4
        elif FPU_OP == 6:
            Y = Z.copy()
            HDT = 4
        elif FPU_OP in [7, 8, 9]:
            try:
                z = Z['value'] if Z['type'] is float else __ieee754(float(Z['value']))
            except Exception:
                __stdout('[Debug: Warning. FPU ZeroDivision exception]')
                z = 0        
            Z = operation[FPU_OP](z)
            __stdout('[Debug: Content of Z = [{}]]'.format(__hex(Z['value'])))
            HDT = 4
        elif FPU_OP in range(10):
            try:     
                x = X['value'] if X['type'] is float else __ieee754(float(X['value']))
                y = Y['value'] if Y['type'] is float else __ieee754(float(Y['value']))
            except Exception:
                x = 0
                y = 0
            Z, error_code = operation[FPU_OP](hex2float(x), hex2float(y))
            exp_x = x >> 23 & 0xFF
            exp_y = y >> 23 & 0xFF
            FPU_INT = abs(exp_x - exp_y) + 1
            FPU_ERR = error_code
            HDT = 2 if FPU_ERR == 1 else 3
            __stdout('[Debug: Content of Z = [{}]]'.format(__hex(Z['value'])))
        else:
            HDT = 2
            FPU_ERR = 1
            FPU_INT = 1
            __stdout('[Debug: FPU invalid operation code [{}]]'.format(hex(FPU_OP)))

def __sum(x, y):
    res = {'value': __ieee754(x + y), 'type' : float}
    return (res, 0)

def __sub(x, y):
    res = {'value': __ieee754(x - y), 'type': float}
    return (res, 0)

def __mul(x, y):
    res = {'value': __ieee754(x * y), 'type': float}
    return (res, 0)

def __div(x, y):
    res = Z
    if y != 0:
        res['value'] = __ieee754(x / y)
        return (res, 0)
    else:
        return (res, 1)

def __ceil(z):
    res = math.ceil(hex2float(z))
    return {'value' : res, 'type' : int}

def __floor(z):
    res = math.floor(hex2float(z))
    return {'value' : res, 'type' : int}

def __round(z):
    res = round(hex2float(z))
    return {'value' : res, 'type' : int}

def __ieee754(value):
    return struct.unpack('I', struct.pack('f', value))[0]

def __store_address():
    global INT_ADR
    INT_ADR = R[29]

def __countdown():
    global WDG, CNT, R
    if WDG == 1:                  # Watchdog enabled
        if CNT > 1: 
            CNT -= 1              # Decrement counter
        else: 
            CNT = 0x7FFFFFFF      # Reset counter
            WDG = 0               # Disable watchdog
    else:
        if R[31] >> 1 & 0x1 == 1:
            __save_context(jmp=-4)
            R[27] = R[29]         # Store interruption address
            R[26] = 0xE1AC04DA    # Store interruption code
            WDG = 1               # Disable watchdog
            __add2queue(1)        # Add interruption to queue

def __add2queue(code):
    global INT_QUEUE
    INT_QUEUE.append(code)

def __int_query():
    global INT_QUEUE
    if INT_QUEUE:
        inter = INT_QUEUE.pop(0)
        return __interrupt(inter)
    else:
        return 0

def __fpu_query():
    global R, FPU_INT, FPU_OP, CTR
    if FPU_OP != 0:
        if FPU_INT > 0:
            FPU_INT -= 1
            __stdout('[Debug: FPU duty cycle :: {}]'.format(FPU_INT))
        else:
            __save_context(jmp=-4)
            R[26] = 0x01EEE754
            R[27] = INT_ADR
            FPU_OP = 0
            CTR &= ~(0x1F)
            CTR |= 0x20 if FPU_ERR == 1 else CTR
            __add2queue(HDT)

def __interrupt(pr=0):
    global R
    if pr == 0:
        msg = '[END OF SIMULATION]'
        try:
            __termout()
            __write(msg)
            sys.exit()
        except Exception:
            __stdout('[Errno ?] Exit with status error')
    else:
        msg = '[HARDWARE INTERRUPTION {}]'.format(pr)
        if pr in [1, 2, 3, 4]:
            __write(msg)
            return pr
        else:
            return 0
        
def __save_context(jmp=0):
    global R
    for index in (29, 26, 27):
        content = R[index] if index != 29 else R[29] + 4 + jmp
        __overwrite(R[30], 4, content)
        R[30] -= 4

def hex2float(value):
    value = int(value, 16) if isinstance(value, str) else value
    return struct.unpack(">f", struct.pack(">i", value))[0]

def main(args):
    try:
        debug_mode(args)
        file = sys.argv[1]
        with open(file, 'r') as bus:
            buffer = bus.read().splitlines()
    except FileNotFoundError as exception:
        __stdout(exception)
        sys.exit()

    try:
        output = sys.argv[2]
    except IndexError:
        output = '/dev/null'
        __stdout('[Debug: Output file not provided, redirecting to /dev/null instead]')

    index = 0
    irs = 0
    arg = __hex(0)
    with open(output, 'w') as bus:
        __init(bus)            # Start bus, if file name provided
        __read_stdin(args)
        __load_program(buffer) # Load program into virtual memory
        __begin()              # Write starting sentence
        while True:
            try:
                inst = buffer[index]        # Access buffer at referenced address
                call = parse_arg(inst)      # Parse instruction word
                __fpu_query()               # FPU cycle interruption verification
                word = 0xFFFFFFFF           # Define 32-bit extractor
                arg  = int(inst, 16) & word # Extract 32-bit buffer
                __loadreg(arg)              # Load current instruction to IR
                irs  = __int_query()        # Iterruption manager
                if irs != 0:
                    index += goto_intr(irs) # In case interruption happens, computes new address
                else:
                    __store_address()
                    cmd, jmp = call(arg)    # Call function with args
                    index += goto(jmp)      # Goes to new address in memory
                    __countdown()           # Update watchdog countdown
                    __write(cmd)            # Write result to the bus
            except TypeError:
                __badinstr(arg)
            except IndexError as ex2:
                __stdout(ex2)
                __stdout('[Error: Probably tried to access buffer at invalid location]')
                __interrupt()
            except Exception as ex1:
                __stdout(ex1)
                __interrupt()

def parse_arg(content):
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
    
    try:
        signal = int(content, 16)     # Convert buffer content to uint64
        op = hex(signal >> 26 & 0x3F) # Get the first 6-bits of the instruction
        return struct[op]             # Return callable operation
    except KeyError:
        return __badinstr             # Instruction not listed as valid operation
    except ValueError as ex:
        __stdout('[Debug: Error while trying to parse arguments]')

if __name__ == '__main__':
    debug = True
    bus   = None
    main(sys.argv)
