---
artifact: wop-wave-prompt
plan_id: 22222222-2222-4222-8222-222222222222
plan_version: 1
plan_title: "Pipeline de Evidências de Release"
wave_id: W003
authorized_items: I004
non_authorized_items: "I001,I002,I003"
predecessor_waves: W002
blocked_successor_waves: none
language: pt-BR
source_readme: README.md
source_readme_sha256: ba3027d6cde762468105b3c8f2764a3fdd24702111be80287a7d400d4aa3a9cc
---

# Onda W003 — Verificar Pacote

<!-- wop:prompt-section global_protocol -->
## Protocolo de Execução <!-- wop:section execution_protocol -->

Execute somente a onda atribuída. Respeite os limites de propriedade e a barreira estrita entre ondas. Não libere uma sucessora apenas pela existência de arquivos; verifique evidências e o gate predecessor. Reporte desvios e nunca declare aceite sem evidência produzida.

<!-- wop:prompt-section execution_scope -->
<!-- wop:prompt-assigned-wave W003 -->
### Objetivo Geral <!-- wop:field general_objective -->

Verificar o pacote completo e produzir evidência final de aceite.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R003

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I004 em W003 após verificar a predecessora; inspecione artefatos anteriores apenas para leitura e produza relatorio-de-aceite.md.

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

Um item concentra a verificação integrada para evitar decisões finais conflitantes.

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

I004 possui relatorio-de-aceite.md e somente lê artefatos anteriores.

<!-- wop:prompt-assigned-item I004 -->
#### Item I004 — Verificar e Relatar

##### Objetivo <!-- wop:field objective -->

Verificar o pacote e documentar o resultado real.

##### Contexto <!-- wop:field context -->

O aceite final não pode ser inferido de evidência apenas planejada.

##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->

Exigir manifesto.md e evidências de conformidade de W002 aprovados.

##### Escopo <!-- wop:field scope -->

Criar relatorio-de-aceite.md sem reparar predecessoras silenciosamente.

##### Responsabilidade <!-- wop:field ownership -->

Propriedade exclusiva de relatorio-de-aceite.md.

##### Saídas <!-- wop:field outputs -->

- relatorio-de-aceite.md

##### Restrições <!-- wop:field restrictions -->

- Parar e reportar qualquer reprovação; não inventar aceite.

<!-- wop:prompt-section predecessor_verification -->
### Pré-requisitos <!-- wop:field prerequisites -->

Saída, evidências, critérios e gate de W002 devem estar aprovados.

<!-- wop:prompt-predecessor W002 -->
## Onda W002 — Construir Manifesto

### Objetivo Geral <!-- wop:field general_objective -->

Criar o manifesto a partir do contrato e inventário aprovados.

### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- O manifesto cumpre todas as regras congeladas e cobre o inventário.

### Gate de Conclusão <!-- wop:field completion_gate -->

I003 está aceito com evidência de conformidade e pronto para verificação independente.

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

Reter resultados de conformidade e cobertura do manifesto.

### Integração e Handoff <!-- wop:field integration_handoff -->

Publicar manifesto.md, evidências e gate aprovado de W002 para W003.

<!-- wop:prompt-predecessor-item I003 -->
#### Item I003 — Gerar Manifesto

##### Saídas <!-- wop:field outputs -->

- manifesto.md

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- Cada entrada do inventário mapeia para um registro válido do manifesto.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Registrar resultados de conformidade e cobertura.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Publicar manifesto.md e os dois resultados reais.

<!-- wop:prompt-section shared_context -->
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

## Decisão de Compatibilidade <!-- wop:section compatibility_decision -->

Preservar os nomes existentes dos campos de evidência para manter compatibilidade com as ferramentas de release.

## Restrições do Relatório Final <!-- wop:section final_report_restrictions scope=item items=I004 -->

O relatório final pode referenciar artefatos predecessores, mas não pode modificá-los.

<!-- wop:prompt-section completion_contract -->
### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- Todos os requisitos são rastreáveis e a inspeção ponta a ponta passa.

### Gate de Conclusão <!-- wop:field completion_gate -->

I004 está aceito e a pessoa responsável possui evidência produzida suficiente para decidir o aceite final.

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

Reter resultados ponta a ponta e referência da decisão humana.

### Integração e Handoff <!-- wop:field integration_handoff -->

Publicar relatório, referências, decisão, desvios e riscos residuais.

<!-- wop:prompt-completion-item I004 -->
#### Item I004 — Verificar e Relatar

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- O relatório registra cada verificação, resultado, evidência e decisão final.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Reter o relatório concluído e as inspeções referenciadas.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Entregar o relatório e as referências à pessoa responsável pela release.
