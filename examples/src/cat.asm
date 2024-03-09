org 10
out_port:
    .word 0
in_port:
    .word 2

_start:
    in in_port
    loop:
        out out_port
        in
        jz break
        jmp loop
    break:
        hlt
