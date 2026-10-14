# Baseline de cobertura cenário→task

Medição de `aiadev.spec_coverage.check` sobre as specs existentes (spec 0030,
T020). Serve de linha de base: features novas devem passar limpas; as antigas
ficam listadas em [`coverage-exceptions.yaml`](./coverage-exceptions.yaml) até
serem corrigidas. As specs antigas não foram editadas.

## Resultado

Das 23 features com `spec.md` e `tasks.md`, **10 passam limpas** e **13 têm
issues** (todas com exceção registrada).

Passam limpas: 0013, 0016, 0018, 0019, 0020, 0021, 0022, 0023, 0030 e
feature-cursor-platform-handler.

## Features com issues

| Feature | Issues | Kinds | Motivo |
| --- | --- | --- | --- |
| 0008-llm-tool-integration | 13 | orphan_task 11, uncovered_scenario 2 | tasks anteriores à linha "Spec scenarios" |
| 0009-token-economy-terse-mode | 5 | orphan_task 5 | tasks anteriores à linha "Spec scenarios" |
| 0010-pipeline-preflight-checks | 5 | orphan_task 5 | tasks anteriores à linha "Spec scenarios" |
| 0011-specify-reconnaissance | 4 | orphan_task 2, uncovered_scenario 1, unknown_criterion 1 | tasks sem referência; critério citado não existe |
| 0012-vscode-spec-explorer | 5 | orphan_task 5 | tasks anteriores à linha "Spec scenarios" |
| 0014-bmad-inspired-evolutions | 2 | orphan_task 2 | tasks sem referência |
| 0015-aiadev-metrics | 1 | orphan_task 1 | task sem referência |
| 0017-knowledge-graph-context-provider | 3 | uncovered_scenario 3 | cenários sem task |
| feature-codex-opencode-gemini-handlers | 7 | unknown_reference 6, orphan_task 1 | referências em formato antigo |
| feature-extensions-system-mvp | 1 | orphan_task 1 | task sem referência |
| feature-install-interactive | 1 | orphan_task 1 | task sem referência |
| feature-pypi-packaging-and-publish | 3 | orphan_task 1, uncovered_scenario 2 | task sem referência; cenários sem task |
| feature-scope-user-per-home-install | 1 | orphan_task 1 | task sem referência |

## Como manter

`tests/test_spec_coverage.py` falha se uma feature suja não está na lista de
exceções ou se uma exceção já passa limpa (remova-a). Corrigir uma feature
antiga é editar sua `tasks.md` e apagar a linha correspondente em
`coverage-exceptions.yaml`.
