---
artifact: wop-execute-all
plan_id: 22222222-2222-4222-8222-222222222222
plan_version: 1
plan_title: "Pipeline de Evidências de Release"
language: pt-BR
source_readme: README.md
source_readme_sha256: ba3027d6cde762468105b3c8f2764a3fdd24702111be80287a7d400d4aa3a9cc
---

# Pipeline de Evidências de Release

<!-- wop:prompt-section wave_prompts -->
- prompts/wave-01.md — W001 — Descoberta do Contrato
- prompts/wave-02.md — W002 — Construir Manifesto
- prompts/wave-03.md — W003 — Verificar Pacote

<!-- wop:prompt-section orchestration -->
## Resultado <!-- wop:section outcome -->

Entregar um pacote reproduzível de evidências de release com manifesto verificado e relatório de aceite.

## Contexto de Execução <!-- wop:section execution_context -->

O exemplo usa apenas arquivos Markdown UTF-8 e demonstra descoberta paralela seguida de implementação e verificação.

## Fatos Confirmados <!-- wop:section confirmed_facts -->

- O pacote possui três ondas estritamente ordenadas.
- I001 e I002 possuem artefatos distintos e podem executar em paralelo.

## Escopo <!-- wop:section scope -->

Criar contrato, inventário, manifesto e relatório de aceite. O deploy do produto está fora do escopo.

## Partes Interessadas e Autoridade <!-- wop:section stakeholders -->

- A pessoa responsável pela release aprova o relatório final.
- Cada responsável por item pode alterar somente sua saída nomeada.

## Requisitos <!-- wop:section requirements -->

- R001: Definir o contrato de evidências da release.
- R002: Produzir um manifesto conforme o contrato.
- R003: Verificar o manifesto e reter resultados reais.

## Restrições <!-- wop:section constraints -->

- Não iniciar uma onda antes da aprovação do gate predecessor.
- Não declarar evidências que não foram produzidas.

## Decisões <!-- wop:section decisions -->

- Markdown é o formato portátil de evidência deste exemplo.

## Premissas <!-- wop:section assumptions -->

- O workspace de execução permite escrita.

## Incertezas <!-- wop:section unknowns -->

Nenhuma. Uma nova incerteza material bloqueia o trabalho afetado e exige revisão do plano ou descoberta delimitada.

## Riscos <!-- wop:section risks -->

- Deriva de contrato: congelar o handoff de W001 e parar W002 se ele mudar.
- Geração parcial: preservar o último artefato aceito e reportar a verificação que falhou.

## Ambientes e Operações <!-- wop:section operations -->

Executar em workspace descartável. Preservar saídas de comandos ou inspeções junto ao relatório de aceite.

## Contratos Globais <!-- wop:section global_contracts -->

- Todos os arquivos usam UTF-8 e finais de linha LF.
- Evidências identificam verificação, resultado real, ator e caminho do artefato.

## Sequência de Ondas <!-- wop:section wave_sequence -->

1. W001 define contrato e inventário em paralelo.
2. W002 cria o manifesto a partir das saídas aprovadas de W001.
3. W003 verifica o pacote e produz evidência final de aceite.

## Mapa de Dependências <!-- wop:section dependency_map -->

I001 e I002 são independentes em W001. W002 depende das saídas aprovadas de W001. W003 depende da saída e das evidências aprovadas de W002.

## Rastreabilidade de Requisitos <!-- wop:section requirement_traceability -->

| Requisito | Itens | Saídas | Verificação |
|---|---|---|---|
| R001 | I001, I002 | contrato.md, inventario.md | revisão e completude |
| R002 | I003 | manifesto.md | conformidade e cobertura |
| R003 | I004 | relatorio-de-aceite.md | resultados ponta a ponta e decisão |

## Estratégia de Verificação <!-- wop:section verification_strategy -->

Revisar cada saída, avaliar cada gate com evidência real e então inspecionar rastreabilidade e conformidade ponta a ponta.

## Rollback e Recuperação <!-- wop:section rollback_recovery -->

Após falha de escrita ou verificação, preservar o último artefato aceito, isolar o candidato, registrar caminhos e resultados e não liberar a próxima onda.

## Aceite Final <!-- wop:section final_acceptance -->

R001-R003 estão satisfeitos, todos os gates passaram, o relatório referencia evidência real e a pessoa responsável registrou uma decisão.

## Protocolo de Execução <!-- wop:section execution_protocol -->

Execute somente a onda atribuída. Respeite os limites de propriedade e a barreira estrita entre ondas. Não libere uma sucessora apenas pela existência de arquivos; verifique evidências e o gate predecessor. Reporte desvios e nunca declare aceite sem evidência produzida.

## Decisão de Compatibilidade <!-- wop:section compatibility_decision -->

Preservar os nomes existentes dos campos de evidência para manter compatibilidade com as ferramentas de release.
