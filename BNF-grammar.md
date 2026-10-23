# Gramática Formal BNF — Linguagem MiniPar 2026.1

**Projeto:** MiniPar-Improvement — Compilador da Linguagem MiniPar 2026.1 Orientada a Objetos  
**Autores:** Emanuele Vitória de Jesus Lima · Jose Lucas de Oliveira Quintela · Luiz Miguel de Melo Bomfim  
**Instituição:** Universidade Federal de Alagoas — Instituto de Computação · Ciência da Computação  
**Disciplina:** Compiladores — Prof. Arturo Hernandez Dominguez  
**Repositório:** https://github.com/luizwhirl/minipar-improvement  

---

> Esta gramática foi derivada diretamente da implementação real do compilador
> (arquivos `src/lexer.py`, `src/parser.py` e `src/ast_nodes.py`), cruzada com
> o relatório técnico do projeto e as especificações formais fornecidas pelo professor.
> Ela descreve **toda** a sintaxe aceita pelo compilador MiniPar 2026.1.

> **Atualização MiniPar 2026.2 — CORE-03 (23/10/2026):** primitivas de strings
> de C-T11-v1 §3.3 implementadas nas seções 14, 15 e nas notas de implementação.
> `substr` e `to_string` usam a produção existente `<chamada_funcao>` (`FuncCallExpr`),
> sem novos tokens ou produções. Os créditos e a gramática de origem foram preservados.
> **CORE-04/05 (23/10/2026):** tokens e produções Fork/Join na seção 10 e BNF
> consolidada; análise semântica implementada, geração/execução pendentes de CORE-06/07.

---

## Sumário

1. [Notação utilizada](#1-notação-utilizada)
2. [Tokens (Análise Léxica)](#2-tokens-análise-léxica)
3. [Programa](#3-programa)
4. [Declarações](#4-declarações)
5. [Comandos](#5-comandos)
6. [Blocos Sequencial e Paralelo](#6-blocos-sequencial-e-paralelo)
7. [Estruturas de Controle](#7-estruturas-de-controle)
8. [Orientação a Objetos](#8-orientação-a-objetos)
9. [Funções](#9-funções)
10. [Expressões](#10-expressões)
11. [Comunicação por Canais](#11-comunicação-por-canais)
12. [Coleções](#12-coleções)
13. [Entrada e Saída](#13-entrada-e-saída)
14. [Tipos e Literais](#14-tipos-e-literais)
15. [Biblioteca Nativa](#15-biblioteca-nativa)
16. [Comentários](#16-comentários)
17. [Gramática Consolidada (BNF Completa)](#17-gramática-consolidada-bnf-completa)

---

## 1. Notação utilizada

| Símbolo | Significado |
|---------|-------------|
| `::=` | Definição de produção |
| `\|` | Alternativa (ou) |
| `{ x }` | Zero ou mais repetições de `x` |
| `[ x ]` | Opcional (zero ou uma ocorrência de `x`) |
| `( x )` | Agrupamento |
| `"token"` | Terminal literal (palavra reservada ou símbolo) |
| `<não-terminal>` | Símbolo não-terminal |

---

## 2. Tokens (Análise Léxica)

O analisador léxico (`src/lexer.py`) produz os seguintes tokens a partir do código-fonte.  
Comentários iniciados por `#` são descartados pelo lexer antes da geração de tokens.

### 2.1 Palavras Reservadas

```
class  extends  new  func  var
if  else  while  do  for  in
break  continue  return
seq  par  this  fork  join  on
c_channel  send  receive  input  print  matrix
true  false
number  int  string  bool  void  list  dict
```

### 2.2 Literais

```bnf
<NUMBER>         ::= <digito> { <digito> } [ "." <digito> { <digito> } ]
<STRING_LITERAL> ::= '"' { <caractere> } '"'
<BOOL_LITERAL>   ::= "true" | "false"
<IDENTIFIER>     ::= ( <letra> | "_" ) { <letra> | <digito> | "_" }
```

### 2.3 Operadores

| Categoria | Tokens |
|-----------|--------|
| Aritméticos | `+`  `-`  `*`  `/`  `%` |
| Relacionais | `==`  `!=`  `<`  `>`  `<=`  `>=` |
| Lógicos | `&&`  `\|\|`  `!` |
| Atribuição | `=` |

### 2.4 Delimitadores

```
(  )  {  }  [  ]  .  ;  ,
```

### 2.5 Tipos declaráveis

```bnf
<tipo> ::= "number" | "int" | "string" | "bool" | "void" | "list" | "dict"
```

---

## 3. Programa

O programa MiniPar é uma sequência de zero ou mais declarações e comandos no nível global.

```bnf
<programa> ::= { <declaracao_global> | <comando> }

<declaracao_global> ::= <declaracao_classe>
                      | <declaracao_funcao>
                      | <declaracao_variavel>
```

---

## 4. Declarações

### 4.1 Declaração de Variável

```bnf
<declaracao_variavel> ::= "var" <IDENTIFIER> [ "=" <expressao> ] ";"
                        | <tipo> <IDENTIFIER> [ "=" <expressao> ] ";"
```

**Exemplos:**

```minipar
var x = 42;
var nome = "MiniPar";
number total = 0;
bool ativo = true;
```

### 4.2 Declaração de Função

```bnf
<declaracao_funcao> ::= "func" <IDENTIFIER> "(" [ <lista_parametros> ] ")" <bloco_seq>

<lista_parametros> ::= <parametro> { "," <parametro> }

<parametro> ::= [ <tipo> ] <IDENTIFIER>
```

**Exemplos:**

```minipar
func somar(a, b) {
    return a + b;
}

func calcular(number x, number y) {
    return x * y;
}
```

### 4.3 Declaração de Classe

```bnf
<declaracao_classe> ::= "class" <IDENTIFIER> [ "extends" <IDENTIFIER> ] "{"
                            { <membro_classe> }
                        "}"

<membro_classe> ::= "var" <declaracao_variavel>
                  | "func" <declaracao_funcao>
```

**Exemplos:**

```minipar
class Animal {
    var nome = "Animal";
    func falar() {
        print("...");
    }
}

class Cachorro extends Animal {
    func falar() {
        print("Au!");
    }
}
```

---

## 5. Comandos

```bnf
<comando> ::= <declaracao_variavel>
            | <atribuicao>
            | <bloco_seq>
            | <bloco_par>
            | <comando_if>
            | <comando_while>
            | <comando_do_while>
            | <comando_for>
            | <comando_print>
            | <comando_send>
            | <comando_return>
            | <comando_break>
            | <comando_continue>
            | <chamada_funcao> ";"
            | <chamada_metodo> ";"
            | <expressao_fork> ";"
            | <expressao_join> ";"
```

### 5.1 Atribuição

A atribuição suporta identificadores simples, propriedades de objetos e indexação de coleções:

```bnf
<atribuicao> ::= <alvo_atribuicao> "=" <expressao> ";"

<alvo_atribuicao> ::= <IDENTIFIER>
                    | <expressao_posfixo> "." <IDENTIFIER>
                    | <expressao_posfixo> "[" <expressao> "]"
```

**Exemplos:**

```minipar
x = 10;
objeto.campo = 42;
lista[0] = "primeiro";
```

### 5.2 Comando Print

```bnf
<comando_print> ::= "print" "(" [ <expressao> { "," <expressao> } ] ")" ";"
```

**Exemplos:**

```minipar
print("Olá, mundo!");
print("Valor:", x, "e", y);
```

### 5.3 Comando Return

```bnf
<comando_return> ::= "return" [ <expressao> ] ";"
```

### 5.4 Comandos Break e Continue

```bnf
<comando_break>    ::= "break" ";"
<comando_continue> ::= "continue" ";"
```

> `break` e `continue` são válidos somente dentro de laços (`while`, `do-while`, `for`).  
> O analisador semântico reporta erro se forem usados fora de laço.

---

## 6. Blocos Sequencial e Paralelo

### 6.1 Bloco Sequencial (SEQ)

Executa os comandos internos em ordem, da mesma forma que um bloco tradicional.

```bnf
<bloco_seq> ::= "seq" "{" { <comando> } "}"
              | "{" { <comando> } "}"
```

O `seq` é opcional: blocos com chaves `{ }` são tratados como sequenciais por padrão.

### 6.2 Bloco Paralelo (PAR)

Cada comando interno é executado como uma `std::thread` independente em C++.  
As threads são sincronizadas por `join()` ao final do bloco.

```bnf
<bloco_par> ::= "par" "{" { <comando> } "}"
```

**Exemplo:**

```minipar
par {
    seq { print("Thread A"); }
    seq { print("Thread B"); }
    seq { print("Thread C"); }
}
```

---

## 7. Estruturas de Controle

### 7.1 If / Else

```bnf
<comando_if> ::= "if" "(" <expressao> ")" <comando>
                 [ "else" <comando> ]
```

**Exemplos:**

```minipar
if (x > 0) {
    print("positivo");
}

if (x > 0) {
    print("positivo");
} else {
    print("negativo ou zero");
}

# Encadeamento if-else-if
if (x > 0) {
    print("positivo");
} else if (x < 0) {
    print("negativo");
} else {
    print("zero");
}
```

### 7.2 While

```bnf
<comando_while> ::= "while" "(" <expressao> ")" <comando>
```

**Exemplo:**

```minipar
while (i < 10) {
    i = i + 1;
}
```

### 7.3 Do-While

```bnf
<comando_do_while> ::= "do" <comando> "while" "(" <expressao> ")" [ ";" ]
```

**Exemplo:**

```minipar
do {
    tentativas = tentativas + 1;
} while (tentativas < 5);
```

### 7.4 For

O `for` suporta tanto o estilo clássico (inicializador; condição; incremento) quanto o estilo iterador (`for var x in colecao`):

```bnf
<comando_for> ::= "for" "(" <for_classico> | <for_iterador> ")" <comando>

<for_classico> ::= [ <inicializador_for> ] ";" [ <expressao> ] ";" [ <incremento_for> ]

<inicializador_for> ::= "var" <IDENTIFIER> [ "=" <expressao> ]
                      | <tipo> <IDENTIFIER> [ "=" <expressao> ]
                      | <alvo_atribuicao> "=" <expressao>
                      | <expressao>

<incremento_for>    ::= <alvo_atribuicao> "=" <expressao>
                      | <expressao>

<for_iterador>      ::= "var" <IDENTIFIER> "in" <expressao>
```

**Exemplos:**

```minipar
# For clássico
for (var i = 0; i < 10; i = i + 1) {
    print(i);
}

# For iterador
for (var item in lista) {
    print(item);
}

# For com range()
for (var i in range(5)) {
    print(i);
}
```

---

## 8. Orientação a Objetos

### 8.1 Instanciação com new

```bnf
<expressao_new> ::= "new" <IDENTIFIER> "(" [ <lista_argumentos> ] ")"
```

**Exemplo:**

```minipar
var obj = new MinhaClasse();
var rede = new RedeNeural(0.5);
```

### 8.2 Acesso a Propriedades

```bnf
<acesso_propriedade> ::= <expressao_posfixo> "." <IDENTIFIER>
```

**Exemplo:**

```minipar
print(neuronio.peso);
```

### 8.3 Chamada de Método

```bnf
<chamada_metodo> ::= <expressao_posfixo> "." <IDENTIFIER> "(" [ <lista_argumentos> ] ")"
```

**Exemplo:**

```minipar
neuronio.treinar();
algoritmo.ordenar();
rede.feedforward(x1, x2);
```

### 8.4 Atribuição de Propriedade

```bnf
<atrib_propriedade> ::= <expressao_posfixo> "." <IDENTIFIER> "=" <expressao> ";"
```

**Exemplo:**

```minipar
this.peso = this.peso + 0.01;
obj.nome = "novo";
```

### 8.5 Referência a this

Dentro de métodos de uma classe, `this` refere-se à instância corrente.

```bnf
<expressao_this> ::= "this"
```

### 8.6 Herança

```bnf
<declaracao_classe> ::= "class" <IDENTIFIER> "extends" <IDENTIFIER> "{"
                            { <membro_classe> }
                        "}"
```

**Exemplo:**

```minipar
class Cachorro extends Animal {
    func latir() {
        print("Au!");
    }
}
```

---

## 9. Funções

### 9.1 Chamada de Função

```bnf
<chamada_funcao> ::= <IDENTIFIER> "(" [ <lista_argumentos> ] ")"

<lista_argumentos> ::= <expressao> { "," <expressao> }
```

### 9.2 Recursão

Funções podem se chamar recursivamente sem nenhuma sintaxe especial:

```minipar
func fatorial(n) {
    if (n <= 1) {
        return 1;
    }
    return n * fatorial(n - 1);
}
```

---

## 10. Expressões

As expressões seguem a hierarquia de precedência implementada no parser (da menor para a maior precedência):

```bnf
<expressao> ::= <expressao_ou>

<expressao_ou>  ::= <expressao_e> { "||" <expressao_e> }

<expressao_e>   ::= <expressao_comp> { "&&" <expressao_comp> }

<expressao_comp> ::= <expressao_termo>
                     { ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) <expressao_termo> }

<expressao_termo> ::= <expressao_fator> { ( "+" | "-" ) <expressao_fator> }

<expressao_fator> ::= <expressao_unaria> { ( "*" | "/" | "%" ) <expressao_unaria> }

<expressao_unaria> ::= ( "-" | "+" | "!" ) <expressao_unaria>
                     | <expressao_posfixo>

<expressao_posfixo> ::= <expressao_primaria>
                        { "." <IDENTIFIER> [ "(" [ <lista_argumentos> ] ")" ]
                        | "[" <expressao> "]"
                        }

<expressao_primaria> ::= <NUMBER>
                       | <STRING_LITERAL>
                       | <BOOL_LITERAL>
                       | <IDENTIFIER> [ "(" [ <lista_argumentos> ] ")" ]
                       | "this"
                       | <expressao_new>
                       | <expressao_c_channel>
                       | <expressao_receive>
                       | <expressao_input>
                       | <expressao_lista>
                       | <expressao_matrix>
                       | <expressao_fork>
                       | <expressao_join>
                       | "(" <expressao> ")"
```

### Fork/Join — CORE-04/05 (2026.2)

```bnf
<expressao_fork> ::= "fork" <IDENTIFIER> "(" [ <lista_argumentos> ] ")" [ "on" <expressao> ]
<expressao_join> ::= "join" "(" <expressao> [ "," <expressao> ] ")"
```

São expressões primárias, também aceitas como comandos terminados por `;`.
O sufixo `on` consome uma expressão completa como destino; para aplicar um
operador ao handle depois do destino, delimitar o fork com parênteses.
Sem `on`, `destination=None` representa execução local. `"local"` e
`"host:porta"` são valores string; a validade do endereço pertence ao runtime.
Os argumentos e o destino permanecem expressões da AST, sem captura implícita.
`fork` retorna `task`, um tipo **inferido**, sem nova palavra de tipo declarativo.
`join` devolve o tipo do resultado da tarefa quando conhecido, ou `unknown`.
Chamadas, propriedades, índices e precedência aritmética existentes são preservados.

```minipar
func dobro(n) { var r = n * 2; return r; }
seq {
    var h1 = fork dobro(3);
    var h2 = fork dobro(4) on "local";
    print(join(h1) + join(h2, 1000));
}
```

Este exemplo passa pelo Lexer/Parser/AST/semântico; **não executa ainda**.
Até CORE-06/07, o pipeline recusa Fork/Join explicitamente antes de gerar TAC/C++.

| Regra | Validação implementada |
|---|---|
| FJ-SEM-01 | Nome deve resolver função global, sem variável ou função local sombreando-o |
| FJ-SEM-02 | Aridade igual à quantidade de parâmetros |
| FJ-SEM-03 | Handle reconhecido como `task`; funções genéricas são verificadas novamente nas chamadas conhecidas |
| FJ-SEM-04 | Destino string e timeout numérico, quando os tipos são conhecidos |
| FJ-SEM-05 | Proibir leitura/escrita de global mutável na tarefa e nas funções/métodos chamados, respeitando escopos e sombreamento |
| FJ-SEM-06 | Proibir objetos, canais e handles nos argumentos/retornos, inclusive dentro das coleções conhecidas |

Parâmetros e locais são analisados com os tipos dos argumentos de cada chamada;
a análise de uma função global não herda os locais do chamador. Chamadas recursivas
não são expandidas indefinidamente: retornos não demonstrados ficam `unknown`.
São transportáveis números, booleanos, strings e listas desses valores; `matrix`
é tratada como coleção aninhada na verificação parcial. Retorno vazio representa
`none` do runtime. A restrição temporária de listas de strings do CORE-03 continua.
O acompanhamento de listas é conservador: não representa posições individuais nem
remove tipos após `pop`/sobrescrita; listas heterogêneas podem produzir `unknown`.
Mutação através de chamadas/atributos e fluxos genéricos não têm inferência completa.
Ausência de diagnóstico nesses casos **não comprova** serialização nem execução.
Detalhes da AST, metadados, evidências e limites em
[`docs/auditorias/CORE-04-05_FORK_JOIN.md`](docs/auditorias/CORE-04-05_FORK_JOIN.md).

### Tabela de Precedência (maior nível = avaliado primeiro)

| Nível | Operadores | Associatividade |
|-------|-----------|-----------------|
| 7 (mais alta) | `()` `[]` `.` (posfixo) | esquerda |
| 6 | `!` `-` (unário) `+` (unário) | direita |
| 5 | `*` `/` `%` | esquerda |
| 4 | `+` `-` | esquerda |
| 3 | `==` `!=` `<` `>` `<=` `>=` | esquerda |
| 2 | `&&` | esquerda |
| 1 (mais baixa) | `\|\|` | esquerda |

---

## 11. Comunicação por Canais

A comunicação entre processos/computadores é feita via canais TCP implementados pela classe `MiniParChannel` no C++ gerado.

### 11.1 Criação de Canal

```bnf
<expressao_c_channel> ::= "c_channel" "(" <expressao> "," <expressao> ")"
```

O primeiro argumento é o endereço IP (string) e o segundo é a porta (número).

**Exemplo:**

```minipar
var canal = c_channel("127.0.0.1", 5000);
var canal_remoto = c_channel("192.168.1.10", 8080);
```

### 11.2 Envio de Mensagem (Send)

```bnf
<comando_send> ::= "send" "(" <expressao> "," <expressao> ")" ";"
```

O primeiro argumento é o canal e o segundo é a mensagem a enviar.

**Exemplo:**

```minipar
send(canal, "Hello Server");
send(canal, resultado);
```

### 11.3 Recebimento de Mensagem (Receive)

```bnf
<expressao_receive> ::= "receive" "(" <expressao> ")"
```

**Exemplo:**

```minipar
var mensagem = receive(canal);
var dado = receive(c_channel("127.0.0.1", 5000));
```

---

## 12. Coleções

### 12.1 Lista (Array)

```bnf
<expressao_lista> ::= "[" [ <expressao> { "," <expressao> } ] "]"
```

**Exemplos:**

```minipar
var vazio = [];
var numeros = [1, 2, 3, 4, 5];
var negativos = [0, -1, -2];
```

O backend atual armazena listas numéricas como `std::vector<double>`. Listas de
strings continuam previstas na sintaxe da linguagem, mas ainda não têm implementação
completa (C-T11-v1 §3.4, PEND-T11-03). Literais e `append`/`push_back` de strings
identificados pelo semântico são rejeitados com diagnóstico; tipos desconhecidos
ficam sujeitos à checagem do C++. CORE-03 não implementa listas de strings.

### 12.2 Indexação

```bnf
<expressao_indice> ::= <expressao_posfixo> "[" <expressao> "]"
```

**Exemplo:**

```minipar
var primeiro = lista[0];
var ultimo = lista[len(lista) - 1];
```

### 12.3 Atribuição por Índice

```bnf
<atrib_indice> ::= <expressao_posfixo> "[" <expressao> "]" "=" <expressao> ";"
```

**Exemplo:**

```minipar
lista[0] = 99;
matriz[i][j] = "#";
```

### 12.4 Matriz (Matrix)

Cria uma matriz bidimensional de `linhas × colunas` inicializada com um valor padrão.

```bnf
<expressao_matrix> ::= "matrix" "(" <expressao> "," <expressao> "," <expressao> ")"
```

**Exemplo:**

```minipar
var tela = matrix(9, 9, " ");       # matriz 9×9 de espaços
var zeros = matrix(3, 3, 0);        # matriz 3×3 de zeros
```

---

## 13. Entrada e Saída

### 13.1 Saída (Print)

```bnf
<comando_print> ::= "print" "(" [ <expressao> { "," <expressao> } ] ")" ";"
```

Múltiplos argumentos são impressos separados por espaço seguidos de `\n`.

### 13.2 Entrada (Input)

```bnf
<expressao_input> ::= "input" "(" [ <expressao> ] ")"
```

Lê uma linha da entrada padrão (stdin). O argumento opcional é exibido como prompt antes da leitura.

**Exemplos:**

```minipar
var nome = input("Seu nome: ");
var valor = input();
var numero = to_number(input("Digite um número: "));
```

---

## 14. Tipos e Literais

### 14.1 Número

```bnf
<literal_numero> ::= <digito> { <digito> } [ "." { <digito> } ]
```

Representa inteiros e ponto flutuante. O C++ deduz o tipo dos literais (`int` ou
ponto flutuante); elementos das listas numéricas e `to_number` usam `double`.
`len` devolve um inteiro com sinal (`std::ptrdiff_t`), portanto `len("") - 1`
e `len([]) - 1` resultam em `-1`.

**Exemplos:** `0`, `42`, `3.14`, `0.5`

### 14.2 String

```bnf
<literal_string> ::= '"' { <caractere_string> } '"'

<caractere_string> ::= <qualquer_caractere_exceto_aspas_e_barra>
                     | "\\" "n"    # newline
                     | "\\" "t"    # tab
                     | "\\" '"'    # aspas duplas
                     | "\\" "\\"   # barra invertida
```

Literais são traduzidos para `std::string`, inclusive quando inicializam variáveis
ou atributos e quando são retornados por funções/métodos. Uma função pode retornar
literal em um ramo e string calculada em outro. `string s;` inicia uma string vazia.
UTF-8 é preservado na saída; `len` e `substr` contam **bytes**, sem decodificar Unicode
(as expressões do Teste 11 são ASCII).

`+` concatena dois valores string: literais, variáveis, atributos, retornos de
funções/métodos e resultados de `substr`/`to_string`, incluindo acumulação em laço.
String + número exige `to_string` explícito. Comparações `==`, `!=`, `<`, `<=`, `>`
e `>=` entre strings usam conteúdo e ordem lexicográfica por byte, inclusive entre
dois literais; `"10" < "9"` é verdadeiro. String comparada com número é rejeitada.
Operandos de tipos conhecidos incompatíveis falham no semântico; parâmetros e
retornos ainda desconhecidos são verificados pelo compilador C++.
`&&` e `||` preservam o curto-circuito do C++, permitindo proteger `substr` com
`i < len(s) && substr(s, i, 1) == "x"`.

### 14.3 Booleano

```bnf
<literal_bool> ::= "true" | "false"
```

### 14.4 Identificador

```bnf
<IDENTIFIER> ::= ( <letra> | "_" ) { <letra> | <digito> | "_" }

<letra>  ::= "A" | ... | "Z" | "a" | ... | "z"
<digito> ::= "0" | ... | "9"
```

---

## 15. Biblioteca Nativa

As seguintes funções são reconhecidas pelo analisador semântico e traduzidas diretamente pelo gerador de código C++:

| Função MiniPar | Assinatura | Descrição |
|---------------|------------|-----------|
| `print(...)` | `print(expr, ...)` | Imprime na saída padrão |
| `input([prompt])` | `input()` / `input(expr)` | Lê linha do stdin |
| `exp(x)` | `exp(number)` → `number` | Exponencial natural (eˣ) |
| `random()` | `random()` → `number` | Número aleatório entre 0 e 1 |
| `range(n)` / `range(a,b)` | `range(int)` → `list` | Gera sequência inteira |
| `len(col)` | `len(list\|string)` → `number` | Comprimento com sinal; bytes em strings (também aceita matrizes) |
| `substr(s, inicio, tamanho)` | `substr(string, number, number)` → `string` | Cópia de recorte base 0, com índices inteiros e limites estritos |
| `to_string(x)` | `to_string(number)` → `string` | Inteiros, inclusive em `double`, sem casas decimais e com sinal negativo |
| `to_number(s)` | `to_number(string)` → `number` | Converte string para número |
| `parse_ints(s)` | `parse_ints(string)` → `list` | Parseia inteiros de string separados por espaço |

`substr` exige exatamente três argumentos; `len` e `to_string`, exatamente um.
Aridade e tipos conhecidos são verificados no semântico. Para `substr`, índices
numéricos com valor inteiro exato (`2`, `2.0`, valor de lista numérica) são aceitos.
Exigem-se valores finitos e `0 <= inicio <= len(s)`,
`0 <= tamanho <= len(s) - inicio`. Não há truncamento, arredondamento, índice negativo
nem redução automática do tamanho. São válidos `substr(s, len(s), 0)` e
`substr("", 0, 0)`; a string original não muda. Valores fracionários, NaN, infinito
ou fora dos limites escrevem diagnóstico com `substr`, `inicio`, `tamanho` e `len`
no stderr, descarregam o stdout anterior e encerram o processo com código **1**.

`to_string` formata valores inteiros sem converter para um tipo inteiro de faixa
menor: `42.0` vira `"42"`, `-46.0` vira `"-46"` e zero negativo vira `"0"`.
Para valores fracionários usa a precisão `max_digits10` do tipo C++, com locale
clássico (ponto decimal, sem separador de milhar); notação científica pode aparecer.
NaN e infinito seguem a representação do stream C++. Esses valores não inteiros
não fazem parte das entradas exigidas pelo T11.

### Métodos de Lista (acesso via ponto)

| Método | Descrição |
|--------|-----------|
| `.append(v)` / `.push_back(v)` | Adiciona elemento ao final |
| `.pop()` | Remove e retorna o último elemento |
| `.size()` | Retorna o tamanho da lista |

---

## 16. Comentários

```bnf
<comentario> ::= "#" { <qualquer_caractere> } <fim_de_linha>
```

Comentários iniciam com `#` e vão até o final da linha. São descartados pelo lexer.

**Exemplos:**

```minipar
# Isso é um comentário de linha inteira
var x = 10; # Comentário ao final da linha
```

---

## 17. Gramática Consolidada (BNF Completa)

A seguir a gramática completa em formato BNF, em ordem de definição:

```bnf
(* ============================================================ *)
(*       GRAMÁTICA BNF — LINGUAGEM MINIPAR 2026.1               *)
(*       Compilador: minipar-improvement                        *)
(*       Repositório: github.com/luizwhirl/minipar-improvement  *)
(* ============================================================ *)


(* ─── ESTRUTURA GLOBAL ─── *)

<programa> ::= { <declaracao_global> | <comando> }

<declaracao_global> ::= <declaracao_classe>
                      | <declaracao_funcao>
                      | <declaracao_variavel>


(* ─── DECLARAÇÕES ─── *)

<declaracao_variavel> ::= "var" <IDENTIFIER> [ "=" <expressao> ] ";"
                        | <tipo> <IDENTIFIER> [ "=" <expressao> ] ";"

<declaracao_funcao>   ::= "func" <IDENTIFIER> "(" [ <lista_parametros> ] ")" <bloco_seq>

<lista_parametros>    ::= <parametro> { "," <parametro> }
<parametro>           ::= [ <tipo> ] <IDENTIFIER>

<declaracao_classe>   ::= "class" <IDENTIFIER> [ "extends" <IDENTIFIER> ]
                          "{" { <membro_classe> } "}"

<membro_classe>       ::= "var" <declaracao_variavel>
                        | "func" <declaracao_funcao>


(* ─── COMANDOS ─── *)

<comando> ::= <declaracao_variavel>
            | <atribuicao>
            | <bloco_seq>
            | <bloco_par>
            | <comando_if>
            | <comando_while>
            | <comando_do_while>
            | <comando_for>
            | <comando_print>
            | <comando_send>
            | <comando_return>
            | <comando_break>
            | <comando_continue>
            | <chamada_funcao> ";"
            | <chamada_metodo> ";"
            | <expressao_fork> ";"
            | <expressao_join> ";"

<atribuicao>        ::= <alvo_atribuicao> "=" <expressao> ";"
<alvo_atribuicao>   ::= <IDENTIFIER>
                      | <expressao_posfixo> "." <IDENTIFIER>
                      | <expressao_posfixo> "[" <expressao> "]"

<comando_print>     ::= "print" "(" [ <expressao> { "," <expressao> } ] ")" ";"
<comando_send>      ::= "send"  "(" <expressao> "," <expressao> ")" ";"
<comando_return>    ::= "return" [ <expressao> ] ";"
<comando_break>     ::= "break" ";"
<comando_continue>  ::= "continue" ";"


(* ─── BLOCOS ─── *)

<bloco_seq> ::= "seq" "{" { <comando> } "}"
              | "{" { <comando> } "}"

<bloco_par> ::= "par" "{" { <comando> } "}"


(* ─── ESTRUTURAS DE CONTROLE ─── *)

<comando_if>       ::= "if" "(" <expressao> ")" <comando> [ "else" <comando> ]

<comando_while>    ::= "while" "(" <expressao> ")" <comando>

<comando_do_while> ::= "do" <comando> "while" "(" <expressao> ")" [ ";" ]

<comando_for>      ::= "for" "(" <for_cabecalho> ")" <comando>

<for_cabecalho>    ::= <for_classico>
                     | <for_iterador>

<for_classico>     ::= [ <inicializador_for> ] ";" [ <expressao> ] ";" [ <incremento_for> ]

<inicializador_for> ::= "var"  <IDENTIFIER> [ "=" <expressao> ]
                      | <tipo> <IDENTIFIER> [ "=" <expressao> ]
                      | <alvo_atribuicao> "=" <expressao>
                      | <expressao>

<incremento_for>   ::= <alvo_atribuicao> "=" <expressao>
                     | <expressao>

<for_iterador>     ::= "var" <IDENTIFIER> "in" <expressao>


(* ─── ORIENTAÇÃO A OBJETOS ─── *)

<expressao_new>         ::= "new" <IDENTIFIER> "(" [ <lista_argumentos> ] ")"
<acesso_propriedade>    ::= <expressao_posfixo> "." <IDENTIFIER>
<chamada_metodo>        ::= <expressao_posfixo> "." <IDENTIFIER> "(" [ <lista_argumentos> ] ")"
<atrib_propriedade>     ::= <expressao_posfixo> "." <IDENTIFIER> "=" <expressao> ";"
<expressao_this>        ::= "this"


(* ─── COMUNICAÇÃO POR CANAIS ─── *)

<expressao_c_channel>   ::= "c_channel" "(" <expressao> "," <expressao> ")"
<expressao_receive>     ::= "receive" "(" <expressao> ")"
(* send já listado em <comando_send> *)


(* ─── FORK/JOIN — 2026.2; frontend implementado, backend pendente ─── *)

<expressao_fork> ::= "fork" <IDENTIFIER> "(" [ <lista_argumentos> ] ")" [ "on" <expressao> ]
<expressao_join> ::= "join" "(" <expressao> [ "," <expressao> ] ")"


(* ─── COLEÇÕES ─── *)

<expressao_lista>   ::= "[" [ <expressao> { "," <expressao> } ] "]"
<expressao_indice>  ::= <expressao_posfixo> "[" <expressao> "]"
<atrib_indice>      ::= <expressao_posfixo> "[" <expressao> "]" "=" <expressao> ";"
<expressao_matrix>  ::= "matrix" "(" <expressao> "," <expressao> "," <expressao> ")"


(* ─── ENTRADA E SAÍDA ─── *)

<expressao_input>   ::= "input" "(" [ <expressao> ] ")"
(* print já listado em <comando_print> *)


(* ─── EXPRESSÕES (hierarquia de precedência) ─── *)

<expressao>          ::= <expressao_ou>

<expressao_ou>       ::= <expressao_e> { "||" <expressao_e> }

<expressao_e>        ::= <expressao_comp> { "&&" <expressao_comp> }

<expressao_comp>     ::= <expressao_termo>
                         { ( "==" | "!=" | "<" | ">" | "<=" | ">=" )
                           <expressao_termo> }

<expressao_termo>    ::= <expressao_fator> { ( "+" | "-" ) <expressao_fator> }

<expressao_fator>    ::= <expressao_unaria> { ( "*" | "/" | "%" ) <expressao_unaria> }

<expressao_unaria>   ::= ( "-" | "+" | "!" ) <expressao_unaria>
                       | <expressao_posfixo>

<expressao_posfixo>  ::= <expressao_primaria>
                         { "." <IDENTIFIER> [ "(" [ <lista_argumentos> ] ")" ]
                         | "[" <expressao> "]"
                         }

<expressao_primaria> ::= <NUMBER>
                       | <STRING_LITERAL>
                       | <BOOL_LITERAL>
                       | <IDENTIFIER> [ "(" [ <lista_argumentos> ] ")" ]
                       | "this"
                       | <expressao_new>
                       | <expressao_c_channel>
                       | <expressao_receive>
                       | <expressao_input>
                       | <expressao_lista>
                       | <expressao_matrix>
                       | <expressao_fork>
                       | <expressao_join>
                       | "(" <expressao> ")"

<lista_argumentos>   ::= <expressao> { "," <expressao> }
<chamada_funcao>     ::= <IDENTIFIER> "(" [ <lista_argumentos> ] ")"


(* ─── TIPOS E LITERAIS ─── *)

<tipo>           ::= "number" | "int" | "string" | "bool" | "void" | "list" | "dict"

<NUMBER>         ::= <digito> { <digito> } [ "." { <digito> } ]
<STRING_LITERAL> ::= '"' { <caractere_string> } '"'
<BOOL_LITERAL>   ::= "true" | "false"
<IDENTIFIER>     ::= ( <letra> | "_" ) { <letra> | <digito> | "_" }

<caractere_string> ::= <qualquer_char_exceto_aspas_e_barra>
                     | "\n" | "\t" | '\"' | "\\"

<letra>  ::= "A" | ... | "Z" | "a" | ... | "z"
<digito> ::= "0" | ... | "9"


(* ─── COMENTÁRIOS ─── *)

<comentario> ::= "#" { <qualquer_char> } <nova_linha>
(* Descartados pelo lexer — não aparecem na AST *)
```

---

## Notas de Implementação

### Inferência de Tipos

O analisador semântico (`src/semantic.py`) usa inferência simples de tipos com as seguintes regras:

| Expressão | Tipo inferido |
|-----------|--------------|
| Literal numérico | `number` |
| Literal string | `string` |
| Literal booleano | `bool` |
| Lista literal `[...]` | `list` |
| `matrix(...)` | `matrix` |
| `c_channel(...)` | `c_channel` |
| `receive(...)` | `string` |
| `input(...)` | `string` |
| `new Classe(...)` | `Classe` |
| `this` | nome da classe atual |
| `fork f(...)` | `task`, com resultado parcial associado ao handle |
| `join(h[, timeout])` | tipo conhecido do resultado de `h`, ou `unknown` |
| `op` relacional / lógico | `bool` |
| `"a" + "b"` (concatenação) | `string` |
| `substr(...)`, `to_string(...)` | `string` |
| `len(...)`, `to_number(...)` | `number` |
| Operação aritmética | `number` |
| Identificador | tipo declarado na tabela de símbolos |
| Desconhecido | `unknown` (compatível com qualquer tipo) |

### Regras Semânticas Verificadas

| Regra | Erro reportado |
|-------|---------------|
| Redeclaração no mesmo escopo | `Variável 'x' já declarada.` |
| Uso antes de declaração | `Variável 'x' não declarada.` |
| Incompatibilidade de tipos | `Tipo incompatível em atribuição de 'x'.` |
| Função não declarada | `Função 'f' não declarada.` |
| Aridade errada (função) | `Função 'f' espera N argumento(s), recebeu M.` |
| `substr`, `to_string`, `len` com tipo conhecido incorreto | `Funcao 'f': esperado tipo, recebido tipo.` |
| `+` ou comparação entre string e outro tipo conhecido | `Operador 'op' entre string e outro tipo exige conversao explicita.` |
| Lista literal ou append de string conhecida | `Listas de strings ainda nao suportadas (C-T11-v1 3.4).` |
| Classe não declarada | `Classe 'C' não declarada.` |
| Superclasse não declarada | `Superclasse 'S' não declarada.` |
| Método inexistente | `Método 'm' não declarado em 'C'.` |
| Atributo inexistente | `Atributo 'a' não declarado em 'C'.` |
| `break`/`continue` fora de laço | `'break' usado fora de laço de repetição.` |

### Geração de Código C++20

| Construto MiniPar | Código C++ gerado |
|-------------------|------------------|
| `class C { ... }` | `class C { public: ... };` |
| `new C(args)` | `std::make_shared<C>(args)` |
| `obj.metodo(args)` | `obj->metodo(args)` |
| `obj.campo` | `obj->campo` |
| `par { a; b; }` | `std::vector<std::thread>` + `emplace_back` + `join` |
| `c_channel(ip, porta)` | `std::make_shared<MiniParChannel>(ip, porta)` |
| `send(canal, msg)` | `canal->sendData(__to_string(msg))` |
| `receive(canal)` | `canal->receiveData()` |
| `[1, 2, 3]` | `std::vector<double>{1, 2, 3}` |
| `matrix(l, c, v)` | `__make_matrix(l, c, v)` |
| `exp(x)` | `std::exp(x)` |
| `random()` | `random_val()` |
| `to_number(s)` | `std::stod(s)` |
| Literal `"texto"` | `std::string("texto")` (armazenamento e retornos reais) |
| `a + b` entre strings | `a + b` sobre `std::string` |
| Comparações entre strings | operadores C++ sobre `std::string` (conteúdo/lexicografia) |
| `len(x)` | `__minipar_len(x)` → `std::ptrdiff_t` |
| `substr(s, inicio, tamanho)` | `__minipar_substr(s, inicio, tamanho)` → `std::string` (validação antes de `s.substr`) |
| `to_string(x)` | `__minipar_to_string(x)` → `std::string` (stream com formatação numérica) |
| `range(n)` | `__minipar_range(n)` |
| `input(p)` | `input(p)` (helper C++) |

---

*Gramática gerada em 15 de junho de 2026 — MiniPar-Improvement v2026.1*
