# Micro-feature do benchmark 0030: `aiadev hello`

Spec fixa e idêntica nos dois braços. Não edite entre pares.

## Demanda

Num projeto Python de exemplo vazio (CLI com `click`, `pytest`), adicionar um
subcomando `greet` que cumprimenta uma pessoa, com testes.

## Comportamento

- `greet NAME` imprime `Hello, NAME!` e sai com 0.
- `greet NAME --shout` imprime `HELLO, NAME!`.
- `greet` sem `NAME` sai com código 2 e a mensagem de uso do `click`.

## Tasks esperadas

1. Subcomando `greet NAME` com teste de saída e de código de saída.
2. Opção `--shout` com teste.
3. Erro de uso sem `NAME` com teste e linha no README do projeto de exemplo.

## Fora de escopo

Internacionalização, cores, outros subcomandos.
