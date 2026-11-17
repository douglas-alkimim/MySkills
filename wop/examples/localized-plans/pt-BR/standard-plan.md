---
plan_id: <uuid>
title: <Título do plano>
version: 1
language: pt-BR
complexity: standard
plan_status: draft
execution_status: not_started
acceptance_status: not_evaluated
created_at: <iso-8601-com-offset>
updated_at: <iso-8601-com-offset>
---

# <Título do plano>

## Resultado <!-- wop:section outcome -->

<Resultado final verificável.>

## Contexto de Execução <!-- wop:section execution_context -->

<Estado atual, ambiente e fatos necessários.>

## Fatos Confirmados <!-- wop:section confirmed_facts -->

- <Fato com fonte.>

## Escopo <!-- wop:section scope -->

<Incluído e excluído.>

## Partes Interessadas e Autoridade <!-- wop:section stakeholders -->

<Responsáveis, aprovadores e limites de decisão.>

## Premissas <!-- wop:section assumptions -->

- <Premissa explícita.>

## Incertezas <!-- wop:section unknowns -->

<Nenhuma, ou descoberta delimitada e regra de bloqueio.>

## Requisitos <!-- wop:section requirements -->

- R001: <Requisito verificável.>

## Restrições <!-- wop:section constraints -->

- <Restrição.>

## Decisões <!-- wop:section decisions -->

- <Decisão confirmada.>

## Riscos <!-- wop:section risks -->

- <Risco, prevenção, detecção e resposta.>

## Ambientes e Operações <!-- wop:section operations -->

<Ambientes, acesso, observabilidade e operação segura.>

## Contratos Globais <!-- wop:section global_contracts -->

- <Interface, formato ou regra congelada.>

## Sequência de Ondas <!-- wop:section wave_sequence -->

1. W001: <objetivo>.
2. W002: <objetivo, após aprovação de W001>.

## Onda W001 — <Nome> <!-- wop:wave W001 -->

### Objetivo Geral <!-- wop:field general_objective -->

<Resultado delimitado da onda.>

### Pré-requisitos <!-- wop:field prerequisites -->

Nenhuma onda predecessora.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R001

### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- <Critério mensurável.>

### Gate de Conclusão <!-- wop:field completion_gate -->

<Todos os itens aceitos, integrados e comprovados.>

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

<Resultados reais a reter.>

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

<Prove independência entre itens da onda.>

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

<Arquivos, artefatos, sistemas e efeitos exclusivos.>

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I001 em W001. Respeite o paralelismo, a propriedade e as restrições declaradas; não inicie uma onda posterior.

### Integração e Handoff <!-- wop:field integration_handoff -->

<Integração, saída e evidência para W002.>

#### Item I001 — <Nome> <!-- wop:item I001 -->

##### Objetivo <!-- wop:field objective -->

<Um resultado delimitado.>

##### Contexto <!-- wop:field context -->

<Fatos e contratos necessários.>

##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->

<Entradas e gates.>

##### Escopo <!-- wop:field scope -->

<Trabalho incluído e excluído.>

##### Responsabilidade <!-- wop:field ownership -->

<Escopo exclusivo.>

##### Saídas <!-- wop:field outputs -->

- <Artefato ou decisão.>

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- <Critério mensurável.>

##### Restrições <!-- wop:field restrictions -->

- Não iniciar uma onda posterior.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

<Procedimento, resultado real e local da evidência.>

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

<Informações e artefatos para integração.>

## Onda W002 — <Nome> <!-- wop:wave W002 -->

### Objetivo Geral <!-- wop:field general_objective -->

<Resultado delimitado da onda.>

### Pré-requisitos <!-- wop:field prerequisites -->

W001, suas saídas, evidências, critérios e gate devem estar aprovados.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R001

### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- <Critério mensurável.>

### Gate de Conclusão <!-- wop:field completion_gate -->

<Todos os itens aceitos, integrados e comprovados.>

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

<Resultados reais a reter.>

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

<Prove independência entre itens da onda.>

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

<Arquivos, artefatos, sistemas e efeitos exclusivos.>

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I002 em W002 após verificar a predecessora. Respeite a propriedade, as saídas e as restrições; não inicie uma onda posterior.

### Integração e Handoff <!-- wop:field integration_handoff -->

<Integração, saída e evidência finais.>

#### Item I002 — <Nome> <!-- wop:item I002 -->

##### Objetivo <!-- wop:field objective -->

<Um resultado delimitado.>

##### Contexto <!-- wop:field context -->

<Fatos e contratos necessários.>

##### Entradas e Pré-requisitos <!-- wop:field inputs_prerequisites -->

<Saídas e evidências aprovadas de W001.>

##### Escopo <!-- wop:field scope -->

<Trabalho incluído e excluído.>

##### Responsabilidade <!-- wop:field ownership -->

<Escopo exclusivo.>

##### Saídas <!-- wop:field outputs -->

- <Artefato ou decisão.>

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- <Critério mensurável.>

##### Restrições <!-- wop:field restrictions -->

- Não iniciar uma onda posterior.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

<Procedimento, resultado real e local da evidência.>

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

<Informações e artefatos para integração.>

## Rastreabilidade de Requisitos <!-- wop:section requirement_traceability -->

| Requisito | Itens responsáveis | Saídas | Evidência |
|---|---|---|---|
| R001 | I001 | <saída> | <evidência> |

## Mapa de Dependências <!-- wop:section dependency_map -->

W001 precede W002. Registre dependências e interferências entre itens.

## Estratégia de Verificação <!-- wop:section verification_strategy -->

<Verificações por item, onda e ponta a ponta.>

## Rollback e Recuperação <!-- wop:section rollback_recovery -->

<Gatilhos, estado seguro e evidência de recuperação.>

## Aceite Final <!-- wop:section final_acceptance -->

<Critérios finais, evidências produzidas e aprovador.>

## Protocolo de Execução <!-- wop:section execution_protocol -->

Identifique o pacote e leia `README.md` e todos os prompts de onda referenciados. Execute as ondas em ordem estrita, integre os resultados e libere a próxima somente após o gate de conclusão ser aprovado com evidências. Ao final, realize o aceite final.

## Histórico de Revisões <!-- wop:section revision_history -->

- Versão 1: plano inicial.
