org 10
  message:
      .word 13, 'Hello, World!'
  pointer:
      .word message
  cycles:
      .word 0
  out_port:
      .word 0

  _start:
      ld message
      st cycles
      loop:
          ld pointer
          inc
          st pointer
          ld (pointer)
          out out_port
          ld cycles
          dec
          st cycles
          jnz loop
      hlt