from __future__ import annotations
import sys
from isa import Opcode, write_code, get_opcode
from typing import TypedDict, List


class Stage1Result(TypedDict):
    l_tokens: dict
    m_tokens: dict


class ParseResult(TypedDict):
    org: int
    m_tokens: dict


class ReadFileResult(TypedDict):
    code: List
    line_count: int


def clean(lines) -> List:
    buf: list[str] = []
    for line in lines:
        if line.find(";") != -1:
            line = line[: line.find(";")].strip()
            if line == "":
                continue
            buf.append(line)
        else:
            buf.append(line)
    return buf


def find_org(lines) -> int:
    for line in lines:
        if line.find("org") == -1:
            continue
        else:
            return int(line[4:].strip())


def find_start(labels) -> int:
    position = None
    for index, label in labels.items():
        if label == "_start":
            position = index
    return position


def parse_literal(line, org, m_tokens) -> ParseResult:
    number = ""
    line_iter = 0
    line = line.strip()[6:]
    if line.find("'") != -1:
        size, line = line.split(",", 1)
        line = line.strip()
        size = int(size)
        m_tokens[org] = [size]
        org += 1
        if size > len(line) + 2:
            assert ValueError("Incorrect size of string")
        line_iter += 1
        for j in range(len(line) - 2):
            m_tokens[org] = [ord(line[line_iter])]
            line_iter += 1
            org += 1
    elif line[line_iter].isnumeric() or line[line_iter] == "-":
        for j in range(len(line)):
            number += line[line_iter]
            line_iter += 1
        m_tokens[org] = [int(number)]
        org += 1
    else:
        m_tokens[org] = [line]
        org += 1
    return org, m_tokens


def stage_1(lines, org) -> Stage1Result:
    l_tokens = {}
    m_tokens = {}
    flag = False
    for line in lines:
        if line.startswith("org"):
            flag = False
            continue
        if line.endswith(":"):
            if flag:
                org += 1
            l_tokens[org] = line[:-1]
            flag = True
            # if line.startswith("_"):
            #     org += 1
        elif line.startswith(".word"):
            org, m_tokens = parse_literal(line, org, m_tokens)
            flag = False
        else:
            row_command = line.split(" ")
            m_tokens[org] = row_command
            org += 1
            flag = False
    return l_tokens, m_tokens


def stage_2(l_tokens, m_tokens) -> dict:
    buf = {}
    for pos, token in m_tokens.items():
        new_label = []
        i_type = False
        for part in token:
            if isinstance(part, str) and part.startswith("("):
                i_type = True
                part = part[1:-1]
            for l_index, label in l_tokens.items():
                if label == part:
                    part = l_index
            new_label.append(part)
        new_label.append(i_type)
        buf[pos] = new_label
    return buf


def stage_3(r_code, start):
    code = [{"index": 0, "opcode": Opcode.JMP, "value": start, "is_indirect": False}]
    for index, token in r_code.items():
        if len(token) == 2:
            code.append(
                {
                    "index": index,
                    "opcode": get_opcode(token[0]),
                    "value": 0 if get_opcode(token[0]) not in [m.value for m in Opcode] else token[0],
                    "is_indirect": token[1],
                }
            )
        elif len(token) == 3:
            code.append({"index": index, "opcode": get_opcode(token[0]), "value": token[1], "is_indirect": token[2]})

    return code


def translate(lines):
    org: int = find_org(lines)
    lines = clean(lines)
    l_tokens, m_tokens = stage_1(lines, org)
    start: int = find_start(l_tokens)
    r_code = stage_2(l_tokens, m_tokens)
    code = stage_3(r_code, start)
    return code


def main(code_source_file, code_target):
    lines: list[str] = []
    with open(code_source_file, encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            lines.append(line.strip())
    code = translate(lines)
    write_code(code_target, code)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
