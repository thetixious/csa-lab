org 10
out_port:
    .word 0

_start:
    in
    loop:
        out out_port
        in
        jz break
        jmp loop
    break:
        hlt
