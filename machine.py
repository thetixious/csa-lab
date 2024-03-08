#!/usr/bin/python3
from __future__ import annotations

import logging
import sys
from typing import ClassVar

from isa import ALUOpcode, Mux, Opcode, non_operand_commands, operand_commands, read_code


class ExitExceptionError(Exception):
    def __init__(self, opcode):
        self.message = f"In {opcode}"
        super().__init__(self.message)


class DataPath:
    acc: ClassVar[int] = None
    alu: ClassVar = None
    addr: ClassVar[int] = None
    dr: ClassVar[int] = None
    mem: ClassVar = None
    mem_capacity: ClassVar = None
    ir: ClassVar = None
    sp: ClassVar[int] = None
    pc: ClassVar[int] = None
    ps: ClassVar = {}
    mr: ClassVar[int] = None
    output_buf_num: ClassVar[list] = None
    output_buf_sym: ClassVar[list] = None
    input_buf: ClassVar[list] = None

    def __init__(self, capacity: int, input_buf):
        self.alu = ALU()
        self.mem_capacity = capacity
        self.input_buf = input_buf
        self.mem = [{"opcode": Opcode.NOP.value, "value": 0}] * self.mem_capacity
        self.addr = 0
        self.ir = {"opcode": Opcode.NOP.value}
        self.sp = 0
        self.pc = 0
        self.ps = {"Z": self.alu.flag_z, "N": self.alu.flag_n}
        self.mr = 0
        self.acc = 0
        self.output_buf_sym = []
        self.output_buf_num = []

    def put_program_into_memory(self, program: list):
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
            if len(self.input_buf) == 0:
                self.acc = 0
                self.alu.flag_z = True
            else:
                symbol = ord(self.input_buf.pop(0))
                self.acc = symbol
                logging.debug(f"INPUT {symbol!r}")
        else:
            assert ValueError(f"Wrong mux  {mux.value!s}")

    def latch_output(self):
        port_type = self.dr
        # symbol
        if port_type == 0:
            ch = chr(self.acc)
            logging.debug(f"symbols buffer: {''.join(self.output_buf_sym)} << {ch!r}")
            self.output_buf_sym.append(str(ch))
        elif port_type == 1:
            ch = self.acc
            logging.debug(f"numeric buffer: {[str(x) for x in self.output_buf_num]} << {ch}")
            self.output_buf_num.append(ch)

    def latch_wr(self):
        self.mem[self.addr] = {
            "index": self.addr,
            "opcode": Opcode.NOP.value,
            "value": self.mr,
            "is_indirect": False,
        }

    def alu_execution(self, op: object, mux_a: Mux = None, mux_b: Mux = None) -> object:
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
    data_path = None
    inst_count = None
    ticks = None

    def __init__(self, data_path: DataPath, program):
        self.data_path = data_path
        self.inst_count = 0
        self.ticks = 0
        data_path.put_program_into_memory(program)

    def inc_ticks(self):
        self.ticks += 1

    def get_ticks(self):
        return self.ticks

    def instruction_fetch(self):
        self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_PC)
        self.data_path.latch_address()
        self.inc_ticks()
        self.data_path.alu_execution(ALUOpcode.INC_B, mux_b=Mux.FROM_PC)
        self.data_path.latch_pc()
        self.data_path.latch_instr()
        self.data_path.latch_dr()
        self.inc_ticks()

    def abstract_execution(self):
        ir = self.data_path.ir
        ps = self.data_path.ps
        opcode = ir["opcode"]
        is_indirect = ir["is_indirect"]
        if opcode == Opcode.NOP:
            self.inc_ticks()
            return
        if is_indirect:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.latch_dr()
            self.inc_ticks()
        if opcode in operand_commands:
            self.operand_execute(opcode)
        elif opcode in non_operand_commands:
            self.non_operand_execute(opcode)
        else:
            self.branch_execute(opcode, ps)

    def non_operand_execute(self, opcode: Opcode):
        if opcode == Opcode.HLT:
            raise ExitExceptionError(Opcode.HLT)
        if opcode == Opcode.INC:
            self.data_path.alu_execution(ALUOpcode.INC_A, mux_a=Mux.FROM_ACC)
            self.data_path.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.DEC:
            self.data_path.alu_execution(ALUOpcode.DEC_A, mux_a=Mux.FROM_ACC)
            self.data_path.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.IN:
            self.data_path.latch_acc(Mux.FROM_INPUT)
            self.inc_ticks()
        elif opcode == Opcode.PUSH:
            self.data_path.alu_execution(ALUOpcode.DEC_A, mux_b=Mux.FROM_SP)
            self.data_path.latch_sp()
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_A, mux_a=Mux.FROM_ACC)
            self.data_path.latch_mr()
            self.data_path.latch_wr()
            self.inc_ticks()
        elif opcode == Opcode.POP:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_SP)
            self.data_path.latch_address()
            self.inc_ticks()

            self.data_path.alu_execution(ALUOpcode.DEC_B, mux_b=Mux.FROM_SP)
            self.data_path.latch_dr()
            self.data_path.latch_sp()
            self.inc_ticks()
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()

    def operand_execute(self, opcode: Opcode):
        if opcode == Opcode.ADD:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.data_path.latch_dr()
            self.inc_ticks()
            self.data_path.alu_execution(ALUOpcode.ADD, mux_a=Mux.FROM_ACC, mux_b=Mux.FROM_DR)
            self.data_path.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.CMP:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.latch_dr()
            self.data_path.alu_execution(ALUOpcode.CMP, mux_a=Mux.FROM_ACC, mux_b=Mux.FROM_DR)
            self.inc_ticks()
        elif opcode == Opcode.AND:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.latch_dr()
            self.data_path.alu_execution(ALUOpcode.AND, mux_a=Mux.FROM_ACC, mux_b=Mux.FROM_DR)
            self.inc_ticks()
        elif opcode == Opcode.LD:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.latch_dr()
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_acc(Mux.FROM_ACC)
            self.inc_ticks()
        elif opcode == Opcode.ST:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.latch_dr()
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_A, mux_a=Mux.FROM_ACC)
            self.data_path.latch_mr()
            self.data_path.latch_wr()
            self.inc_ticks()
        elif opcode == Opcode.OUT:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_address()
            self.inc_ticks()
            self.data_path.latch_dr()
            self.data_path.latch_output()

    def branch_execute(self, opcode: Opcode, ps: dict):
        if opcode == Opcode.JMP:
            self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
            self.data_path.latch_pc()
            self.inc_ticks()
        elif opcode == Opcode.JZ:
            if ps["Z"]:
                self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
                self.data_path.latch_pc()
                self.inc_ticks()
        elif opcode == Opcode.JNZ:
            if not ps["Z"]:
                self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
                self.data_path.latch_pc()
                self.inc_ticks()
        elif opcode == Opcode.JG:
            if not ps["N"]:
                self.data_path.alu_execution(ALUOpcode.NEXT_IN_B, mux_b=Mux.FROM_DR)
                self.data_path.latch_pc()
                self.inc_ticks()

    def run_fetches(self):
        self.instruction_fetch()
        self.abstract_execution()
        self.data_path.latch_flags()
        logging.debug(self.self_shot())

    def self_shot(self) -> str:
        return "TICK: {:4} | AC {:7} | IR: {:4} | ADDR: {:4} | PC: {:3} | DR: {:7} | SP : {:4} | mem[ADDR] {:7} | ToMEM : {:3} |".format(
            self.get_ticks(),
            self.data_path.acc,
            self.data_path.ir["opcode"],
            self.data_path.addr,
            self.data_path.pc,
            self.data_path.dr,
            self.data_path.sp,
            self.data_path.mem[self.data_path.addr]["value"],
            self.data_path.mr,
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
        ALUOpcode.NEXT_IN_B,
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
    data_path = DataPath(mem_capacity, input_token)
    control_unit = ControlUnit(data_path, code)
    instr_counter = 0
    try:
        while instr_counter < bound:
            control_unit.run_fetches()
            instr_counter += 1
    except ExitExceptionError:
        pass

    if instr_counter > bound:
        logging.warning("Limit exceeded!")
    logging.info("symbol_buffer: %s", repr("".join(data_path.output_buf_sym)))
    logging.info("numeric_buffer: [%s]", ", ".join(str(x) for x in data_path.output_buf_num))
    return (
        data_path.output_buf_sym,
        data_path.output_buf_num,
        instr_counter,
        control_unit.get_ticks(),
    )


def main(source, file):
    code = read_code(source)
    input_tokens = read_data(file)
    mem_size = 300
    bound = 5000
    symbols, nums, instr_counter, ticks_counter = simulation(code, input_tokens, mem_size, bound)

    print("".join(symbols))
    if len(nums) != 0:
        print(nums)
    print("count of instructions: ", instr_counter)
    print("count of ticks: ", ticks_counter)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
