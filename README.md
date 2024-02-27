# csa-lab

Автор: Ри Аркадий Русланович, P33081

**Исходный вариант:**
```
lisp | acc | neum | mc | tick | struct | stream | port | pstr | prob2 | 8bit 
```
**Упрощенный вариант:**
```
asm | acc | neum | hw | instr | struct | stream | port | pstr | prob2 
```

## Язык программирования
``` 
<program> ::= <asm_line> | <asm_line> <program> 
<asm_line> ::= <label> ":" <command> |
               <label> ":" <adr_command> <addres> |
               <command> |
               <command> <operand> |
               <adr_command> <operand> |
               <label> ":" <operand> |
               <empty string>
<label> ::= <letter> | <letter> <label>
<operand> ::= <address> | <label> 
<letter> ::= any symbol 
<addres> ::= any number
```


## Устройство памяти 
