---
plan_id: 22222222-2222-4222-8222-222222222222
title: Pipeline de Evidências de Release
version: 1
language: pt-BR
complexity: standard
plan_status: ready
execution_status: not_started
acceptance_status: not_evaluated
created_at: 2026-04-01T10:00:00-03:00
updated_at: 2026-04-01T10:00:00-03:00
---

# Pipeline de Evidências de Release

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

## Premissas <!-- wop:section assumptions -->

- O workspace de execução permite escrita.

## Incertezas <!-- wop:section unknowns -->

Nenhuma. Uma nova incerteza material bloqueia o trabalho afetado e exige revisão do plano ou descoberta delimitada.

## Requisitos <!-- wop:section requirements -->

- R001: Definir o contrato de evidências da release.
- R002: Produzir um manifesto conforme o contrato.
- R003: Verificar o manifesto e reter resultados reais.

## Restrições <!-- wop:section constraints -->

- Não iniciar uma onda antes da aprovação do gate predecessor.
- Não declarar evidências que não foram produzidas.

## Decisões <!-- wop:section decisions -->

- Markdown é o formato portátil de evidência deste exemplo.

## Riscos <!-- wop:section risks -->

- Deriva de contrato: congelar o handoff de W001 e parar W002 se ele mudar.
- Geração parcial: preservar o último artefato aceito e reportar a verificação que falhou.

## Ambientes e Operações <!-- wop:section operations -->

Executar em workspace descartável. Preservar saídas de comandos ou inspeções junto ao relatório de aceite.

## Contratos Globais <!-- wop:section global_contracts -->

- Todos os arquivos usam UTF-8 e finais de linha LF.
- Evidências identificam verificação, resultado real, ator e caminho do artefato.

## Decisão de Compatibilidade <!-- wop:section compatibility_decision -->

Preservar os nomes existentes dos campos de evidência para manter compatibilidade com as ferramentas de release.

## Notas de Construção do Manifesto <!-- wop:section manifest_construction scope=wave waves=W002 -->

Construir o manifesto somente a partir do contrato e do inventário congelados e aceitos no gate de W001.

## Restrições do Relatório Final <!-- wop:section final_report_restrictions scope=item items=I004 -->

O relatório final pode referenciar artefatos predecessores, mas não pode modificá-los.

## Sequência de Ondas <!-- wop:section wave_sequence -->

1. W001 define contrato e inventário em paralelo.
2. W002 cria o manifesto a partir das saídas aprovadas de W001.
3. W003 verifica o pacote e produz evidência final de aceite.

## Onda W001 — Descoberta do Contrato <!-- wop:wave W001 -->

### Objetivo Geral <!-- wop:field general_objective -->

Congelar o contrato e o inventário de evidências da release.

### Pré-requisitos <!-- wop:field prerequisites -->

Nenhuma onda predecessora.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R001

### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- Contrato e inventário estão completos, consistentes e revisáveis.

### Gate de Conclusão <!-- wop:field completion_gate -->

I001 e I002 estão aceitos com evidência e suas saídas não conflitam.

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

Reter resultados da revisão do contrato e da completude do inventário.

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

I001 escreve contrato.md e I002 escreve inventario.md; nenhum consome ou altera a saída do outro.

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

I001 possui contrato.md. I002 possui inventario.md.

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I001 e I002 em W001, em paralelo sob limites exclusivos de propriedade, e integre os dois resultados no gate.

### Integração e Handoff <!-- wop:field integration_handoff -->

Publicar contrato.md, inventario.md, suas evidências e o gate aprovado de W001 para W002.

#### Item I001 — Definir Contrato <!-- wop:item I001 -->

##### Objetivo <!-- wop:field objective -->

Definir os campos obrigatórios de evidência da release.

##### Contexto <!-- wop:field context -->

O manifesto precisa ser portátil e auditável.

##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->

Usar R001 e os contratos globais.

##### Escopo <!-- wop:field scope -->

Criar somente contrato.md.

##### Responsabilidade <!-- wop:field ownership -->

Propriedade exclusiva de contrato.md.

##### Saídas <!-- wop:field outputs -->

- contrato.md

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- Cada campo obrigatório possui definição e regra de validação.

##### Restrições <!-- wop:field restrictions -->

- Não alterar inventario.md nem iniciar W002.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Registrar resultado de revisão campo a campo.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Publicar contrato.md e a evidência de revisão.

#### Item I002 — Inventariar Evidências <!-- wop:item I002 -->

##### Objetivo <!-- wop:field objective -->

Inventariar as fontes esperadas de evidência.

##### Contexto <!-- wop:field context -->

O inventário é entrada da geração do manifesto.

##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->

Usar R001 e o escopo declarado.

##### Escopo <!-- wop:field scope -->

Criar somente inventario.md.

##### Responsabilidade <!-- wop:field ownership -->

Propriedade exclusiva de inventario.md.

##### Saídas <!-- wop:field outputs -->

- inventario.md

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- Cada fonte no escopo possui responsável e local esperado.

##### Restrições <!-- wop:field restrictions -->

- Não alterar contrato.md nem iniciar W002.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Registrar inspeção de completude contra o escopo.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Publicar inventario.md e a evidência de inspeção.

## Onda W002 — Construir Manifesto <!-- wop:wave W002 -->

### Objetivo Geral <!-- wop:field general_objective -->

Criar o manifesto a partir do contrato e inventário aprovados.

### Pré-requisitos <!-- wop:field prerequisites -->

Saídas, evidências, critérios e gate de W001 devem estar aprovados.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R002

### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- O manifesto cumpre todas as regras congeladas e cobre o inventário.

### Gate de Conclusão <!-- wop:field completion_gate -->

I003 está aceito com evidência de conformidade e pronto para verificação independente.

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

Reter resultados de conformidade e cobertura do manifesto.

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

A onda possui um item porque a construção integra as duas saídas predecessoras.

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

I003 possui manifesto.md e não altera artefatos congelados de W001.

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I003 em W002 após verificar a predecessora; produza e verifique manifesto.md sem alterar as entradas congeladas.

### Integração e Handoff <!-- wop:field integration_handoff -->

Publicar manifesto.md, evidências e gate aprovado de W002 para W003.

#### Item I003 — Gerar Manifesto <!-- wop:item I003 -->

##### Objetivo <!-- wop:field objective -->

Produzir um manifesto conforme o contrato.

##### Contexto <!-- wop:field context -->

W001 define o esquema congelado e o inventário de fontes.

##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->

Exigir contrato.md, inventario.md, evidências e gate de W001 aprovados.

##### Escopo <!-- wop:field scope -->

Criar somente manifesto.md.

##### Responsabilidade <!-- wop:field ownership -->

Propriedade exclusiva de manifesto.md.

##### Saídas <!-- wop:field outputs -->

- manifesto.md

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- Cada entrada do inventário mapeia para um registro válido do manifesto.

##### Restrições <!-- wop:field restrictions -->

- Não alterar saídas de W001 nem iniciar W003.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Registrar resultados de conformidade e cobertura.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Publicar manifesto.md e os dois resultados reais.

## Onda W003 — Verificar Pacote <!-- wop:wave W003 -->

### Objetivo Geral <!-- wop:field general_objective -->

Verificar o pacote completo e produzir evidência final de aceite.

### Pré-requisitos <!-- wop:field prerequisites -->

Saída, evidências, critérios e gate de W002 devem estar aprovados.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R003

### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- Todos os requisitos são rastreáveis e a inspeção ponta a ponta passa.

### Gate de Conclusão <!-- wop:field completion_gate -->

I004 está aceito e a pessoa responsável possui evidência produzida suficiente para decidir o aceite final.

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

Reter resultados ponta a ponta e referência da decisão humana.

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

Um item concentra a verificação integrada para evitar decisões finais conflitantes.

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

I004 possui relatorio-de-aceite.md e somente lê artefatos anteriores.

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I004 em W003 após verificar a predecessora; inspecione artefatos anteriores apenas para leitura e produza relatorio-de-aceite.md.

### Integração e Handoff <!-- wop:field integration_handoff -->

Publicar relatório, referências, decisão, desvios e riscos residuais.

#### Item I004 — Verificar e Relatar <!-- wop:item I004 -->

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

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- O relatório registra cada verificação, resultado, evidência e decisão final.

##### Restrições <!-- wop:field restrictions -->

- Parar e reportar qualquer reprovação; não inventar aceite.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Reter o relatório concluído e as inspeções referenciadas.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Entregar o relatório e as referências à pessoa responsável pela release.

## Rastreabilidade de Requisitos <!-- wop:section requirement_traceability -->

| Requisito | Itens | Saídas | Verificação |
|---|---|---|---|
| R001 | I001, I002 | contrato.md, inventario.md | revisão e completude |
| R002 | I003 | manifesto.md | conformidade e cobertura |
| R003 | I004 | relatorio-de-aceite.md | resultados ponta a ponta e decisão |

## Mapa de Dependências <!-- wop:section dependency_map -->

I001 e I002 são independentes em W001. W002 depende das saídas aprovadas de W001. W003 depende da saída e das evidências aprovadas de W002.

## Estratégia de Verificação <!-- wop:section verification_strategy -->

Revisar cada saída, avaliar cada gate com evidência real e então inspecionar rastreabilidade e conformidade ponta a ponta.

## Rollback e Recuperação <!-- wop:section rollback_recovery -->

Após falha de escrita ou verificação, preservar o último artefato aceito, isolar o candidato, registrar caminhos e resultados e não liberar a próxima onda.

## Aceite Final <!-- wop:section final_acceptance -->

R001-R003 estão satisfeitos, todos os gates passaram, o relatório referencia evidência real e a pessoa responsável registrou uma decisão.

## Protocolo de Execução <!-- wop:section execution_protocol -->

Execute somente a onda atribuída. Respeite os limites de propriedade e a barreira estrita entre ondas. Não libere uma sucessora apenas pela existência de arquivos; verifique evidências e o gate predecessor. Reporte desvios e nunca declare aceite sem evidência produzida.

## Histórico de Revisões <!-- wop:section revision_history -->

- Versão 1, 2026-04-01: exemplo completo inicial em português.
