# Contract — `[NEEDS CLARIFICATION:cl-N ...]` marker grammar

> Definição canônica do novo formato de marcador, consumido por `specify`,
> `clarify`, validators e qualquer ferramenta que enumere ambiguidades.

## Grammar (PCRE)

```
\[NEEDS CLARIFICATION:cl-(?P<id>[1-9][0-9]*)\s+(?P<question>[^\]]+)\]
```

- Prefixo literal: `[NEEDS CLARIFICATION:` (case-sensitive, sem espaços antes do `:`).
- Id estável: `cl-` seguido de inteiro positivo (`[1-9][0-9]*`), sem zero-padding e sem zero (`cl-0` é inválido).
- Separador: pelo menos um whitespace (`\s+`) entre id e a pergunta.
- Pergunta: qualquer caractere exceto `]`, mínimo 1, máximo razoável (não validamos teto).
- Sufixo literal: `]`.

## Regras de id

- **Monotônico por spec.** O primeiro marcador é `cl-1`, o segundo `cl-2`, etc.
- **Não reutilizar.** Quando um marcador é resolvido (substituído pelo `clarify`),
  o id sai do uso. O próximo marcador novo recebe `max(existing) + 1`, mesmo
  que haja gaps.
- **Escopo é o arquivo `spec.md` corrente.** Ids de specs diferentes são
  independentes.
- Geração: `specify` faz `grep -oP "cl-(\d+)" spec.md | sort -V | tail -1`
  ou equivalente em Python; novo id = max + 1 (ou 1 se nenhum existe).

## Exemplos

```
[NEEDS CLARIFICATION:cl-1 qual provider de pagamento usar?]
[NEEDS CLARIFICATION:cl-2 limite máximo de uploads simultâneos?]
[NEEDS CLARIFICATION:cl-3 fluxo de cancelamento permite refund parcial?]
```

Inválido (rejeitado pela validação):

```
[NEEDS CLARIFICATION: pergunta sem id]            ← falta cl-N
[NEEDS CLARIFICATION:cl-001 ...]                  ← zero-padding proibido
[NEEDS CLARIFICATION:cl-1.2 ...]                  ← id deve ser inteiro
[NEEDS CLARIFICATION cl-1 ...]                    ← falta o : entre prefixo e id
```

## Schema input do `clarify`

```json
{
  "spec_path": "specs/0008-llm-tool-integration/spec.md",
  "workspace_path": "/abs/path/to/workspace",
  "answers": [
    { "id": "cl-1", "answer": "Stripe v2024-04, com fallback para Pix via Mercado Pago." },
    { "id": "cl-3", "answer": "Sim — refund parcial pelo valor proporcional já entregue." }
  ]
}
```

- `id` é a string completa `cl-N` (não o inteiro pelado).
- Ids ausentes em `answers` são preservados no spec (não removidos).
- Ids passados que não existem no spec → erro `unknown_marker_id`.

## Compatibilidade com specs antigos

Specs gravados antes desta feature usam `[NEEDS CLARIFICATION: ...]` sem id. O
parser:

- **Lê** marcadores legacy e os trata como `id = null`.
- **Reporta** marcadores legacy ao caller no payload de saída do `specify`/`clarify`,
  com flag `needs_renumbering: true`.
- **Não migra automaticamente.** Re-stamping é responsabilidade do humano (ou
  de uma ferramenta separada que pode vir em iteração futura).

## Validador (CI)

`scripts/validate_skills.py` ganha uma asserção: se um spec sob `specs/` contém
um marcador, ele deve seguir a grammar acima OU ser legacy explícito. Marcadores
malformados (typo `cl-1.2`, etc.) falham o build.
