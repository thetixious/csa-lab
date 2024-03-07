org 10

greet_mess:
    .word 7, 'Hello, '
pointer:
    .word greet_mess

addr_for_mess:
    .word 100
addr_output:
    .word 100
size:
    .word 0
cycles:
    .word 0
out_port:
    .word 0

_start:
    ld greet_mess
    st cycles
    print:
        ld pointer
        inc
        st pointer
        ld (pointer)
        out out_port
        ld cycles
        dec
        st cycles
        jnz print

    input:
        in
        jz print2
        st (addr_for_mess)
        ld addr_for_mess
        inc
        st addr_for_mess
        ld size
        inc
        st size
        jmp input

    print2:
        ld size
        jz break
        ld (addr_output)
        out out_port
        ld addr_output
        inc
        st addr_output
        ld size
        dec
        st size
        jmp print2








    break:
        hlt


