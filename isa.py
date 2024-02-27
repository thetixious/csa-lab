from __future__ import annotations
import json

from enum import Enum


class Opcode(str,Enum):
    LD: str = "LD"
    ADD: str = "ADD"
    SUB: str = "SUB"
    ST: str = "ST"
    DEC: str = "DEC"
    INC: str = "INC"
    PUSH: str = "PUSH"
    POP: str = "POP"
    CALL: str = "CALL"
    RET: str = "RET"
    DIV: str = "DIV"
    MUL: str = "MUL"
    MOD: str = "MOD"
    EQ: str = "EQ"
    GT: str = "GT"
    LT: str = "LT"
    IN: str = "IN"
    OUT: str = "OUT"
    JMP: str = "JMP"
    JZ: str = "JZ"
    JNZ: str = "JNZ"
    JG: str = "JG"
    HLT: str = "HLT"
    CMP: str = "CMP"
    NOP: str = "NOP"

    def __str__(self) -> str:
        return str(self.value)


branch_commands: str = [Opcode.JZ, Opcode.JNZ, Opcode.JMP]
non_operand_commands: str = [Opcode.INC, Opcode.DEC, Opcode.HLT, Opcode.POP, Opcode.PUSH]
operand_commands: str = [Opcode.ADD, Opcode.IN, Opcode.OUT, Opcode.CALL, Opcode.CMP]


def get_opcode(str_opcode) -> Opcode:
    return {

        "ld": Opcode.LD,
        "add": Opcode.ADD,
        "sub": Opcode.SUB,
        "st": Opcode.ST,
        "dec": Opcode.DEC,
        "inc": Opcode.INC,
        "push": Opcode.PUSH,
        "pop": Opcode.POP,
        "call": Opcode.CALL,
        "ret": Opcode.RET,
        "div": Opcode.DIV,
        "mul": Opcode.MUL,
        "mod": Opcode.MOD,
        "eq": Opcode.EQ,
        "gt": Opcode.GT,
        "lt": Opcode.LT,
        "in": Opcode.IN,
        "out": Opcode.OUT,
        "jmp": Opcode.JMP,
        "jz": Opcode.JZ,
        "jg": Opcode.JG,

        "jnz": Opcode.JNZ,
        "hlt": Opcode.HLT,
        "cmp": Opcode.CMP,
        "nop": Opcode.NOP

    }.get(str_opcode, Opcode.NOP)


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            print(instr)
            buf.append(json.dumps(instr))
        file.write("[" + ",\n".join(buf) + "]")


def read_code(filename):
    with open(filename, "r", encoding="utf-8") as file:
        code = json.loads(file.read())
    return code
