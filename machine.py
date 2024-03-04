#!/usr/bin/python3
from __future__ import annotations
import logging
import sys
from typing import ClassVar

from isa import *


class ExitException(Exception):
    def __init__(self, opcode):
        self.message = f"In {opcode}"
        super().__init__(self.message)


class DataPath:
    acc: int = None
    alu = None
    addr: int = None
    dr: int = None
    mem = None
    mem_capacity = None
    ir = None
    sp: int = None
    pc: int = None
    ps = {}
    mr: int = None
    output_buf_num: list = None
    output_buf_sym: list = None
    input_buf: list = None

    def __init__(self, capacity:int, input_buf):
        self.alu = ALU()
        self.mem_capacity = capacity
        self.input_buf = input_buf
        self.mem = [{"opcode": Opcode.NOP.value}] * self.mem_capacity
        self.addr = 0
        self.ir = {"opcode": Opcode.NOP.value}
        self.sp = 0
        self.pc = 0
        self.ps = {"Z": self.alu.flag_z, "N": self.alu.flag_n}
        self.mr = 0
        self.acc = 0
        self.output_buf_sym = []
        self.output_buf_num = []

    def put_program_into_memory(self, program: object) -> object:
        for line in program:
            index = line["index"]
            self.mem[index] = line

    def latch_address(self):
        self.addr = self.alu.result

    def latch_mr(self):
        self.mr = self.alu.result

    def latch_instr(self):
        self.ir = self.mem[self.addr]  # add exceptions

    def latch_dr(self):
        self.dr = self.mem[self.addr]["value"]

    def latch_pc(self):
        self.pc = self.alu.result % self.mem_capacity

    def latch_sp(self):
        self.sp = self.alu.result * self.mem_capacity

    def latch_flags(self):
        self.ps["N"] = self.alu.flag_n
        self.ps["Z"] = self.alu.flag_z

    def latch_acc(self, mux: Mux):
        if mux.value == Mux.FROM_ACC:
            self.acc = self.alu.result
        elif mux.value == Mux.FROM_INPUT:
            symbol = ord(self.input_buf.pop(0)["symbol"])
            self.acc = symbol
            logging.debug(f"INPUT {repr(symbol)}")
        else:
            assert ValueError(f"Wrong mux  {mux.value}")

    def latch_output(self):
        port_type = self.dr
        # symbol
        if port_type == 0:
            print(self.acc)
            ch = chr(self.acc)
            logging.debug(f"symbols buffer: {''.join(self.output_buf_sym)} << {repr(ch)}")
            self.output_buf_sym.append(ch)
        elif port_type == 1:
            ch = self.acc
            logging.debug(f"numeric buffer: {[str(x) for x in self.output_buf_num]} << {ch}")
            self.output_buf_num.append(ch)

    def latch_wr(self):
        self.mem[self.addr] = {"index": self.addr, "opcode": Opcode.NOP.value, "value": self.mr, "is_indirect": False, }

    def alu_execution(self, op, mux_a: Mux = None, mux_b: Mux = None):
        route_a = None
        route_b = None
        if mux_a is not None:
            if mux_a == Mux.FROM_ACC:
                route_a = self.acc
            elif mux_a == Mux.FROM_PS:
                if self.ps["N"]:
                    n = 1
                else:
                    n = 0
                if self.ps["Z"]:
                    z = 1
                else:
                    z = 0
                route_a = n * 10 + z
            else:
                assert ValueError(f"Wrong left mux:  {mux_a.value}")
        if mux_b is not None:
            if mux_b == Mux.FROM_DR:
                route_b = self.dr
            elif mux_b == Mux.FROM_PC:
                route_b = self.pc
            elif mux_b == Mux.FROM_SP:
                route_b = self.sp
            else:
                assert ValueError(f"Wrong right mux:  {mux_b.value}")
        self.alu.set_alu(route_a, route_b, op)
        self.alu.calc()


class ControlUnit:
    dataPath = None
    inst_count = None
    ticks = None

    def __init__(self, dataPath: DataPath, program):
        self.dataPath = dataPath
        self.inst_count = 0
        self.ticks = 0
        dataPath.put_program_into_memory(program)

    def inc_ticks(self):
        self.ticks += 1

    def get_ticks(self):
        return self.ticks

    def instruction_fetch(self):
        self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_PC)
        self.dataPath.latch_address()
        self.inc_ticks()
        self.dataPath.alu_execution(ALUOpcode.INC_B, mux_b=Mux.FROM_PC)
        self.dataPath.latch_pc()
        self.dataPath.latch_instr()
        self.dataPath.latch_dr()
        self.inc_ticks()

    def abstract_execution(self):
        ir = self.dataPath.ir
        ps = self.dataPath.ps
        opcode = ir["opcode"]
        is_indirect = ir["is_indirect"]
        if opcode == Opcode.NOP:
            self.inc_ticks()
            return
        if is_indirect:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.latch_dr()
            self.inc_ticks()
        if opcode in operand_commands:
            self.operand_execute(opcode)
        elif opcode in non_operand_commands:
            self.non_operand_execute(opcode)
        else:
            self.branch_execute(opcode, ps)

    def non_operand_execute(self, opcode: Opcode):
        if opcode == Opcode.HLT:
            raise ExitException(Opcode.HLT)
        if opcode == Opcode.INC:
            self.dataPath.alu_execution(ALUOpcode.INC_A, mux_a=Mux.FROM_ACC)
            self.dataPath.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.DEC:
            self.dataPath.alu_execution(ALUOpcode.DEC_A, mux_a=Mux.FROM_ACC)
            self.dataPath.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.PUSH:
            self.dataPath.alu_execution(ALUOpcode.DEC_A, mux_b=Mux.FROM_SP)
            self.dataPath.latch_sp()
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_A, mux_a=Mux.FROM_ACC)
            self.dataPath.latch_mr()
            self.dataPath.latch_wr()
            self.inc_ticks()
        elif opcode == Opcode.POP:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_SP)
            self.dataPath.latch_address()
            self.inc_ticks()

            self.dataPath.alu_execution(ALUOpcode.DEC_B, mux_b=Mux.FROM_SP)
            self.dataPath.latch_dr()
            self.dataPath.latch_sp()
            self.inc_ticks()
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()

    def operand_execute(self, opcode: Opcode):
        if opcode == Opcode.ADD:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.dataPath.latch_dr()
            self.inc_ticks()
            self.dataPath.alu_execution(ALUOpcode.ADD, mux_a=Mux.FROM_ACC, mux_b=Mux.FROM_DR)
            self.dataPath.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.CMP:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.latch_dr()
            self.dataPath.alu_execution(ALUOpcode.CMP, mux_a=Mux.FROM_ACC, mux_b=Mux.FROM_DR)
            self.inc_ticks()
        elif opcode == Opcode.AND:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.latch_dr()
            self.dataPath.alu_execution(ALUOpcode.AND, mux_a=Mux.FROM_ACC, mux_b=Mux.FROM_DR)
            self.inc_ticks()
        elif opcode == Opcode.LD:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.latch_dr()
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.ST:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.latch_dr()
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_A, mux_a=Mux.FROM_ACC)
            self.dataPath.latch_mr()
            self.dataPath.latch_wr()
            self.inc_ticks()
        elif opcode == Opcode.IN:
            self.dataPath.latch_acc(Mux.FROM_INPUT)
            self.inc_ticks()
        elif opcode == Opcode.OUT:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_address()
            self.inc_ticks()
            self.dataPath.latch_dr()
            self.dataPath.latch_output()

    def branch_execute(self, opcode: Opcode, ps: dict):
        if opcode == Opcode.JMP:
            self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.dataPath.latch_pc()
            self.inc_ticks()
        elif opcode == Opcode.JZ:
            if ps["Z"]:
                self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
                self.dataPath.latch_pc()
                self.inc_ticks()
        elif opcode == Opcode.JNZ:
            if not ps["Z"]:
                self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
                self.dataPath.latch_pc()
                self.inc_ticks()
        elif opcode == Opcode.JG:
            if not ps["N"]:
                self.dataPath.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
                self.dataPath.latch_pc()
                self.inc_ticks()

    def run_fetches(self):
        self.instruction_fetch()
        self.abstract_execution()
        self.dataPath.latch_flags()
        logging.debug(self.self_shot())

    def self_shot(self) -> str:
        return "TICK: {:4} | AC {:7} | IR: {:4} | ADDR: {:4} | PC: {:3} | DR: {:7} | SP : {:4} | mem[ADDR] {:7} | ToMEM : {:3} |".format(
            self.get_ticks(),
            self.dataPath.acc,
            self.dataPath.ir["opcode"],
            self.dataPath.addr,
            self.dataPath.pc,
            self.dataPath.dr,
            self.dataPath.sp,
            self.dataPath.mem[self.dataPath.addr]["value"],
            self.dataPath.mr,
        )


class ALU:
    flag_n: ClassVar[bool] = None
    flag_z: ClassVar[bool] = None
    result: ClassVar = None
    route_a: ClassVar = None
    route_b: ClassVar = None
    alu_op: ClassVar = [
        ALUOpcode.INC_A,
        ALUOpcode.INC_B,
        ALUOpcode.DEC_A,
        ALUOpcode.DEC_B,
        ALUOpcode.ADD,
        ALUOpcode.CMP,
        ALUOpcode.AND,
        ALUOpcode.NEXT_IN_A,
        ALUOpcode.NEXT_IN_B
    ]
    operation: ClassVar[ALUOpcode] = None

    def calc(self):
        buf = None
        if self.operation == ALUOpcode.AND:
            buf = self.route_a & self.route_b
        if self.operation == ALUOpcode.INC_A:
            self.result = self.route_a + 1
        if self.operation == ALUOpcode.INC_B:
            self.result = self.route_b + 1
        if self.operation == ALUOpcode.DEC_A:
            self.result = self.route_a - 1
        if self.operation == ALUOpcode.DEC_B:
            self.result = self.route_b
        if self.operation == ALUOpcode.CMP:
            buf = self.route_a - self.route_b
        if self.operation == ALUOpcode.ADD:
            self.result = self.route_a + self.route_b
        if self.operation == ALUOpcode.NEXT_IN_A:
            self.result = self.route_a
        if self.operation == ALUOpcode.NEXT_IN_B:
            self.result = self.route_b
        else:
            assert ValueError(f"Unknown  {self.operation} operation")
        self.rise_flag(buf)

    def rise_flag(self, buf=None):
        if buf is None:
            self.flag_n = self.result < 0
            self.flag_z = self.result == 0
        else:
            self.flag_n = buf < 0
            self.flag_z = buf == 0

    def set_alu(self, path_a, path_b, operation: ALUOpcode):
        if operation not in ALUOpcode:
            assert ValueError(f"Unknown  {self.operation} operation")
        self.route_a = path_a
        self.route_b = path_b
        self.operation = operation

    def __init__(self):
        self.operation = None
        self.route_b = None
        self.route_a = None
        self.result = 0
        self.rise_flag()


def read_data(file) -> list:
    with open(file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)
    return input_token


def simulation(code: list, input_token: list, mem_capacity: int, bound: int):
    dataPath = DataPath(mem_capacity, input_token)
    control_unit = ControlUnit(dataPath, code)
    instr_counter = 0
    try:
        while instr_counter < bound:
            control_unit.run_fetches()
            instr_counter += 1
    except ExitException:
        pass

    if instr_counter > bound:
        logging.warning("Limit exceeded!")
    logging.info("symbol_buffer: %s", repr("".join(dataPath.output_buf_sym)))
    logging.info("numeric_buffer: [%s]", ", ".join(str(x) for x in dataPath.output_buf_num))
    return dataPath.output_buf_sym, dataPath.output_buf_num, instr_counter, control_unit.get_ticks()


def main(source, file):
    code = read_code(source)
    input_tokens = read_data(file)
    mem_size = 300
    bound = 5000
    symbols, nums, instr_counter, ticks_counter = simulation(code, input_tokens, mem_size, bound)

    print("".join(symbols))
    print(nums)
    print("count of instructions: ", instr_counter)
    print("count of ticks: ", ticks_counter)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
