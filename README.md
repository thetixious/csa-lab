# csa-lab

Автор: Ри Аркадий Русланович, P33081

```
lisp | acc | neum | mc | tick | struct | stream | port | pstr | prob2 | 8bit 
```

## Язык программирования



```
<program> ::= <s_expression> | <s_expression> <program>

<s_expression> ::= '(' atom ')' 
                  | '(' <s_expression> ')' 
                  | <expression> 

<expression> ::= <defun_exp> 
                | <if_exp> 
                | <loop_exp>
                | <set_v_exp>
                | <print_char_exp>
                | <print_string_exp>
                | <call_user_function>

<defun_exp> ::= '(' 'defun' <idt> '(' <idt> ')' <body> ')'  
<loop> ::= '(' 'while' <s_expression> <s_expression> ')'         
<set_v_exp> ::= '(' 'set' <idt> <s_expression> ')'               
<print_char> ::= '(' 'printc' s_expression ')'                   
<print_string> ::= '(' 'prints' s_expression ')'                 
<call_user_function> ::= '(' <idt> <s_expression> ')'            

<idt> ::= <idt_l> | <idt_l> <idt>
<idt_l> ::= <letter> | '_'

<atom> ::= <literal> | <identifier>

<literal> ::= <number> | <string>
<number> ::= [ "-" ] <unsigned_number>
<unsigned_number> ::= <digit> | <digit> <unsigned_number>
<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
<string> ::= '"' <string_letters> '"'
<string_letters> ::= "" | <string_letter> | <string_letter> <string_letters>
<string_letter> ::= <any symbol except: '"'>
```
## Устройство памяти 