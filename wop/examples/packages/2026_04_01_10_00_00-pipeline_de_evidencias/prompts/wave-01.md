---
artifact: wop-wave-prompt
plan_id: 22222222-2222-4222-8222-222222222222
plan_version: 1
plan_title: "Pipeline de Evidências de Release"
wave_id: W001
authorized_items: "I001,I002"
non_authorized_items: "I003,I004"
predecessor_waves: none
blocked_successor_waves: "W002,W003"
language: pt-BR
source_readme: README.md
source_readme_sha256: ba3027d6cde762468105b3c8f2764a3fdd24702111be80287a7d400d4aa3a9cc
---

# Onda W001 — Descoberta do Contrato

<!-- wop:prompt-section global_protocol -->
## Protocolo de Execução <!-- wop:section execution_protocol -->

Execute somente a onda atribuída. Respeite os limites de propriedade e a barreira estrita entre ondas. Não libere uma sucessora apenas pela existência de arquivos; verifique evidências e o gate predecessor. Reporte desvios e nunca declare aceite sem evidência produzida.

<!-- wop:prompt-section execution_scope -->
<!-- wop:prompt-assigned-wave W001 -->
### Objetivo Geral <!-- wop:field general_objective -->

Congelar o contrato e o inventário de evidências da release.

### Requisitos Atendidos <!-- wop:field requirements_addressed -->

- R001

### Instruções de Execução da Onda <!-- wop:field execution_instructions -->

Execute somente I001 e I002 em W001, em paralelo sob limites exclusivos de propriedade, e integre os dois resultados no gate.

### Justificativa de Paralelismo <!-- wop:field parallelism_rationale -->

I001 escreve contrato.md e I002 escreve inventario.md; nenhum consome ou altera a saída do outro.

### Limites de Propriedade <!-- wop:field ownership_boundaries -->

I001 possui contrato.md. I002 possui inventario.md.

<!-- wop:prompt-assigned-item I001 -->
#### Item I001 — Definir Contrato

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

##### Restrições <!-- wop:field restrictions -->

- Não alterar inventario.md nem iniciar W002.

<!-- wop:prompt-assigned-item I002 -->
#### Item I002 — Inventariar Evidências

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

##### Restrições <!-- wop:field restrictions -->

- Não alterar contrato.md nem iniciar W002.

<!-- wop:prompt-section predecessor_verification -->
### Pré-requisitos <!-- wop:field prerequisites -->

Nenhuma onda predecessora.

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

<!-- wop:prompt-section completion_contract -->
### Critérios Gerais de Aceite <!-- wop:field general_acceptance_criteria -->

- Contrato e inventário estão completos, consistentes e revisáveis.

### Gate de Conclusão <!-- wop:field completion_gate -->

I001 e I002 estão aceitos com evidência e suas saídas não conflitam.

### Requisitos de Evidência <!-- wop:field evidence_requirements -->

Reter resultados da revisão do contrato e da completude do inventário.

### Integração e Handoff <!-- wop:field integration_handoff -->

Publicar contrato.md, inventario.md, suas evidências e o gate aprovado de W001 para W002.

<!-- wop:prompt-completion-item I001 -->
#### Item I001 — Definir Contrato

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- Cada campo obrigatório possui definição e regra de validação.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Registrar resultado de revisão campo a campo.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Publicar contrato.md e a evidência de revisão.

<!-- wop:prompt-completion-item I002 -->
#### Item I002 — Inventariar Evidências

##### Critérios de Aceite <!-- wop:field acceptance_criteria -->

- Cada fonte no escopo possui responsável e local esperado.

##### Evidências de Verificação <!-- wop:field verification_evidence -->

Registrar inspeção de completude contra o escopo.

##### Requisitos de Handoff <!-- wop:field handoff_requirements -->

Publicar inventario.md e a evidência de inspeção.
