from __future__ import annotations

import json
from enum import Enum


class Opcode(str, Enum):
    AND: str = "AND"
    LD: str = "LD"
    ADD: str = "ADD"
    ST: str = "ST"
    DEC: str = "DEC"
    INC: str = "INC"
    PUSH: str = "PUSH"
    POP: str = "POP"
    IN: str = "IN"
    OUT: str = "OUT"
    JMP: str = "JMP"
    JG: str = "JG"
    JZ: str = "JZ"
    JNZ: str = "JNZ"
    HLT: str = "HLT"
    CMP: str = "CMP"
    NOP: str = "NOP"

    def __str__(self) -> str:
        return str(self.value)


branch_commands: str = [Opcode.JZ, Opcode.JNZ, Opcode.JMP, Opcode.JG]
non_operand_commands: str = [Opcode.INC, Opcode.DEC, Opcode.HLT, Opcode.POP, Opcode.PUSH]
operand_commands: str = [Opcode.ADD, Opcode.OUT, Opcode.LD, Opcode.CMP, Opcode.ST, Opcode.AND, Opcode.IN]


def get_opcode(str_opcode) -> Opcode:
    return {
        "ld": Opcode.LD,
        "add": Opcode.ADD,
        "and": Opcode.AND,
        "st": Opcode.ST,
        "dec": Opcode.DEC,
        "inc": Opcode.INC,
        "push": Opcode.PUSH,
        "pop": Opcode.POP,
        "in": Opcode.IN,
        "out": Opcode.OUT,
        "jmp": Opcode.JMP,
        "jz": Opcode.JZ,
        "jg": Opcode.JG,
        "jnz": Opcode.JNZ,
        "hlt": Opcode.HLT,
        "cmp": Opcode.CMP,
        "nop": Opcode.NOP,
    }.get(str_opcode, Opcode.NOP)


class Mux(str, Enum):
    FROM_ACC: str = "from_acc"
    FROM_DR: str = "from_dr"
    FROM_ALU: str = "from_alu"
    FROM_PC: str = "from_pc"
    FROM_SP: str = "from_sp"
    FROM_INPUT: str = "from_input"
    FROM_PS: str = "from_ps"

    def __str__(self):
        return str(self.value)


class ALUOpcode(str, Enum):
    INC_A = "inc_a"
    INC_B = "inc_b"
    DEC_A = "dec_a"
    DEC_B = "dec_b"
    ADD = "add"
    CMP = "cmp"
    AND = "and"
    NEXT_IN_A = "next_in_a"
    NEXT_IN_B = "next_in_b"

    def __str__(self) -> str:
        return str(self.value)


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n".join(buf) + "]")


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        return json.loads(file.read())
