---
plan_id: <uuid>
title: <Título del plan>
version: 1
language: es
complexity: standard
plan_status: draft
execution_status: not_started
acceptance_status: not_evaluated
created_at: <iso-8601-con-zona>
updated_at: <iso-8601-con-zona>
---

# <Título del plan>

## Resultado Esperado <!-- wop:section outcome -->

<Resultado final verificable.>

## Contexto de Ejecución <!-- wop:section execution_context -->

<Estado actual, entorno y hechos necesarios.>

## Hechos Confirmados <!-- wop:section confirmed_facts -->

- <Hecho con fuente.>

## Alcance <!-- wop:section scope -->

<Incluido y excluido.>

## Interesados y Autoridad <!-- wop:section stakeholders -->

<Responsables, aprobadores y límites de decisión.>

## Supuestos <!-- wop:section assumptions -->

- <Supuesto explícito.>

## Incógnitas <!-- wop:section unknowns -->

<Ninguna, o descubrimiento acotado y regla de bloqueo.>

## Requisitos <!-- wop:section requirements -->

- R001: <Requisito verificable.>

## Restricciones <!-- wop:section constraints -->

- <Restricción.>

## Decisiones <!-- wop:section decisions -->

- <Decisión confirmada.>

## Riesgos <!-- wop:section risks -->

- <Riesgo, prevención, detección y respuesta.>

## Entornos y Operaciones <!-- wop:section operations -->

<Entornos, acceso, observabilidad y operación segura.>

## Contratos Globales <!-- wop:section global_contracts -->

- <Interfaz, formato o regla congelada.>

## Secuencia de Olas <!-- wop:section wave_sequence -->

1. W001: <objetivo>.
2. W002: <objetivo, después de aprobar W001>.

## Ola W001 — <Nombre> <!-- wop:wave W001 -->

### Objetivo General <!-- wop:field general_objective -->

<Resultado acotado de la ola.>

### Prerrequisitos <!-- wop:field prerequisites -->

Ninguna ola predecesora.

### Requisitos Abordados <!-- wop:field requirements_addressed -->

- R001

### Criterios Generales de Aceptación <!-- wop:field general_acceptance_criteria -->

- <Criterio medible.>

### Puerta de Finalización <!-- wop:field completion_gate -->

<Todos los ítems aceptados, integrados y demostrados.>

### Requisitos de Evidencia <!-- wop:field evidence_requirements -->

<Resultados reales que se deben conservar.>

### Justificación de Paralelismo <!-- wop:field parallelism_rationale -->

<Demuestre independencia entre ítems de la ola.>

### Límites de Propiedad <!-- wop:field ownership_boundaries -->

<Archivos, artefactos, sistemas y efectos exclusivos.>

### Instrucciones de Ejecución de la Ola <!-- wop:field execution_instructions -->

Ejecute solamente I001 en W001. Respete el paralelismo, la propiedad y las restricciones declaradas; no inicie una ola posterior.

### Integración y Transferencia <!-- wop:field integration_handoff -->

<Integración, resultado y evidencia para W002.>

#### Ítem I001 — <Nombre> <!-- wop:item I001 -->

##### Objetivo <!-- wop:field objective -->

<Un resultado acotado.>

##### Contexto <!-- wop:field context -->

<Hechos y contratos necesarios.>

##### Insumos y Prerrequisitos <!-- wop:field inputs_prerequisites -->

<Insumos y puertas.>

##### Alcance <!-- wop:field scope -->

<Trabajo incluido y excluido.>

##### Responsabilidad <!-- wop:field ownership -->

<Ámbito exclusivo.>

##### Resultados <!-- wop:field outputs -->

- <Artefacto o decisión.>

##### Criterios de Aceptación <!-- wop:field acceptance_criteria -->

- <Criterio medible.>

##### Restricciones <!-- wop:field restrictions -->

- No iniciar una ola posterior.

##### Evidencia de Verificación <!-- wop:field verification_evidence -->

<Procedimiento, resultado real y ubicación de la evidencia.>

##### Requisitos de Transferencia <!-- wop:field handoff_requirements -->

<Información y artefactos para integración.>

## Ola W002 — <Nombre> <!-- wop:wave W002 -->

### Objetivo General <!-- wop:field general_objective -->

<Resultado acotado de la ola.>

### Prerrequisitos <!-- wop:field prerequisites -->

W001, sus resultados, evidencias, criterios y puerta deben estar aprobados.

### Requisitos Abordados <!-- wop:field requirements_addressed -->

- R001

### Criterios Generales de Aceptación <!-- wop:field general_acceptance_criteria -->

- <Criterio medible.>

### Puerta de Finalización <!-- wop:field completion_gate -->

<Todos los ítems aceptados, integrados y demostrados.>

### Requisitos de Evidencia <!-- wop:field evidence_requirements -->

<Resultados reales que se deben conservar.>

### Justificación de Paralelismo <!-- wop:field parallelism_rationale -->

<Demuestre independencia entre ítems de la ola.>

### Límites de Propiedad <!-- wop:field ownership_boundaries -->

<Archivos, artefactos, sistemas y efectos exclusivos.>

### Instrucciones de Ejecución de la Ola <!-- wop:field execution_instructions -->

Ejecute solamente I002 en W002 después de verificar la predecesora. Respete la propiedad, los resultados y las restricciones; no inicie una ola posterior.

### Integración y Transferencia <!-- wop:field integration_handoff -->

<Integración, resultado y evidencia finales.>

#### Ítem I002 — <Nombre> <!-- wop:item I002 -->

##### Objetivo <!-- wop:field objective -->

<Un resultado acotado.>

##### Contexto <!-- wop:field context -->

<Hechos y contratos necesarios.>

##### Insumos y Prerrequisitos <!-- wop:field inputs_prerequisites -->

<Resultados y evidencias aprobados de W001.>

##### Alcance <!-- wop:field scope -->

<Trabajo incluido y excluido.>

##### Responsabilidad <!-- wop:field ownership -->

<Ámbito exclusivo.>

##### Resultados <!-- wop:field outputs -->

- <Artefacto o decisión.>

##### Criterios de Aceptación <!-- wop:field acceptance_criteria -->

- <Criterio medible.>

##### Restricciones <!-- wop:field restrictions -->

- No iniciar una ola posterior.

##### Evidencia de Verificación <!-- wop:field verification_evidence -->

<Procedimiento, resultado real y ubicación de la evidencia.>

##### Requisitos de Transferencia <!-- wop:field handoff_requirements -->

<Información y artefactos para integración.>

## Trazabilidad de Requisitos <!-- wop:section requirement_traceability -->

| Requisito | Ítems responsables | Resultados | Evidencia |
|---|---|---|---|
| R001 | I001 | <resultado> | <evidencia> |

## Mapa de Dependencias <!-- wop:section dependency_map -->

W001 precede W002. Registre dependencias e interferencias entre ítems.

## Estrategia de Verificación <!-- wop:section verification_strategy -->

<Verificaciones por ítem, ola y extremo a extremo.>

## Rollback y Recuperación <!-- wop:section rollback_recovery -->

<Disparadores, estado seguro y evidencia de recuperación.>

## Aceptación Final <!-- wop:section final_acceptance -->

<Criterios finales, evidencias producidas y aprobador.>

## Protocolo de Ejecución <!-- wop:section execution_protocol -->

Identifique el paquete y lea `README.md` y todos los prompts de ola referenciados. Ejecute las olas en orden estricto, integre los resultados y libere la siguiente solo después de aprobar la puerta de finalización con evidencias. Al terminar, realice la aceptación final.

## Historial de Revisiones <!-- wop:section revision_history -->

- Versión 1: plan inicial.
