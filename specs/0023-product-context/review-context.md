# Code review context: skill `product` e contexto de produto (0023)

## O que foi construído

Uma skill de agente `product` (`/aia:product`) que cria ou atualiza `specs/_product/{mission,tech-stack,roadmap}.md` num projeto consumidor, inferindo do repositório com fonte citada e transformando em marcador de clarificação o que não é inferível. Três templates novos dão a forma dos artefatos. `specify` passa a ler mission e roadmap, e `plan` passa a ler tech-stack, sempre de forma condicional (sem os arquivos, nada muda). A branch também traz as specs 0024–0029, que são só documentos, e o `specs/_product/` do próprio aiadev (dogfooding, fora do pacote).

## Referências

- Spec: `specs/0023-product-context/spec.md`
- Plan: `specs/0023-product-context/plan.md`
- Tasks: `specs/0023-product-context/tasks.md` (15/15 `done`)
- Specs só-documento na mesma PR: `specs/0024-replan/` … `specs/0029-artifact-only-handoffs/`

## Arquivos alterados

38 arquivos, 2724 inserções, 6 remoções (`git diff --stat main...HEAD`). Código de produção Python: só `scripts/generate_pipeline_reference.py` (+1 linha). O resto é Markdown (skills, templates, registros, specs) e testes.

## Decisões principais

- `product` fica fora de `PIPELINE_SKILLS` e do `aiadev preflight` (spec cl-4): o modo tools/MCP exige um artefato por chamada e `product` escreve três.
- `specs/_product/` é um caminho fixo, sem configuração (cl-1). `pipeline_state` e `metrics` já ignoram o diretório.
- `tech-stack.md` registra decisões e o bloco auto-stack é o inventário detectado. O `plan` lista a divergência entre os dois e não escolhe (cl-3).
- Não há parser de roadmap nesta feature: a gramática existe só no template, e o parser fica para a 0024 (plan ADR-3).
- Os testes de skill são de texto, com escopo por seção ou por passo do Loop, e os de instalação rodam de verdade, via `CliRunner`, nas 5 plataformas.

## Pontos que merecem atenção

- O texto das skills é o comportamento. Vale ler `skills/product/SKILL.md` do começo ao fim, como um agente consumidor leria.
- O dogfooding (T015) expôs três falhas corrigidas nesta branch: os comentários-guia reprovavam no bloqueio de marcadores do CI, uma citação na linha de campo quebrava o parser do roadmap, e os manifestos de monorepo não eram lidos.
- As respostas de conteúdo de `specs/_product/` foram aprovadas pelo mantenedor em 2026-09-25. Os trechos sem fonte estão marcados como decisão do mantenedor.
- `.aiadev/review.yaml` local tinha uma aprovação de 2026-05-28, de outra branch. O gate atual não amarra a aprovação à branch nem ao commit; a spec 0025 trata disso.

## Cobertura de testes

- `.venv/bin/python -m pytest --ignore=tests/test_mcp_server.py` → `1209 passed, 3 skipped` (linha de base na `main`: 1137 passed). `tests/test_mcp_server.py`: 7 falhas pré-existentes, porque o extra opcional `mcp` não está instalado no venv local.
- `.venv/bin/aiadev validate --quiet` → exit 0.
- `npx markdownlint-cli2@0.13.0 '**/*.md'` (versão do CI) → 0 erros fora de `node_modules/` local.
- Grep do bloqueio de marcadores do CI em `specs/**` → nenhuma ocorrência.
- Cada task passou por revisão de spec e de qualidade (`.review-log.jsonl`), mais uma revisão final da branch com checagem de drift.
- Verificação manual: rodei a skill `product` neste repositório (T015) e revisei a saída com o mantenedor.
