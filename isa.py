from __future__ import annotations

from enum import Enum


class Opcode(Enum):
    LD: str = "LD"
    ADD: str = "ADD"
    SUB: str = "SUB"
    LD: str = "LD"
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
    HLT: str = "HLT"

    def __str__(self) -> str:
        return self.value

