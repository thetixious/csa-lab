org 10
  limit:
      .word 4000000
  odd:
      .word 1
  prev:
      .word 1
  cur:
      .word 2
  tmp:
      .word 0
  result:
      .word 0
  out_port:
      .word 1

  _start:
      ld cur
      cmp limit
      jg end
      and odd
      jnz finally
      if_even:
          ld result
          add cur
          st result
      finally:
          inc
          dec
          ld cur
          st tmp
          add prev
          st cur
          ld tmp
          st prev
      jmp _start
      end:
          ld result
          out out_port
      hlt