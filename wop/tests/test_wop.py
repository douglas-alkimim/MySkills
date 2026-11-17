"""End-to-end tests for the WOP workspace, database, prompts, and lifecycle."""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import uuid
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_plan  # noqa: E402
import plan_model  # noqa: E402
import wop_db  # noqa: E402


def write_utf8(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def render_template_package(
    root: Path, template_path: Path, package_name: str
) -> Path:
    template = template_path.read_text(encoding="utf-8")
    iso = datetime.now().astimezone().isoformat(timespec="seconds")
    rendered_lines = []
    for line in template.splitlines():
        if line.startswith("plan_id:"):
            line = "plan_id: {0}".format(uuid.uuid4())
        elif line.startswith("language:") and "<" in line:
            line = "language: en"
        elif line.startswith("created_at:"):
            line = "created_at: {0}".format(iso)
        elif line.startswith("updated_at:"):
            line = "updated_at: {0}".format(iso)
        rendered_lines.append(line)
    package = root / ".wop" / "plans" / package_name
    package.mkdir()
    write_utf8(package / "README.md", "\n".join(rendered_lines) + "\n")
    validate_plan.generate_prompts(package)
    return package


def item(item_id: str, name: str, output: str) -> str:
    return f"""#### Item {item_id} — {name}

##### Objective

Produce {output}.

##### Context

This item contributes a bounded artifact to the current wave.

##### Inputs and Prerequisites

Use the frozen contracts and accepted predecessor evidence.

##### Scope

Create and verify only {output}.

##### Ownership

Own {output}; do not edit another item owner’s artifact.

##### Outputs

- {output}

##### Acceptance Criteria

- The output exists and contains its required contract.
- Verification evidence is recorded.

##### Restrictions

- Do not start a later wave.
- Do not change frozen contracts.

##### Verification Evidence

Record the inspection or command result that proves the output.

##### Handoff Requirements

Publish the output location and verification evidence.
"""


def wave(
    wave_id: str,
    name: str,
    predecessor: str,
    items: list[str],
    criterion: str,
) -> str:
    assigned_ids = re.findall(r"#### Item (I\d{3})", "\n".join(items))
    execution_instruction = (
        "Execute only {0} in {1}; apply the declared parallelism, ownership, "
        "outputs, and restrictions without starting a later wave."
    ).format(" and ".join(assigned_ids), wave_id)
    return f"""## Wave {wave_id} — {name}

### General Objective

Complete the bounded work for {name}.

### Prerequisites

{predecessor}

### Requirements Addressed

- R001

### General Acceptance Criteria

- {criterion}
- All item criteria pass with recorded evidence.

### Completion Gate

Every item is complete, accepted, integrated where needed, and the general criteria pass.

### Evidence Requirements

Retain item checks and a wave gate decision.

### Parallelism Rationale

Items own different files and share no mutable resource.

### Ownership Boundaries

Each item may change only its named output.

### Wave Execution Instructions

{execution_instruction}

### Integration and Handoff

Collect outputs and gate evidence for the next wave.

{chr(10).join(items)}
"""


def create_package(
    root: Path,
    plan_id: Optional[str] = None,
    name: str = "representative_plan",
    timestamp: str = "2026_01_02_03_04_05",
) -> tuple[Path, str]:
    plan_id = plan_id or str(uuid.uuid4())
    package = root / ".wop" / "plans" / f"{timestamp}-{name}"
    package.mkdir(parents=True)
    iso = datetime.now().astimezone().isoformat(timespec="seconds")
    readme = f"""---
plan_id: {plan_id}
title: Representative Plan
version: 1
language: en
complexity: standard
plan_status: ready
execution_status: not_started
acceptance_status: not_evaluated
created_at: {iso}
updated_at: {iso}
---

# Representative Plan

## Outcome

Deliver a verified three-stage example.

## Execution Context

The test project is local and uses UTF-8 Markdown artifacts.

## Confirmed Facts

- The project root exists.
- Three sequential waves are required.

## Scope

Create discovery, implementation, and verification artifacts.

## Assumptions

- The local filesystem is writable.

## Unknowns

None. New unknowns become blockers or explicit discovery work.

## Requirements

- R001: Produce and verify the three-stage deliverable.

## Constraints

- Preserve the strict wave barrier.

## Decisions

- Markdown is authoritative.

## Global Contracts

- All artifacts are UTF-8.
- Evidence must identify the check and result.

## Wave Sequence

1. W001 discovers the contract.
2. W002 implements the contract after W001 passes.
3. W003 verifies the result after W002 passes.

{wave("W001", "Discovery", "No predecessor wave.", [item("I001", "Inspect", "contract.md"), item("I002", "Inventory", "inventory.md")], "The contract and inventory are complete.")}

{wave("W002", "Implementation", "W001 must have passed its completion gate.", [item("I003", "Build", "result.md")], "The result implements the accepted contract.")}

{wave("W003", "Verification", "W002 must have passed its completion gate.", [item("I004", "Verify", "evidence.md")], "End-to-end verification passes.")}

## Requirement Traceability

| Requirement | Responsible items | Evidence |
|---|---|---|
| R001 | I001, I002, I003, I004 | contract, inventory, result, and evidence |

## Dependency Map

W001 precedes W002; W002 precedes W003. Items I001 and I002 are independent.

## Verification Strategy

Inspect every artifact, run applicable checks, and retain actual results.

## Final Acceptance

All wave gates pass and the final evidence proves R001.

## Execution Protocol

Execute waves strictly in order. Parallelize only independent same-wave items.

## Revision History

- Version 1: Initial complete plan.
"""
    write_utf8(package / "README.md", readme)
    validate_plan.generate_prompts(package)
    return package, plan_id


def create_localized_package(root: Path, language: str) -> tuple[Path, str]:
    is_portuguese = language == "pt-BR"
    labels = {
        "title": "Plano de Entrega" if is_portuguese else "Plan de Entrega",
        "outcome": "Resultado" if is_portuguese else "Resultado Esperado",
        "context": "Contexto de Execução" if is_portuguese else "Contexto de Ejecución",
        "facts": "Fatos Confirmados" if is_portuguese else "Hechos Confirmados",
        "scope": "Escopo" if is_portuguese else "Alcance",
        "stakeholders": "Partes Interessadas" if is_portuguese else "Interesados",
        "assumptions": "Premissas" if is_portuguese else "Supuestos",
        "unknowns": "Incertezas" if is_portuguese else "Incógnitas",
        "requirements": "Requisitos",
        "constraints": "Restrições" if is_portuguese else "Restricciones",
        "decisions": "Decisões" if is_portuguese else "Decisiones",
        "risks": "Riscos" if is_portuguese else "Riesgos",
        "operations": "Ambientes e Operações" if is_portuguese else "Entornos y Operaciones",
        "contracts": "Contratos Globais" if is_portuguese else "Contratos Globales",
        "sequence": "Sequência de Ondas" if is_portuguese else "Secuencia de Olas",
        "traceability": "Rastreabilidade de Requisitos" if is_portuguese else "Trazabilidad de Requisitos",
        "dependencies": "Mapa de Dependências" if is_portuguese else "Mapa de Dependencias",
        "verification": "Estratégia de Verificação" if is_portuguese else "Estrategia de Verificación",
        "rollback": "Rollback e Recuperação" if is_portuguese else "Rollback y Recuperación",
        "final": "Aceite Final" if is_portuguese else "Aceptación Final",
        "protocol": "Protocolo de Execução" if is_portuguese else "Protocolo de Ejecución",
        "history": "Histórico de Revisões" if is_portuguese else "Historial de Revisiones",
        "wave": "Onda" if is_portuguese else "Ola",
        "general_objective": "Objetivo Geral" if is_portuguese else "Objetivo General",
        "prerequisites": "Pré-requisitos" if is_portuguese else "Prerrequisitos",
        "addressed": "Requisitos Atendidos" if is_portuguese else "Requisitos Abordados",
        "general_criteria": "Critérios Gerais de Aceite" if is_portuguese else "Criterios Generales de Aceptación",
        "gate": "Gate de Conclusão" if is_portuguese else "Puerta de Finalización",
        "evidence": "Requisitos de Evidência" if is_portuguese else "Requisitos de Evidencia",
        "parallel": "Justificativa de Paralelismo" if is_portuguese else "Justificación de Paralelismo",
        "boundaries": "Limites de Propriedade" if is_portuguese else "Límites de Propiedad",
        "integration": "Integração e Handoff" if is_portuguese else "Integración y Transferencia",
        "item": "Item" if is_portuguese else "Ítem",
        "objective": "Objetivo",
        "item_context": "Contexto",
        "inputs": "Entradas e Pré-requisitos" if is_portuguese else "Insumos y Prerrequisitos",
        "item_scope": "Escopo" if is_portuguese else "Alcance",
        "ownership": "Responsabilidade",
        "execution_instructions": "Instruções de Execução da Onda" if is_portuguese else "Instrucciones de Ejecución de la Ola",
        "outputs": "Saídas" if is_portuguese else "Resultados",
        "criteria": "Critérios de Aceite" if is_portuguese else "Criterios de Aceptación",
        "restrictions": "Restrições" if is_portuguese else "Restricciones",
        "verification_evidence": "Evidências de Verificação" if is_portuguese else "Evidencia de Verificación",
        "handoff": "Requisitos de Handoff" if is_portuguese else "Requisitos de Transferencia",
    }
    plan_id = str(uuid.uuid4())
    package = root / ".wop" / "plans" / (
        "2026_02_03_04_05_06-plano_localizado" if is_portuguese
        else "2026_02_03_04_05_07-plan_localizado"
    )
    package.mkdir(parents=True)
    iso = datetime.now().astimezone().isoformat(timespec="seconds")

    def section(identifier: str, label: str, content: str) -> str:
        return "## {0} <!-- wop:section {1} -->\n\n{2}".format(label, identifier, content)

    def local_item(item_id: str, output: str) -> str:
        fields = (
            ("objective", labels["objective"], "Produzir " if is_portuguese else "Producir "),
            ("context", labels["item_context"], "Contexto delimitado." if is_portuguese else "Contexto delimitado."),
            ("inputs_prerequisites", labels["inputs"], "Contratos aprovados." if is_portuguese else "Contratos aprobados."),
            ("scope", labels["item_scope"], "Somente a saída indicada." if is_portuguese else "Solo el resultado indicado."),
            ("ownership", labels["ownership"], "Propriedade exclusiva." if is_portuguese else "Propiedad exclusiva."),
            ("outputs", labels["outputs"], "- {0}".format(output)),
            ("acceptance_criteria", labels["criteria"], "- A saída foi verificada." if is_portuguese else "- El resultado fue verificado."),
            ("restrictions", labels["restrictions"], "- Não iniciar outra onda." if is_portuguese else "- No iniciar otra ola."),
            ("verification_evidence", labels["verification_evidence"], "Registrar o resultado real." if is_portuguese else "Registrar el resultado real."),
            ("handoff_requirements", labels["handoff"], "Publicar saída e evidência." if is_portuguese else "Publicar resultado y evidencia."),
        )
        rendered = []
        for field_id, label, content in fields:
            if field_id == "objective":
                content += output + "."
            rendered.append(
                "##### {0} <!-- wop:field {1} -->\n\n{2}".format(label, field_id, content)
            )
        return "#### {0} {1} <!-- wop:item {1} -->\n\n{2}".format(
            labels["item"], item_id, "\n\n".join(rendered)
        )

    def local_wave(wave_id: str, predecessor: str, item_id: str, output: str) -> str:
        fields = (
            ("general_objective", labels["general_objective"], "Entregar a etapa delimitada." if is_portuguese else "Entregar la etapa delimitada."),
            ("prerequisites", labels["prerequisites"], predecessor),
            ("requirements_addressed", labels["addressed"], "- R001"),
            ("general_acceptance_criteria", labels["general_criteria"], "- Todos os critérios passam." if is_portuguese else "- Todos los criterios pasan."),
            ("completion_gate", labels["gate"], "Itens aceitos com evidência." if is_portuguese else "Ítems aceptados con evidencia."),
            ("evidence_requirements", labels["evidence"], "Resultados verificáveis." if is_portuguese else "Resultados verificables."),
            ("parallelism_rationale", labels["parallel"], "Escopos exclusivos." if is_portuguese else "Alcances exclusivos."),
            ("ownership_boundaries", labels["boundaries"], "Cada item altera apenas sua saída." if is_portuguese else "Cada ítem modifica solo su resultado."),
            ("execution_instructions", labels["execution_instructions"], ("Executar somente {0} em {1}." if is_portuguese else "Ejecutar solamente {0} en {1}.").format(item_id, wave_id)),
            ("integration_handoff", labels["integration"], "Entregar saída e evidência à próxima onda." if is_portuguese else "Entregar resultado y evidencia a la próxima ola."),
        )
        rendered = [
            "### {0} <!-- wop:field {1} -->\n\n{2}".format(label, field_id, content)
            for field_id, label, content in fields
        ]
        return "## {0} {1} — Etapa <!-- wop:wave {1} -->\n\n{2}\n\n{3}".format(
            labels["wave"], wave_id, "\n\n".join(rendered), local_item(item_id, output)
        )

    no_predecessor = "Nenhuma onda predecessora." if is_portuguese else "Ninguna ola predecesora."
    must_pass = "W001 deve ter o gate aprovado." if is_portuguese else "W001 debe tener la puerta aprobada."
    readme = """---
plan_id: {plan_id}
title: {title}
version: 1
language: {language}
complexity: standard
plan_status: ready
execution_status: not_started
acceptance_status: not_evaluated
created_at: {iso}
updated_at: {iso}
---

# {title}

{sections}

{wave_one}

{wave_two}
""".format(
        plan_id=plan_id,
        title=labels["title"],
        language=language,
        iso=iso,
        sections="\n\n".join((
            section("outcome", labels["outcome"], "Entrega verificada."),
            section("execution_context", labels["context"], "Projeto local em UTF-8."),
            section("confirmed_facts", labels["facts"], "- O workspace existe."),
            section("scope", labels["scope"], "Criar e verificar artefatos."),
            section("stakeholders", labels["stakeholders"], "- Responsável aprova o resultado."),
            section("assumptions", labels["assumptions"], "- O filesystem está disponível."),
            section("unknowns", labels["unknowns"], "Nenhum."),
            section("requirements", labels["requirements"], "- R001: entregar o resultado."),
            section("constraints", labels["constraints"], "- Preservar a ordem das ondas."),
            section("decisions", labels["decisions"], "- Markdown é autoritativo."),
            section("risks", labels["risks"], "- Falha parcial exige rollback."),
            section("operations", labels["operations"], "- Executar em workspace temporário."),
            section("global_contracts", labels["contracts"], "- Saídas e evidências usam UTF-8."),
            section("wave_sequence", labels["sequence"], "W001 precede W002."),
            section("requirement_traceability", labels["traceability"], "R001 -> I001, I002."),
            section("dependency_map", labels["dependencies"], "W002 depende de W001."),
            section("verification_strategy", labels["verification"], "Inspecionar as saídas e registrar resultados."),
            section("rollback_recovery", labels["rollback"], "Restaurar a versão anterior e reportar a falha."),
            section("final_acceptance", labels["final"], "R001 verificado com evidência."),
            section("execution_protocol", labels["protocol"], "Executar ondas em ordem estrita."),
            section("revision_history", labels["history"], "- Versão 1: plano inicial."),
        )),
        wave_one=local_wave("W001", no_predecessor, "I001", "contrato.md"),
        wave_two=local_wave("W002", must_pass, "I002", "evidencia.md"),
    )
    write_utf8(package / "README.md", readme)
    validate_plan.generate_prompts(package)
    return package, plan_id


UNIVERSAL_LANGUAGE_CASES = {
    "pt-BR": {
        "slug": "plano_universal", "title": "Plano Universal",
        "section": "Seção", "wave": "Onda", "item": "Item", "field": "Campo",
        "outcome": "Entregar um resultado verificado e rastreável.",
        "requirement": "Produzir o artefato e comprovar o resultado.",
        "criterion": "O resultado atende ao requisito e possui evidência real.",
        "instruction": "Leia o README, execute as ondas em ordem, valide cada gate e pare diante de falhas.",
        "no_predecessor": "Nenhuma onda predecessora é necessária.",
        "predecessor": "W001, suas saídas, evidências, critérios e gate devem estar aprovados.",
        "handoff": "Publique as saídas, os resultados reais e as evidências para a próxima onda.",
        "detail": "Preserve o escopo, os contratos e os identificadores técnicos.",
        "history": "Versão inicial do plano.",
    },
    "en": {
        "slug": "universal_plan", "title": "Universal Plan",
        "section": "Section", "wave": "Wave", "item": "Item", "field": "Field",
        "outcome": "Deliver a verified and traceable result.",
        "requirement": "Produce the artifact and prove the result.",
        "criterion": "The result satisfies the requirement and has actual evidence.",
        "instruction": "Read the README, execute waves in order, evaluate every gate, and stop on failure.",
        "no_predecessor": "No predecessor wave is required.",
        "predecessor": "W001, its outputs, evidence, criteria, and gate must be approved.",
        "handoff": "Publish outputs, actual results, and evidence for the next wave.",
        "detail": "Preserve scope, contracts, and technical identifiers.",
        "history": "Initial plan version.",
    },
    "es": {
        "slug": "plan_universal", "title": "Plan Universal",
        "section": "Sección", "wave": "Ola", "item": "Ítem", "field": "Campo",
        "outcome": "Entregar un resultado verificado y trazable.",
        "requirement": "Producir el artefacto y demostrar el resultado.",
        "criterion": "El resultado satisface el requisito y tiene evidencia real.",
        "instruction": "Lea el README, ejecute las olas en orden, evalúe cada puerta y deténgase ante fallos.",
        "no_predecessor": "No se requiere una ola predecesora.",
        "predecessor": "W001, sus resultados, evidencias, criterios y puerta deben estar aprobados.",
        "handoff": "Publique resultados, comprobaciones reales y evidencias para la siguiente ola.",
        "detail": "Conserve el alcance, los contratos y los identificadores técnicos.",
        "history": "Versión inicial del plan.",
    },
    "fr": {
        "slug": "plan_universel", "title": "Plan Universel",
        "section": "Section", "wave": "Vague", "item": "Élément", "field": "Champ",
        "outcome": "Livrer un résultat vérifié et traçable.",
        "requirement": "Produire l’artefact et démontrer le résultat.",
        "criterion": "Le résultat satisfait l’exigence et possède une preuve réelle.",
        "instruction": "Lisez le README, exécutez les vagues dans l’ordre, évaluez chaque porte et arrêtez-vous en cas d’échec.",
        "no_predecessor": "Aucune vague précédente n’est requise.",
        "predecessor": "W001, ses sorties, preuves, critères et sa porte doivent être approuvés.",
        "handoff": "Publiez les sorties, les résultats réels et les preuves pour la vague suivante.",
        "detail": "Préservez la portée, les contrats et les identifiants techniques.",
        "history": "Version initiale du plan.",
    },
    "de": {
        "slug": "universeller_plan", "title": "Universeller Plan",
        "section": "Abschnitt", "wave": "Welle", "item": "Element", "field": "Feld",
        "outcome": "Ein geprüftes und rückverfolgbares Ergebnis liefern.",
        "requirement": "Das Artefakt erstellen und das Ergebnis nachweisen.",
        "criterion": "Das Ergebnis erfüllt die Anforderung und besitzt echte Nachweise.",
        "instruction": "Lesen Sie die README, führen Sie die Wellen der Reihe nach aus, prüfen Sie jedes Gate und stoppen Sie bei Fehlern.",
        "no_predecessor": "Keine vorherige Welle ist erforderlich.",
        "predecessor": "W001 sowie Ausgaben, Nachweise, Kriterien und Gate müssen genehmigt sein.",
        "handoff": "Veröffentlichen Sie Ausgaben, tatsächliche Ergebnisse und Nachweise für die nächste Welle.",
        "detail": "Umfang, Verträge und technische Bezeichner bleiben erhalten.",
        "history": "Erste Version des Plans.",
    },
    "ja": {
        "slug": "universal_plan_ja", "title": "汎用計画",
        "section": "セクション", "wave": "ウェーブ", "item": "項目", "field": "フィールド",
        "outcome": "検証可能で追跡可能な成果を提供する。",
        "requirement": "成果物を作成し、結果を証明する。",
        "criterion": "結果が要件を満たし、実際の証拠が記録されている。",
        "instruction": "READMEを読み、ウェーブを順番に実行し、各ゲートを評価し、失敗時には停止する。",
        "no_predecessor": "先行ウェーブは不要である。",
        "predecessor": "W001の出力、証拠、基準、ゲートが承認されていること。",
        "handoff": "出力、実際の結果、証拠を次のウェーブへ引き渡す。",
        "detail": "スコープ、契約、技術識別子を維持する。",
        "history": "計画の初版。",
    },
    "zh-CN": {
        "slug": "universal_plan_zh", "title": "通用计划",
        "section": "部分", "wave": "波次", "item": "项目", "field": "字段",
        "outcome": "交付经过验证且可追踪的结果。",
        "requirement": "生成制品并证明实际结果。",
        "criterion": "结果满足要求，并记录了真实证据。",
        "instruction": "读取README，按顺序执行各波次，评估每个门禁，并在失败时停止。",
        "no_predecessor": "不需要前置波次。",
        "predecessor": "W001的输出、证据、标准和门禁必须已获批准。",
        "handoff": "向下一波次发布输出、实际结果和证据。",
        "detail": "保持范围、契约和技术标识符不变。",
        "history": "计划的初始版本。",
    },
    "ar": {
        "slug": "universal_plan_ar", "title": "خطة شاملة",
        "section": "قسم", "wave": "موجة", "item": "عنصر", "field": "حقل",
        "outcome": "تسليم نتيجة قابلة للتحقق والتتبع.",
        "requirement": "إنتاج الأثر وإثبات النتيجة الفعلية.",
        "criterion": "تستوفي النتيجة المتطلب ولها دليل فعلي مسجل.",
        "instruction": "اقرأ README ونفذ الموجات بالترتيب وقيّم كل بوابة وتوقف عند الفشل.",
        "no_predecessor": "لا توجد موجة سابقة مطلوبة.",
        "predecessor": "يجب اعتماد مخرجات W001 وأدلتها ومعاييرها وبوابتها.",
        "handoff": "انشر المخرجات والنتائج الفعلية والأدلة للموجة التالية.",
        "detail": "حافظ على النطاق والعقود والمعرفات التقنية.",
        "history": "الإصدار الأول من الخطة.",
    },
    "eo": {
        "slug": "universala_plano", "title": "Universala Plano",
        "section": "Sekcio", "wave": "Ondo", "item": "Ero", "field": "Kampo",
        "outcome": "Liveri kontrolitan kaj spureblan rezulton.",
        "requirement": "Produkti la artefakton kaj pruvi la realan rezulton.",
        "criterion": "La rezulto plenumas la postulon kaj havas realan pruvon.",
        "instruction": "Legu README, plenumu la ondojn laŭorde, taksu ĉiun pordegon kaj haltu ĉe malsukceso.",
        "no_predecessor": "Neniu antaŭa ondo estas bezonata.",
        "predecessor": "La eligoj, pruvoj, kriterioj kaj pordego de W001 devas esti aprobitaj.",
        "handoff": "Publikigu eligojn, realajn rezultojn kaj pruvojn por la sekva ondo.",
        "detail": "Konservu la amplekson, kontraktojn kaj teknikajn identigilojn.",
        "history": "Komenca versio de la plano.",
    },
}


def render_universal_readme(
    language: str,
    fixture: dict[str, str],
    plan_id: str,
    created_at: str,
    updated_at: str,
    version: int = 1,
    extra_requirement: str = "",
) -> str:
    section_counter = {"value": 0}

    def section(identifier: str, content: str) -> str:
        section_counter["value"] += 1
        return "## {0} {1:02d} <!-- wop:section {2} -->\n\n{3}".format(
            fixture["section"], section_counter["value"], identifier, content
        )

    def item(item_id: str) -> str:
        output = "artifact-{0}.md".format(item_id.casefold())
        contents = (
            fixture["outcome"], fixture["detail"], fixture["detail"],
            fixture["detail"], fixture["detail"], "- {0}".format(output),
            "- {0}".format(fixture["criterion"]), fixture["instruction"],
            fixture["criterion"], fixture["handoff"],
        )
        field_ids = (
            "objective", "context", "inputs_prerequisites", "scope", "ownership",
            "outputs", "acceptance_criteria", "restrictions",
            "verification_evidence", "handoff_requirements",
        )
        fields = [
            "##### {0} {1:02d} <!-- wop:field {2} -->\n\n{3}".format(
                fixture["field"], index, field_id, content
            )
            for index, (field_id, content) in enumerate(
                zip(field_ids, contents), start=1
            )
        ]
        return "#### {0} {1} <!-- wop:item {1} -->\n\n{2}".format(
            fixture["item"], item_id, "\n\n".join(fields)
        )

    def wave(wave_id: str, predecessor: str, item_id: str) -> str:
        contents = (
            fixture["outcome"], predecessor, "- R001",
            "- {0}".format(fixture["criterion"]), fixture["criterion"],
            fixture["criterion"], fixture["detail"], fixture["detail"],
            "{0} {1} {2}.".format(fixture["detail"], wave_id, item_id),
            fixture["handoff"],
        )
        field_ids = (
            "general_objective", "prerequisites", "requirements_addressed",
            "general_acceptance_criteria", "completion_gate", "evidence_requirements",
            "parallelism_rationale", "ownership_boundaries",
            "execution_instructions", "integration_handoff",
        )
        fields = [
            "### {0} {1:02d} <!-- wop:field {2} -->\n\n{3}".format(
                fixture["field"], index, field_id, content
            )
            for index, (field_id, content) in enumerate(
                zip(field_ids, contents), start=1
            )
        ]
        return "## {0} {1} <!-- wop:wave {1} -->\n\n{2}\n\n{3}".format(
            fixture["wave"], wave_id, "\n\n".join(fields), item(item_id)
        )

    requirement = "- R001: {0}".format(fixture["requirement"])
    if extra_requirement:
        requirement += "\n\n" + extra_requirement
    sections = "\n\n".join((
        section("outcome", fixture["outcome"]),
        section("execution_context", fixture["detail"]),
        section("confirmed_facts", "- " + fixture["detail"]),
        section("scope", fixture["detail"]),
        section("stakeholders", fixture["detail"]),
        section("assumptions", "- " + fixture["detail"]),
        section("unknowns", fixture["detail"]),
        section("requirements", requirement),
        section("constraints", "- " + fixture["detail"]),
        section("decisions", "- " + fixture["detail"]),
        section("risks", "- " + fixture["detail"]),
        section("operations", fixture["detail"]),
        section("global_contracts", "- " + fixture["detail"]),
        section("wave_sequence", fixture["instruction"]),
        section("requirement_traceability", "R001 -> I001, I002"),
        section("dependency_map", "W001 -> W002"),
        section("verification_strategy", fixture["criterion"]),
        section("rollback_recovery", fixture["instruction"]),
        section("final_acceptance", fixture["criterion"]),
        section("execution_protocol", fixture["instruction"]),
        section("revision_history", fixture["history"]),
    ))
    return """---
plan_id: {plan_id}
title: {title}
version: {version}
language: {language}
complexity: standard
plan_status: ready
execution_status: not_started
acceptance_status: not_evaluated
created_at: {created_at}
updated_at: {updated_at}
---

# {title}

{sections}

{wave_one}

{wave_two}
""".format(
        plan_id=plan_id, title=fixture["title"], version=version,
        language=language, created_at=created_at, updated_at=updated_at,
        sections=sections,
        wave_one=wave("W001", fixture["no_predecessor"], "I001"),
        wave_two=wave("W002", fixture["predecessor"], "I002"),
    )


def create_universal_package(
    root: Path,
    language: str,
    timestamp: str,
    plan_id: Optional[str] = None,
    version: int = 1,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    extra_requirement: str = "",
) -> tuple[Path, str]:
    fixture = UNIVERSAL_LANGUAGE_CASES[language]
    plan_id = plan_id or str(uuid.uuid4())
    iso = datetime.now().astimezone().isoformat(timespec="seconds")
    package = root / ".wop" / "plans" / "{0}-{1}".format(
        timestamp, fixture["slug"]
    )
    package.mkdir(parents=True)
    write_utf8(
        package / "README.md",
        render_universal_readme(
            language, fixture, plan_id, created_at or iso, updated_at or iso,
            version, extra_requirement,
        ),
    )
    validate_plan.generate_prompts(package)
    return package, plan_id


def create_scoped_context_package(
    root: Path,
    timestamp: str = "2026_05_06_07_08_09",
    name: str = "scoped_context_plan",
) -> tuple[Path, str]:
    package, plan_id = create_package(
        root, name=name, timestamp=timestamp
    )
    readme_path = package / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    custom_sections = """## Global Architecture Note <!-- wop:section global_architecture scope=global -->

GLOBAL-CONTEXT-SENTINEL applies to every wave and the orchestrator.

## Discovery Note <!-- wop:section discovery_note scope=wave waves=W001 -->

W001-CONTEXT-SENTINEL applies only to the discovery wave.

## Delivery Note <!-- wop:section delivery_note scope=wave waves=W002,W003 -->

W23-CONTEXT-SENTINEL applies only to implementation and verification.

## Audit Item Note <!-- wop:section audit_item_note scope=item items=I004 -->

I004-CONTEXT-SENTINEL applies only to the wave containing I004.

## Conservative Default <!-- wop:section conservative_default -->

DEFAULT-GLOBAL-SENTINEL has no explicit scope and therefore applies globally.

"""
    text = text.replace("## Wave Sequence\n", custom_sections + "## Wave Sequence\n", 1)
    text = text.replace(
        "Execute only I004 in W003;",
        "Execute only I004 and I005 in W003;",
        1,
    )
    text = text.replace(
        "\n## Requirement Traceability\n",
        "\n" + item("I005", "Audit", "audit.md") + "\n## Requirement Traceability\n",
        1,
    )
    text = text.replace("I001, I002, I003, I004", "I001, I002, I003, I004, I005")
    write_utf8(readme_path, text)
    validate_plan.generate_prompts(package)
    return package, plan_id


class WopLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        wop_db.initialize(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_initialization_is_idempotent_and_schema_is_constrained(self) -> None:
        first = wop_db.initialize(self.root)
        second = wop_db.initialize(self.root)
        self.assertEqual(first["database"], second["database"])
        self.assertTrue(first["foreign_keys"])
        with closing(sqlite3.connect(first["database"])) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertTrue(
                {"plans", "plan_relations", "plan_revisions", "plan_events",
                 "plan_tombstones"}.issubset(tables)
            )
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_behavior_catalog_contains_all_twenty_three_acceptance_cases(self) -> None:
        lines = (SKILL_ROOT / "tests" / "behavior-cases.md").read_text(
            encoding="utf-8"
        ).splitlines()
        numbers = [
            int(line.split(".", 1)[0])
            for line in lines
            if "." in line and line.split(".", 1)[0].isdigit()
        ]
        self.assertEqual(numbers, list(range(1, 24)))

    def test_three_wave_prompt_generation_and_validation(self) -> None:
        package, _ = create_package(self.root)
        report = validate_plan.validate_package(package, self.root)
        self.assertTrue(report["valid"], report["errors"])
        prompts = sorted((package / "prompts").glob("wave-*.md"))
        self.assertEqual(len(prompts), 3)
        self.assertIn("W001", prompts[1].read_text(encoding="utf-8"))
        self.assertIn("W002", prompts[2].read_text(encoding="utf-8"))
        master = (package / "prompts" / "execute-all.md").read_text(encoding="utf-8")
        refs = [master.index(f"prompts/wave-{number:02d}.md") for number in (1, 2, 3)]
        self.assertEqual(refs, sorted(refs))

    def test_wave_prompts_have_exact_assignments_and_no_protocol_leakage(self) -> None:
        package, _ = create_scoped_context_package(self.root)
        report = validate_plan.validate_package(package, self.root)
        self.assertTrue(report["valid"], report["errors"])
        expected = {
            1: ("I001,I002", "I003,I004,I005", "W002,W003"),
            2: ("I003", "I001,I002,I004,I005", "W003"),
            3: ("I004,I005", "I001,I002,I003", "none"),
        }
        instructions = {
            1: "Execute only I001 and I002 in W001",
            2: "Execute only I003 in W002",
            3: "Execute only I004 and I005 in W003",
        }
        for number in (1, 2, 3):
            prompt = (package / "prompts" / "wave-{0:02d}.md".format(number))
            text = prompt.read_text(encoding="utf-8")
            metadata = validate_plan.frontmatter(text)
            self.assertEqual(metadata["authorized_items"], expected[number][0])
            self.assertEqual(metadata["non_authorized_items"], expected[number][1])
            self.assertEqual(metadata["blocked_successor_waves"], expected[number][2])
            self.assertIn(instructions[number], text)
            for other in ({1, 2, 3} - {number}):
                self.assertNotIn(instructions[other], text)
            self.assertEqual(text.count("## Execution Protocol"), 1)
            self.assertEqual(text.count("### Prerequisites"), 1)
            assigned = set(
                re.findall(r"wop:prompt-assigned-item (I\d{3})", text)
            )
            self.assertEqual(assigned, set(expected[number][0].split(",")))

    def test_custom_context_scope_propagation_is_exact(self) -> None:
        package, _ = create_scoped_context_package(
            self.root, "2026_05_06_07_08_10", "custom_context_plan"
        )
        wave_texts = {
            number: (package / "prompts" / "wave-{0:02d}.md".format(number))
            .read_text(encoding="utf-8")
            for number in (1, 2, 3)
        }
        master = (package / "prompts" / "execute-all.md").read_text(
            encoding="utf-8"
        )
        for text in list(wave_texts.values()) + [master]:
            self.assertIn("GLOBAL-CONTEXT-SENTINEL", text)
            self.assertIn("DEFAULT-GLOBAL-SENTINEL", text)
        self.assertIn("W001-CONTEXT-SENTINEL", wave_texts[1])
        self.assertNotIn("W001-CONTEXT-SENTINEL", wave_texts[2])
        self.assertNotIn("W001-CONTEXT-SENTINEL", wave_texts[3])
        self.assertNotIn("W001-CONTEXT-SENTINEL", master)
        self.assertNotIn("W23-CONTEXT-SENTINEL", wave_texts[1])
        self.assertIn("W23-CONTEXT-SENTINEL", wave_texts[2])
        self.assertIn("W23-CONTEXT-SENTINEL", wave_texts[3])
        self.assertNotIn("W23-CONTEXT-SENTINEL", master)
        self.assertNotIn("I004-CONTEXT-SENTINEL", wave_texts[1])
        self.assertNotIn("I004-CONTEXT-SENTINEL", wave_texts[2])
        self.assertIn("I004-CONTEXT-SENTINEL", wave_texts[3])
        self.assertNotIn("I004-CONTEXT-SENTINEL", master)
        report = validate_plan.validate_package(package, self.root)
        self.assertTrue(report["valid"], report["errors"])

    def test_legacy_waves_without_execution_instructions_remain_compatible(self) -> None:
        package, _ = create_package(
            self.root,
            name="legacy_wave_instructions",
            timestamp="2026_05_06_07_08_11",
        )
        readme = package / "README.md"
        legacy_text, replacements = re.subn(
            r"\n### Wave Execution Instructions\n\n.*?(?=\n### Integration and Handoff)",
            "",
            readme.read_text(encoding="utf-8"),
            flags=re.DOTALL,
        )
        self.assertEqual(replacements, 3)
        write_utf8(readme, legacy_text)
        validate_plan.generate_prompts(package)
        report = validate_plan.validate_package(package, self.root)
        self.assertTrue(report["valid"], report["errors"])
        warning_codes = [warning["code"] for warning in report["warnings"]]
        self.assertEqual(
            warning_codes.count("legacy_wave_execution_instructions"), 3
        )
        for number in (1, 2, 3):
            prompt = (package / "prompts" / "wave-{0:02d}.md".format(number))
            self.assertIn("authorized_items:", prompt.read_text(encoding="utf-8"))

    def test_deterministic_prompt_and_context_contradictions_are_rejected(self) -> None:
        mutations = (
            (
                "global_protocol",
                "Execute waves strictly in order. Parallelize only independent same-wave items.",
                "Execute only I001 and I002.",
                "global_protocol_item_assignment",
            ),
            (
                "forward_dependency",
                "W001 must have passed its completion gate.",
                "W003 must have passed its completion gate.",
                "forward_wave_dependency",
            ),
            (
                "future_instruction",
                "Execute only I001 and I002 in W001;",
                "Execute only I001 and I002 in W002;",
                "future_wave_instruction",
            ),
            (
                "ownership_conflict",
                "Each item may change only its named output.\n\n### Wave Execution Instructions\n\nExecute only I003",
                "I004 owns result.md.\n\n### Wave Execution Instructions\n\nExecute only I003",
                "wave_ownership_conflict",
            ),
            (
                "unknown_wave_scope",
                "## Wave Sequence\n",
                "## Invalid Wave Context <!-- wop:section invalid_wave scope=wave waves=W999 -->\n\nInvalid.\n\n## Wave Sequence\n",
                "custom_section_wave",
            ),
            (
                "unknown_item_scope",
                "## Wave Sequence\n",
                "## Invalid Item Context <!-- wop:section invalid_item scope=item items=I999 -->\n\nInvalid.\n\n## Wave Sequence\n",
                "custom_section_item",
            ),
        )
        for offset, (name, old, new, expected_code) in enumerate(mutations, start=20):
            with self.subTest(case=name):
                package, _ = create_package(
                    self.root,
                    name="invalid_{0}".format(name),
                    timestamp="2026_05_06_07_08_{0:02d}".format(offset),
                )
                readme = package / "README.md"
                changed = readme.read_text(encoding="utf-8")
                self.assertIn(old, changed)
                write_utf8(readme, changed.replace(old, new, 1))
                validate_plan.generate_prompts(package)
                report = validate_plan.validate_package(package, self.root)
                self.assertFalse(report["valid"])
                self.assertIn(expected_code, {error["code"] for error in report["errors"]})

        package, _ = create_package(
            self.root,
            name="foreign_prompt_item",
            timestamp="2026_05_06_07_08_30",
        )
        prompt = package / "prompts" / "wave-02.md"
        write_utf8(
            prompt,
            prompt.read_text(encoding="utf-8")
            + "\n<!-- wop:prompt-assigned-item I004 -->\n",
        )
        report = validate_plan.validate_package(package, self.root)
        self.assertFalse(report["valid"])
        self.assertIn(
            "prompt_item_assignment", {error["code"] for error in report["errors"]}
        )

    def test_readme_change_requires_and_supports_regeneration(self) -> None:
        package, _ = create_package(self.root)
        prompt = package / "prompts" / "wave-02.md"
        original = prompt.read_text(encoding="utf-8")
        readme = package / "README.md"
        changed = readme.read_text(encoding="utf-8").replace(
            "The result implements the accepted contract.",
            "The result implements and documents the accepted contract.",
        )
        write_utf8(readme, changed)
        stale_report = validate_plan.validate_package(package, self.root)
        self.assertFalse(stale_report["valid"])
        self.assertTrue(
            any(error["code"] == "prompt_metadata" for error in stale_report["errors"])
        )
        validate_plan.generate_prompts(package)
        regenerated = prompt.read_text(encoding="utf-8")
        self.assertNotEqual(original, regenerated)
        self.assertIn("implements and documents", regenerated)
        self.assertTrue(validate_plan.validate_package(package, self.root)["valid"])

    def test_register_search_get_status_rename_archive_restore_delete(self) -> None:
        package, plan_id = create_package(self.root)
        registered = wop_db.register(self.root, package)
        self.assertEqual(registered["plan_id"], plan_id)
        self.assertEqual(wop_db.get_plan(self.root, plan_id=plan_id)["title"],
                         "Representative Plan")
        self.assertEqual(wop_db.get_plan(self.root, name=package.name)["plan_id"], plan_id)
        self.assertEqual(wop_db.search(self.root, "Representative")[0]["plan_id"], plan_id)
        self.assertEqual(wop_db.search(self.root, "three-stage")[0]["plan_id"], plan_id)
        changed = wop_db.set_status(
            self.root, plan_id, "in_progress", "in_progress", "pending"
        )
        self.assertEqual(changed["execution_status"], "in_progress")

        renamed_name = "2026_01_02_03_04_06-representative_plan"
        renamed = wop_db.rename_package(
            self.root, plan_id, str(package.parent / renamed_name)
        )
        self.assertEqual(renamed["current_directory_name"], renamed_name)
        self.assertEqual(len(wop_db.history(self.root, plan_id)), 1)

        archived = wop_db.move_package(self.root, plan_id, True)
        self.assertEqual(archived["plan_status"], "archived")
        archived_path = self.root / archived["current_relative_path"]
        self.assertTrue((archived_path / "prompts" / "execute-all.md").is_file())
        restored = wop_db.move_package(self.root, plan_id, False)
        self.assertEqual(restored["plan_status"], "in_progress")
        restored_path = self.root / restored["current_relative_path"]
        self.assertTrue((restored_path / "README.md").is_file())

        deleted = wop_db.delete_plan(self.root, plan_id, True, "test deletion")
        self.assertTrue(deleted["tombstone_retained"])
        self.assertFalse(restored_path.exists())
        with wop_db.connect(self.root) as conn:
            self.assertIsNotNone(
                conn.execute(
                    "SELECT 1 FROM plan_tombstones WHERE plan_id=?", (plan_id,)
                ).fetchone()
            )
            self.assertIsNotNone(
                conn.execute(
                    "SELECT 1 FROM plan_events WHERE plan_id=? AND event_type='deleted'",
                    (plan_id,),
                ).fetchone()
            )

    def test_relationship_integrity_and_dependent_delete_guard(self) -> None:
        first, first_id = create_package(self.root, name="first_plan")
        second, second_id = create_package(
            self.root, name="second_plan", timestamp="2026_01_02_03_04_06"
        )
        wop_db.register(self.root, first)
        wop_db.register(self.root, second)
        relation = wop_db.create_relation(
            self.root, second_id, first_id, "depends_on", "Second consumes first."
        )
        self.assertEqual(relation["target_plan_id"], first_id)
        with self.assertRaises(wop_db.WopError):
            wop_db.delete_plan(self.root, first_id, True, "must fail")
        self.assertEqual(len(wop_db.relations(self.root, first_id)), 1)

    def test_rebuild_and_integrity_detection(self) -> None:
        package, plan_id = create_package(self.root)
        result = wop_db.rebuild(self.root)
        self.assertTrue(result["ok"], result["errors"])
        self.assertIn(plan_id, result["registered"])
        self.assertTrue(wop_db.check(self.root)["ok"])
        package.rename(package.with_name("2026_01_02_03_04_07-representative_plan"))
        integrity = wop_db.check(self.root)
        self.assertFalse(integrity["ok"])
        self.assertTrue(
            any(issue["code"] == "missing_package" for issue in integrity["issues"])
        )

    def test_rebuild_reports_ambiguous_duplicate_identity(self) -> None:
        plan_id = str(uuid.uuid4())
        create_package(self.root, plan_id=plan_id, name="first_copy")
        create_package(
            self.root,
            plan_id=plan_id,
            name="second_copy",
            timestamp="2026_01_02_03_04_06",
        )
        result = wop_db.rebuild(self.root)
        self.assertFalse(result["ok"])
        self.assertTrue(
            any("Ambiguous duplicate plan_id" in item["error"]
                for item in result["errors"])
        )
        with wop_db.connect(self.root) as conn:
            self.assertIsNone(
                conn.execute("SELECT 1 FROM plans WHERE plan_id=?", (plan_id,)).fetchone()
            )

    def test_json_cli_and_invalid_arguments(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        command = [
            sys.executable, str(SCRIPTS / "wop_db.py"),
            "--root", str(self.root), "--json", "get", "--id", plan_id,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["plan_id"], plan_id)
        invalid = subprocess.run(
            [
                sys.executable, str(SCRIPTS / "wop_db.py"),
                "--root", str(self.root), "--json", "delete", "--id", plan_id,
            ],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(invalid.returncode, 2)
        self.assertTrue(package.exists())

    def test_rename_collision_is_safe(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        collision = package.parent / "2026_01_02_03_04_06-representative_plan"
        collision.mkdir()
        with self.assertRaises(wop_db.WopError):
            wop_db.rename_package(self.root, plan_id, str(collision))
        self.assertTrue(package.exists())
        self.assertEqual(
            wop_db.get_plan(self.root, plan_id=plan_id)["current_directory_name"],
            package.name,
        )

    def test_rebuild_preserves_operational_states_and_reports_stale_projection(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        wop_db.set_status(
            self.root,
            plan_id,
            "accepted",
            "executed",
            "accepted",
            ["reports/final-verification.json"],
            "All final criteria passed.",
            "release-manager",
            True,
        )
        wop_db.update_frontmatter_projection(
            package,
            {
                "plan_status": "ready",
                "execution_status": "not_started",
                "acceptance_status": "not_evaluated",
            },
        )
        result = wop_db.rebuild(self.root)
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["conflicts"]), 3)
        record = wop_db.get_plan(self.root, plan_id=plan_id)
        self.assertEqual(record["plan_status"], "accepted")
        self.assertEqual(record["execution_status"], "executed")
        self.assertEqual(record["acceptance_status"], "accepted")
        self.assertEqual(len(wop_db.evidence(self.root, plan_id)), 1)

    def test_archive_restore_preserves_state_and_editorial_timestamp(self) -> None:
        package, plan_id = create_package(self.root)
        registered = wop_db.register(self.root, package)
        changed = wop_db.set_status(
            self.root, plan_id, "in_progress", "in_progress", "pending"
        )
        editorial_timestamp = changed["updated_at"]
        archived = wop_db.move_package(self.root, plan_id, True)
        self.assertEqual(archived["plan_status"], "archived")
        self.assertEqual(archived["pre_archive_plan_status"], "in_progress")
        self.assertEqual(archived["execution_status"], "in_progress")
        self.assertEqual(archived["acceptance_status"], "pending")
        self.assertEqual(archived["updated_at"], editorial_timestamp)
        archived_path = self.root / archived["current_relative_path"]
        archived_meta = wop_db.metadata_from_package(archived_path)
        self.assertEqual(archived_meta["plan_status"], "archived")
        restored = wop_db.move_package(self.root, plan_id, False)
        self.assertEqual(restored["plan_status"], "in_progress")
        self.assertEqual(restored["execution_status"], "in_progress")
        self.assertEqual(restored["acceptance_status"], "pending")
        self.assertEqual(restored["updated_at"], editorial_timestamp)
        restored_path = self.root / restored["current_relative_path"]
        restored_meta = wop_db.metadata_from_package(restored_path)
        self.assertEqual(restored_meta["plan_status"], "in_progress")
        self.assertTrue(wop_db.check(self.root)["ok"])
        self.assertEqual(registered["created_at"], restored["created_at"])

    def test_completion_and_acceptance_require_evidence(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        with self.assertRaises(wop_db.WopError):
            wop_db.set_status(
                self.root, plan_id, "completed", "executed", "pending"
            )
        with self.assertRaises(wop_db.WopError):
            wop_db.set_status(
                self.root, plan_id, "accepted", "executed", "accepted"
            )
        accepted = wop_db.set_status(
            self.root,
            plan_id,
            "accepted",
            "executed",
            "accepted",
            ["reports/acceptance.md"],
            "Execution and final acceptance were verified.",
            "product-owner",
            True,
        )
        self.assertEqual(accepted["plan_status"], "accepted")
        recorded = wop_db.evidence(self.root, plan_id)
        self.assertEqual(recorded[0]["evidence_type"], "execution_and_acceptance")
        self.assertEqual(recorded[0]["human_approved"], 1)

    def test_check_rejects_unchecked_integrity_and_metadata_conflicts(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        with mock.patch(
            "wop_db.prompt_integrity_detail",
            return_value=("unchecked", "validator crashed"),
        ):
            report = wop_db.check(self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(item["status"] == "unchecked" for item in report["issues"])
        )
        readme = package / "README.md"
        changed = readme.read_text(encoding="utf-8").replace(
            "title: Representative Plan", "title: Conflicting Projection"
        )
        with readme.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(changed)
        report = wop_db.check(self.root)
        self.assertFalse(report["ok"])
        codes = {item["code"] for item in report["issues"]}
        self.assertIn("metadata_mismatch", codes)
        self.assertIn("content_hash_mismatch", codes)
        self.assertEqual(
            wop_db.get_plan(self.root, plan_id=plan_id)["title"],
            "Representative Plan",
        )

    def test_status_partial_failure_restores_readme_and_database(self) -> None:
        package, plan_id = create_package(self.root)
        before = wop_db.register(self.root, package)
        readme_before = (package / "README.md").read_bytes()
        with mock.patch(
            "wop_db.content_hash", side_effect=OSError("simulated hash failure")
        ):
            with self.assertRaises(OSError):
                wop_db.set_status(
                    self.root, plan_id, "in_progress", "in_progress", "pending"
                )
        after = wop_db.get_plan(self.root, plan_id=plan_id)
        self.assertEqual(after["plan_status"], before["plan_status"])
        self.assertEqual(after["execution_status"], before["execution_status"])
        self.assertEqual((package / "README.md").read_bytes(), readme_before)
        with wop_db.connect(self.root) as conn:
            operation = conn.execute(
                "SELECT status FROM plan_operations WHERE plan_id=? "
                "ORDER BY started_at DESC LIMIT 1",
                (plan_id,),
            ).fetchone()
        self.assertEqual(operation["status"], "rolled_back")

    def test_portuguese_and_spanish_ir_generation_is_complete(self) -> None:
        for index, language in enumerate(("pt-BR", "es"), start=7):
            with self.subTest(language=language):
                package, _ = create_universal_package(
                    self.root,
                    language,
                    "2026_03_04_05_06_{0:02d}".format(index),
                )
                report = validate_plan.validate_package(package, self.root)
                self.assertTrue(report["valid"], report["errors"])
                prompt = (package / "prompts" / "wave-02.md").read_text(
                    encoding="utf-8"
                )
                fixture = UNIVERSAL_LANGUAGE_CASES[language]
                self.assertIn(fixture["wave"] + " W002", prompt)
                self.assertIn(fixture["criterion"], prompt)
                self.assertIn(fixture["instruction"], prompt)
                self.assertNotIn("Execution Boundary", prompt)
                self.assertIn("I001", prompt)
                self.assertIn("artifact-i001.md", prompt)
                self.assertIn("W001", prompt)
                master = (package / "prompts" / "execute-all.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(fixture["title"], master)
                self.assertIn(fixture["instruction"], master)
                self.assertEqual(master.count("prompts/wave-"), 2)
                self.assertEqual(
                    validate_plan.frontmatter(master)["language"], language
                )

    def test_language_selection_hierarchy_and_open_tags(self) -> None:
        self.assertEqual(plan_model.select_language("fr", "pt-BR"), "fr")
        self.assertEqual(plan_model.select_language(None, "ja"), "ja")
        self.assertEqual(plan_model.select_language(None, None), "en")
        for language in (
            "pt-BR", "en", "es", "fr", "de", "ja", "zh-CN", "ar",
            "x-klingon", "sl-rozaj-biske",
        ):
            with self.subTest(language=language):
                self.assertTrue(plan_model.is_language_tag(language))
        for invalid in ("", "en_US", "-fr", "fr-", "not a tag"):
            with self.subTest(invalid=invalid):
                self.assertFalse(plan_model.is_language_tag(invalid))
        with self.assertRaises(ValueError):
            plan_model.select_language("en_US", "fr")

    def test_universal_generation_for_required_languages(self) -> None:
        languages = ("pt-BR", "en", "es", "fr", "de", "ja", "zh-CN", "ar")
        for index, language in enumerate(languages, start=20):
            with self.subTest(language=language):
                package, _ = create_universal_package(
                    self.root,
                    language,
                    "2026_03_04_05_07_{0:02d}".format(index),
                )
                report = validate_plan.validate_package(package, self.root)
                self.assertTrue(report["valid"], report["errors"])
                fixture = UNIVERSAL_LANGUAGE_CASES[language]
                prompt = (package / "prompts" / "wave-02.md").read_text(
                    encoding="utf-8"
                )
                master = (package / "prompts" / "execute-all.md").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(
                    validate_plan.frontmatter(prompt)["language"], language
                )
                self.assertEqual(
                    validate_plan.frontmatter(master)["language"], language
                )
                for expected in (
                    fixture["title"], fixture["criterion"],
                    fixture["instruction"], fixture["handoff"],
                ):
                    self.assertIn(expected, prompt)
                self.assertIn(fixture["title"], master)
                self.assertIn(fixture["instruction"], master)
                for literal in ("W001", "W002", "I001", "R001", "README.md"):
                    self.assertIn(literal, prompt)

    def test_language_not_registered_in_runtime_catalog(self) -> None:
        package, _ = create_universal_package(
            self.root, "eo", "2026_03_04_05_08_01"
        )
        report = validate_plan.validate_package(package, self.root)
        self.assertTrue(report["valid"], report["errors"])
        fixture = UNIVERSAL_LANGUAGE_CASES["eo"]
        prompt = (package / "prompts" / "wave-02.md").read_text(encoding="utf-8")
        master = (package / "prompts" / "execute-all.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(fixture["criterion"], prompt)
        self.assertIn(fixture["instruction"], master)
        scripts_text = "\n".join(
            path.read_text(encoding="utf-8") for path in SCRIPTS.glob("*.py")
        )
        self.assertNotIn("LOCALES", scripts_text)
        self.assertNotIn("locale_for", scripts_text)
        self.assertNotIn("if language ==", scripts_text)

    def test_language_change_replaces_prompts_and_updates_sqlite(self) -> None:
        timestamp = "2026_03_04_05_09_01"
        package, plan_id = create_universal_package(
            self.root, "pt-BR", timestamp
        )
        registered = wop_db.register(self.root, package)
        old_prompt = (package / "prompts" / "wave-02.md").read_text(
            encoding="utf-8"
        )
        old_master = (package / "prompts" / "execute-all.md").read_text(
            encoding="utf-8"
        )
        updated_at = (
            datetime.fromisoformat(registered["updated_at"]) + timedelta(seconds=1)
        ).isoformat()
        french = UNIVERSAL_LANGUAGE_CASES["fr"]
        write_utf8(
            package / "README.md",
            render_universal_readme(
                "fr", french, plan_id, registered["created_at"], updated_at, 2
            ),
        )
        validate_plan.generate_prompts(package)
        revised_path = package.parent / "2026_03_04_05_09_02-plan_universel"
        revised = wop_db.rename_package(
            self.root, plan_id, str(revised_path), "Passer au français", "test"
        )
        self.assertEqual(revised["language"], "fr")
        self.assertEqual(revised["version"], 2)
        self.assertEqual(revised["plan_id"], plan_id)
        for prompt_path in (revised_path / "prompts").glob("*.md"):
            text = prompt_path.read_text(encoding="utf-8")
            self.assertEqual(validate_plan.frontmatter(text)["language"], "fr")
        new_prompt = (revised_path / "prompts" / "wave-02.md").read_text(
            encoding="utf-8"
        )
        new_master = (revised_path / "prompts" / "execute-all.md").read_text(
            encoding="utf-8"
        )
        self.assertNotEqual(old_prompt, new_prompt)
        self.assertNotEqual(old_master, new_master)
        self.assertIn(french["criterion"], new_prompt)
        self.assertIn(french["instruction"], new_master)
        self.assertNotIn(UNIVERSAL_LANGUAGE_CASES["pt-BR"]["criterion"], new_prompt)
        self.assertTrue(wop_db.check(self.root)["ok"])

    def test_mixed_technical_content_is_preserved_verbatim(self) -> None:
        technical = """```python
user_id = fetch_user(\"/api/v1/users\")
```

Execute `docker compose up` e preserve `API`, `backend`, `SQL`, `JWT` e `USER_TOKEN`."""
        package, _ = create_universal_package(
            self.root,
            "pt-BR",
            "2026_03_04_05_10_01",
            extra_requirement=technical,
        )
        report = validate_plan.validate_package(package, self.root)
        self.assertTrue(report["valid"], report["errors"])
        prompt = (package / "prompts" / "wave-01.md").read_text(encoding="utf-8")
        self.assertIn(technical, prompt)
        for literal in (
            'fetch_user("/api/v1/users")', "docker compose up", "API",
            "backend", "SQL", "JWT", "USER_TOKEN",
        ):
            self.assertIn(literal, prompt)

    def test_multilingual_update_preserves_language_and_refreshes_artifacts(self) -> None:
        package, plan_id = create_universal_package(
            self.root, "ja", "2026_03_04_05_11_01"
        )
        registered = wop_db.register(self.root, package)
        old_master = (package / "prompts" / "execute-all.md").read_text(
            encoding="utf-8"
        )
        updated_fixture = dict(UNIVERSAL_LANGUAGE_CASES["ja"])
        updated_fixture["requirement"] = "更新された成果物を作成し、実際の結果を証明する。"
        updated_fixture["instruction"] = "READMEを読み、更新後のウェーブを順番に実行し、各ゲートを再評価する。"
        updated_at = (
            datetime.fromisoformat(registered["updated_at"]) + timedelta(seconds=1)
        ).isoformat()
        write_utf8(
            package / "README.md",
            render_universal_readme(
                "ja", updated_fixture, plan_id,
                registered["created_at"], updated_at, 2,
            ),
        )
        validate_plan.generate_prompts(package)
        revised_path = package.parent / "2026_03_04_05_11_02-universal_plan_ja"
        revised = wop_db.rename_package(
            self.root, plan_id, str(revised_path), "日本語の計画を更新", "test"
        )
        self.assertEqual(revised["language"], "ja")
        self.assertEqual(revised["version"], 2)
        prompt = (revised_path / "prompts" / "wave-01.md").read_text(
            encoding="utf-8"
        )
        master = (revised_path / "prompts" / "execute-all.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(updated_fixture["requirement"], prompt)
        self.assertIn(updated_fixture["instruction"], master)
        self.assertNotEqual(old_master, master)
        self.assertEqual(validate_plan.frontmatter(master)["language"], "ja")
        self.assertTrue(wop_db.check(self.root)["ok"])

    def test_official_templates_and_localized_examples_are_structurally_complete(self) -> None:
        cases = (
            (
                SKILL_ROOT / "templates" / "compact-plan.md",
                "2026_03_04_05_06_04-compact_model",
                1,
            ),
            (
                SKILL_ROOT / "templates" / "standard-plan.md",
                "2026_03_04_05_06_05-standard_model",
                2,
            ),
            (
                SKILL_ROOT / "templates" / "extensive-plan.md",
                "2026_03_04_05_06_06-extensive_model",
                3,
            ),
            (
                SKILL_ROOT / "examples" / "localized-plans" / "pt-BR" /
                "standard-plan.md",
                "2026_03_04_05_06_07-modelo_pt",
                2,
            ),
            (
                SKILL_ROOT / "examples" / "localized-plans" / "es" /
                "standard-plan.md",
                "2026_03_04_05_06_08-modelo_es",
                2,
            ),
        )
        self.assertFalse((SKILL_ROOT / "templates" / "standard-plan.pt-BR.md").exists())
        self.assertFalse((SKILL_ROOT / "templates" / "standard-plan.es.md").exists())
        for template_path, package_name, expected_waves in cases:
            with self.subTest(template=template_path):
                package = render_template_package(
                    self.root, template_path, package_name
                )
                report = validate_plan.validate_package(package, self.root)
                self.assertEqual(len(plan_model.parse_plan(
                    (package / "README.md").read_text(encoding="utf-8")
                ).waves), expected_waves)
                self.assertTrue(report["valid"], report["errors"])

    def test_compact_template_is_minimal_one_wave_one_item_and_generates_prompts(self) -> None:
        compact_path = SKILL_ROOT / "templates" / "compact-plan.md"
        standard_path = SKILL_ROOT / "templates" / "standard-plan.md"
        compact_text = compact_path.read_text(encoding="utf-8")
        standard_text = standard_path.read_text(encoding="utf-8")
        self.assertLess(len(compact_text.splitlines()), len(standard_text.splitlines()) * 0.6)
        self.assertEqual(compact_text.count("wop:wave "), 1)
        self.assertEqual(compact_text.count("wop:item "), 1)
        for omitted in (
            "wop:section confirmed_facts", "wop:section assumptions",
            "wop:section unknowns", "wop:section global_contracts",
            "wop:section dependency_map", "wop:section requirement_traceability",
        ):
            self.assertNotIn(omitted, compact_text)
        for filler in ("No risks.", "No dependencies.", "No assumptions."):
            self.assertNotIn(filler, compact_text)
        package = render_template_package(
            self.root,
            compact_path,
            "2026_06_01_02_03_04-compact_usability",
        )
        report = validate_plan.validate_package(
            package, self.root, check_database=False
        )
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["warnings"], [])
        self.assertTrue((package / "prompts" / "wave-01.md").is_file())
        self.assertTrue((package / "prompts" / "execute-all.md").is_file())

    def test_standard_can_omit_genuinely_irrelevant_conditional_sections(self) -> None:
        package = render_template_package(
            self.root,
            SKILL_ROOT / "templates" / "standard-plan.md",
            "2026_06_01_02_03_09-standard_conditional_sections",
        )
        readme = package / "README.md"
        text = readme.read_text(encoding="utf-8")
        for section_id in (
            "confirmed_facts", "assumptions", "unknowns", "global_contracts"
        ):
            text, count = re.subn(
                r"\n## [^\n]*<!-- wop:section {0} -->.*?(?=\n## )".format(
                    section_id
                ),
                "",
                text,
                flags=re.DOTALL,
            )
            self.assertEqual(count, 1, section_id)
        write_utf8(readme, text)
        validate_plan.generate_prompts(package)
        report = validate_plan.validate_package(
            package, self.root, check_database=False
        )
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["audit_profile"]["planning"], "complete")

    def test_audit_profiles_scale_depth_without_skipping_universal_invariants(self) -> None:
        cases = (
            ("compact-plan.md", "2026_06_01_02_03_05-audit_compact", "essential", "direct_verification"),
            ("standard-plan.md", "2026_06_01_02_03_06-audit_standard", "complete", "traceability_matrix"),
            ("extensive-plan.md", "2026_06_01_02_03_07-audit_extensive", "detailed", "full_traceability"),
        )
        reports = []
        for template_name, package_name, planning, coverage in cases:
            package = render_template_package(
                self.root, SKILL_ROOT / "templates" / template_name, package_name
            )
            report = validate_plan.validate_package(package, self.root)
            self.assertTrue(report["valid"], report["errors"])
            self.assertEqual(report["audit_profile"]["planning"], planning)
            self.assertEqual(report["audit_profile"]["coverage"], coverage)
            self.assertEqual(report["audit_profile"]["final_acceptance"], "mandatory")
            self.assertEqual(report["audit_profile"]["workspace_integrity"], "mandatory")
            reports.append(report)
        universal = reports[0]["universal_audit_invariants"]
        self.assertTrue(universal)
        self.assertTrue(all(report["universal_audit_invariants"] == universal for report in reports))
        self.assertLess(
            len(reports[0]["semantic_review_required"]),
            len(reports[2]["semantic_review_required"]),
        )

    def test_skill_reference_loading_routes_are_selective(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        rows = {
            line.split("|", 2)[1].strip(): line
            for line in skill.splitlines()
            if line.startswith("|") and line.count("|") >= 3
        }
        inspect_row = rows["DISCOVER or READ"]
        self.assertIn("plan-management/workspace.md", inspect_row)
        self.assertIn("plan-management/discovery.md", inspect_row)
        for unrelated in ("core/", "writing/", "modules/", "interaction/", "checklists/"):
            self.assertNotIn(unrelated, inspect_row)
        create_row = rows["CREATE"]
        for required in (
            "core/adaptive-planning.md", "core/planning-process.md",
            "core/wave-methodology.md", "writing/writing-for-agents.md",
            "writing/information-hierarchy.md",
        ):
            self.assertIn(required, create_row)
        self.assertIn(
            "only when unresolved user-owned decisions materially change the plan",
            skill,
        )
        self.assertIn("Never load every format module by default", skill)
        self.assertIn("Do not load every checklist", skill)

    def test_anti_fragmentation_contract_preserves_simple_work_and_real_independence(self) -> None:
        compact = plan_model.parse_plan(
            (SKILL_ROOT / "templates" / "compact-plan.md").read_text(encoding="utf-8")
        )
        self.assertEqual(len(compact.waves), 1)
        self.assertEqual(len(compact.waves[0].items), 1)
        required_docs = (
            "core/adaptive-planning.md", "core/wave-methodology.md",
            "core/planning-process.md", "core/parallelism.md",
            "checklists/planning-audit.md", "checklists/independence-audit.md",
        )
        anti_fragmentation_text = ""
        for relative in required_docs:
            text = (SKILL_ROOT / relative).read_text(encoding="utf-8").casefold()
            self.assertTrue(
                any(term in text for term in ("split", "fragment", "multiple items")),
                relative,
            )
            anti_fragmentation_text += "\n" + text
        self.assertIn("one wave", anti_fragmentation_text)
        self.assertIn("one item", anti_fragmentation_text)

        package = render_template_package(
            self.root,
            SKILL_ROOT / "templates" / "compact-plan.md",
            "2026_06_01_02_03_08-compact_parallelism_guard",
        )
        readme = package / "README.md"
        text = readme.read_text(encoding="utf-8")
        second_item = """#### Item I002 — Independent Output <!-- wop:item I002 -->

##### Objective <!-- wop:field objective -->

Produce the second output.

##### Scope <!-- wop:field scope -->

- Create the second output.

##### Outputs <!-- wop:field outputs -->

- second-output.md

##### Acceptance Criteria <!-- wop:field acceptance_criteria -->

- The second output passes inspection.

"""
        text = text.replace("Execute only I001 in W001", "Execute only I001 and I002 in W001")
        text = text.replace("## Verification and Final Checks", second_item + "## Verification and Final Checks")
        write_utf8(readme, text)
        validate_plan.generate_prompts(package)
        report = validate_plan.validate_package(package, self.root)
        self.assertFalse(report["valid"])
        codes = {error["code"] for error in report["errors"]}
        self.assertIn("compact_parallelism_field", codes)
        self.assertIn("item_field", codes)

    def test_all_relative_markdown_links_resolve_after_localized_example_move(self) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        missing = []
        for source in SKILL_ROOT.rglob("*.md"):
            for target in link_pattern.findall(source.read_text(encoding="utf-8")):
                target = target.strip().split("#", 1)[0]
                if not target or "://" in target or target.startswith(("#", "/")):
                    continue
                if not (source.parent / target).resolve().exists():
                    missing.append((source.relative_to(SKILL_ROOT).as_posix(), target))
        self.assertEqual(missing, [])
        for language in ("pt-BR", "es"):
            localized = (
                SKILL_ROOT / "examples" / "localized-plans" / language /
                "standard-plan.md"
            ).read_text(encoding="utf-8")
            self.assertEqual(localized.count("wop:wave "), 2)
            self.assertEqual(localized.count("wop:item "), 2)

    def test_complete_examples_cover_full_lifecycle(self) -> None:
        examples = (
            (
                "2026_04_01_09_00_00-release_evidence_pipeline",
                "2026_04_01_09_00_01-release_evidence_pipeline",
                "Deliver a reproducible release-evidence bundle",
                "Deliver a reproducible and documented release-evidence bundle",
            ),
            (
                "2026_04_01_10_00_00-pipeline_de_evidencias",
                "2026_04_01_10_00_01-pipeline_de_evidencias",
                "Entregar um pacote reproduzível de evidências",
                "Entregar um pacote reproduzível e documentado de evidências",
            ),
        )
        source_root = SKILL_ROOT / "examples" / "packages"
        for source_name, revised_name, old_text, new_text in examples:
            with self.subTest(example=source_name):
                package = self.root / ".wop" / "plans" / source_name
                shutil.copytree(source_root / source_name, package)
                report = validate_plan.validate_package(package, self.root)
                self.assertTrue(report["valid"], report["errors"])
                example_prompts = {
                    number: (package / "prompts" / "wave-{0:02d}.md".format(number))
                    .read_text(encoding="utf-8")
                    for number in (1, 2, 3)
                }
                expected_assignments = {1: "I001,I002", 2: "I003", 3: "I004"}
                for number, prompt_text in example_prompts.items():
                    self.assertEqual(
                        validate_plan.frontmatter(prompt_text)["authorized_items"],
                        expected_assignments[number],
                    )
                    self.assertIn("wop:section compatibility_decision", prompt_text)
                    protocol_block = prompt_text.split(
                        plan_model.prompt_marker("global_protocol"), 1
                    )[1].split(plan_model.prompt_marker("execution_scope"), 1)[0]
                    self.assertEqual(plan_model.technical_ids(protocol_block, "I"), [])
                    self.assertEqual(prompt_text.count("wop:field prerequisites"), 1)
                self.assertNotIn(
                    "wop:section manifest_construction", example_prompts[1]
                )
                self.assertIn(
                    "wop:section manifest_construction", example_prompts[2]
                )
                self.assertNotIn(
                    "wop:section manifest_construction", example_prompts[3]
                )
                self.assertNotIn(
                    "wop:section final_report_restrictions", example_prompts[1]
                )
                self.assertNotIn(
                    "wop:section final_report_restrictions", example_prompts[2]
                )
                self.assertIn(
                    "wop:section final_report_restrictions", example_prompts[3]
                )
                example_master = (
                    package / "prompts" / "execute-all.md"
                ).read_text(encoding="utf-8")
                self.assertIn("wop:section compatibility_decision", example_master)
                self.assertNotIn("wop:section manifest_construction", example_master)
                self.assertNotIn(
                    "wop:section final_report_restrictions", example_master
                )
                registered = wop_db.register(self.root, package, "example homologation")
                plan_id = registered["plan_id"]
                self.assertEqual(
                    wop_db.get_plan(self.root, plan_id=plan_id)["version"], 1
                )

                readme = package / "README.md"
                changed = readme.read_text(encoding="utf-8")
                changed = changed.replace("version: 1", "version: 2", 1)
                changed = changed.replace(old_text, new_text, 1)
                original_updated = registered["updated_at"]
                revised_updated = (
                    datetime.fromisoformat(original_updated) + timedelta(seconds=1)
                ).isoformat()
                changed = changed.replace(
                    "updated_at: {0}".format(original_updated),
                    "updated_at: {0}".format(revised_updated),
                    1,
                )
                write_utf8(readme, changed)
                validate_plan.generate_prompts(package)
                revised = wop_db.rename_package(
                    self.root,
                    plan_id,
                    str(package.parent / revised_name),
                    "Homologation revision",
                    "example test",
                )
                self.assertEqual(revised["version"], 2)
                archived = wop_db.move_package(self.root, plan_id, True)
                self.assertEqual(archived["plan_status"], "archived")
                restored = wop_db.move_package(self.root, plan_id, False)
                self.assertEqual(restored["plan_status"], "ready")
                self.assertTrue(wop_db.check(self.root)["ok"])
                deleted = wop_db.delete_plan(
                    self.root, plan_id, True, "example lifecycle homologation"
                )
                self.assertTrue(deleted["tombstone_retained"])

    def test_prompt_generation_is_atomic_and_removes_obsolete_prompts(self) -> None:
        package, _ = create_package(self.root)
        prompt_dir = package / "prompts"
        before = {
            path.name: path.read_bytes() for path in prompt_dir.iterdir() if path.is_file()
        }
        real_write = validate_plan.write_utf8
        call_count = {"value": 0}

        def fail_second_write(path: Path, content: str) -> None:
            call_count["value"] += 1
            if call_count["value"] == 2:
                raise OSError("simulated prompt write failure")
            real_write(path, content)

        with mock.patch("validate_plan.write_utf8", side_effect=fail_second_write):
            with self.assertRaises(validate_plan.ValidationFailure):
                validate_plan.generate_prompts(package)
        after = {
            path.name: path.read_bytes() for path in prompt_dir.iterdir() if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertFalse(
            any(
                path.name.startswith((".generate-prompts-", ".previous-prompts-"))
                for path in package.iterdir()
            )
        )
        obsolete = prompt_dir / "wave-99.md"
        write_utf8(obsolete, "obsolete")
        self.assertFalse(validate_plan.validate_package(package, self.root)["valid"])
        validate_plan.generate_prompts(package)
        self.assertFalse(obsolete.exists())
        self.assertTrue(validate_plan.validate_package(package, self.root)["valid"])

    def test_dependency_cycles_are_rejected_and_preexisting_cycles_are_audited(self) -> None:
        first, first_id = create_package(self.root, name="cycle_first")
        second, second_id = create_package(
            self.root, name="cycle_second", timestamp="2026_01_02_03_04_06"
        )
        third, third_id = create_package(
            self.root, name="cycle_third", timestamp="2026_01_02_03_04_07"
        )
        for package in (first, second, third):
            wop_db.register(self.root, package)
        wop_db.create_relation(
            self.root, first_id, second_id, "depends_on", "First uses second."
        )
        wop_db.create_relation(
            self.root, second_id, third_id, "depends_on", "Second uses third."
        )
        with self.assertRaises(wop_db.WopError):
            wop_db.create_relation(
                self.root, third_id, first_id, "depends_on", "Invalid cycle."
            )
        wop_db.create_relation(
            self.root, third_id, first_id, "related_to", "Association is allowed."
        )
        with wop_db.connect(self.root) as conn:
            conn.execute(
                "INSERT INTO plan_relations(source_plan_id,target_plan_id,"
                "relation_type,rationale,created_at) VALUES(?,?,?,?,?)",
                (third_id, first_id, "depends_on", "legacy invalid cycle", wop_db.now()),
            )
        report = wop_db.check(self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(item["code"] == "dependency_cycle" for item in report["issues"])
        )

    def test_content_revision_is_versioned_but_read_and_admin_rename_are_not(self) -> None:
        package, plan_id = create_package(self.root)
        original = wop_db.register(self.root, package)
        wop_db.get_plan(self.root, plan_id=plan_id)
        wop_db.history(self.root, plan_id)
        initial_history_count = len(wop_db.history(self.root, plan_id))
        self.assertEqual(initial_history_count, 1)

        readme = package / "README.md"
        changed = readme.read_text(encoding="utf-8")
        changed = changed.replace("version: 1", "version: 2", 1)
        changed = changed.replace(
            "updated_at: {0}".format(original["updated_at"]),
            "updated_at: {0}".format(
                (datetime.fromisoformat(original["updated_at"]) + timedelta(seconds=1))
                .replace(microsecond=0)
                .isoformat()
            ),
            1,
        )
        changed = changed.replace(
            "Deliver a verified three-stage example.",
            "Deliver a verified and documented three-stage example.",
        )
        write_utf8(readme, changed)
        validate_plan.generate_prompts(package)
        revised_name = "2026_01_02_03_04_08-representative_plan"
        revised = wop_db.rename_package(
            self.root,
            plan_id,
            str(package.parent / revised_name),
            "Document the deliverable",
            "user revision",
        )
        self.assertEqual(revised["plan_id"], plan_id)
        self.assertEqual(revised["created_at"], original["created_at"])
        self.assertEqual(revised["version"], 2)
        self.assertEqual(
            len(wop_db.history(self.root, plan_id)), initial_history_count + 1
        )
        revised_path = self.root / revised["current_relative_path"]
        admin_name = "2026_01_02_03_04_09-representative_plan"
        renamed = wop_db.rename_package(
            self.root, plan_id, str(revised_path.parent / admin_name)
        )
        self.assertEqual(renamed["version"], 2)
        self.assertEqual(
            len(wop_db.history(self.root, plan_id)), initial_history_count + 1
        )
        self.assertTrue(wop_db.check(self.root)["ok"])

    def test_archive_failure_rolls_back_filesystem_and_projection(self) -> None:
        package, plan_id = create_package(self.root)
        before = wop_db.register(self.root, package)
        readme_before = (package / "README.md").read_bytes()
        with mock.patch(
            "wop_db.content_hash", side_effect=OSError("simulated archive hash failure")
        ):
            with self.assertRaises(OSError):
                wop_db.move_package(self.root, plan_id, True)
        self.assertTrue(package.is_dir())
        self.assertEqual((package / "README.md").read_bytes(), readme_before)
        after = wop_db.get_plan(self.root, plan_id=plan_id)
        self.assertEqual(after["current_relative_path"], before["current_relative_path"])
        self.assertEqual(after["plan_status"], before["plan_status"])
        with wop_db.connect(self.root) as conn:
            operation = conn.execute(
                "SELECT status FROM plan_operations WHERE plan_id=? "
                "ORDER BY started_at DESC LIMIT 1",
                (plan_id,),
            ).fetchone()
        self.assertEqual(operation["status"], "rolled_back")

    def test_rename_sqlite_failure_restores_original_package(self) -> None:
        package, plan_id = create_package(self.root)
        before = wop_db.register(self.root, package)
        target = package.parent / "2026_01_02_03_04_11-representative_plan"
        with mock.patch(
            "wop_db.add_event", side_effect=sqlite3.OperationalError("simulated DB failure")
        ):
            with self.assertRaises(sqlite3.OperationalError):
                wop_db.rename_package(self.root, plan_id, str(target))
        self.assertTrue(package.is_dir())
        self.assertFalse(target.exists())
        after = wop_db.get_plan(self.root, plan_id=plan_id)
        self.assertEqual(after["current_relative_path"], before["current_relative_path"])
        with wop_db.connect(self.root) as conn:
            operation = conn.execute(
                "SELECT status FROM plan_operations WHERE plan_id=? "
                "ORDER BY started_at DESC LIMIT 1",
                (plan_id,),
            ).fetchone()
        self.assertEqual(operation["status"], "rolled_back")

    def test_delete_cleanup_failure_is_auditable_and_retains_tombstone(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        with mock.patch(
            "wop_db.shutil.rmtree", side_effect=OSError("simulated cleanup failure")
        ):
            with self.assertRaises(wop_db.WopError):
                wop_db.delete_plan(self.root, plan_id, True, "cleanup recovery test")
        with wop_db.connect(self.root) as conn:
            tombstone = conn.execute(
                "SELECT 1 FROM plan_tombstones WHERE plan_id=?", (plan_id,)
            ).fetchone()
            operation = conn.execute(
                "SELECT status,target_path FROM plan_operations WHERE plan_id=? "
                "ORDER BY started_at DESC LIMIT 1",
                (plan_id,),
            ).fetchone()
        self.assertIsNotNone(tombstone)
        self.assertEqual(operation["status"], "failed")
        self.assertTrue(Path(operation["target_path"]).is_dir())
        audit = wop_db.check(self.root)
        self.assertFalse(audit["ok"])
        codes = {item["code"] for item in audit["issues"]}
        self.assertIn("unfinished_operation", codes)
        self.assertIn("staged_delete_package", codes)

    def test_interrupted_operation_never_passes_audit(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        operation_id = wop_db.start_operation(
            self.root, plan_id, "simulated_interruption", package, package
        )
        report = wop_db.check(self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                issue["code"] == "unfinished_operation"
                and operation_id in issue["message"]
                for issue in report["issues"]
            )
        )

    def test_tombstoned_ids_and_path_traversal_are_rejected(self) -> None:
        package, plan_id = create_package(self.root)
        wop_db.register(self.root, package)
        wop_db.delete_plan(self.root, plan_id, True, "retire test plan")
        replacement, _ = create_package(
            self.root,
            plan_id=plan_id,
            name="forbidden_reuse",
            timestamp="2026_01_02_03_04_10",
        )
        with self.assertRaises(wop_db.WopError):
            wop_db.register(self.root, replacement)
        with self.assertRaises(wop_db.WopError):
            wop_db.normalize_package(
                self.root,
                self.root / ".wop" / "plans" / ".." / "outside",
                must_exist=False,
            )

    def test_validator_cli_cannot_modify_outside_managed_workspace(self) -> None:
        package, _ = create_package(self.root)
        outside = self.root / "2026_01_02_03_04_12-outside_package"
        shutil.copytree(package, outside)
        before = {
            path.relative_to(outside).as_posix(): path.read_bytes()
            for path in outside.rglob("*")
            if path.is_file()
        }
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_plan.py"),
                "--root",
                str(self.root),
                "--directory",
                str(outside),
                "--generate-prompts",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        error = json.loads(result.stderr)
        self.assertEqual(error["integrity_status"], "unchecked")
        after = {
            path.relative_to(outside).as_posix(): path.read_bytes()
            for path in outside.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
