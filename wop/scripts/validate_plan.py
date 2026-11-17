#!/usr/bin/env python3
"""Parse, generate, and validate language-neutral WOP plan packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

from plan_model import (
    COMPACT_REQUIRED_ITEM_FIELD_IDS,
    COMPACT_REQUIRED_SECTION_IDS,
    COMPACT_REQUIRED_WAVE_FIELD_IDS,
    PlanIR,
    PlanParseError,
    REQUIRED_ITEM_FIELD_IDS,
    REQUIRED_SECTION_IDS,
    REQUIRED_WAVE_FIELD_IDS,
    STANDARD_REQUIRED_SECTION_IDS,
    WaveIR,
    is_language_tag,
    parse_plan,
    prompt_entity_marker,
    prompt_marker,
    split_frontmatter,
    technical_ids,
)


DIRECTORY_PATTERN = re.compile(
    r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}-[a-z0-9]+(?:_[a-z0-9]+)*$"
)
REQUIRED_METADATA = (
    "plan_id", "title", "version", "language", "complexity", "plan_status",
    "execution_status", "acceptance_status", "created_at", "updated_at",
)
OPERATIONAL_PROJECTION_KEYS = (
    "plan_status", "execution_status", "acceptance_status",
)
UNIVERSAL_AUDIT_INVARIANTS = (
    "Declared plan language is used consistently.",
    "Required metadata is valid.",
    "Every item has an objective and acceptance criteria.",
    "Every wave has an objective and general acceptance criteria.",
    "Strict wave sequencing is preserved.",
    "Same-wave independence is verified whenever items coexist.",
    "All required prompts exist and match the plan.",
    "SQLite and filesystem integrity are checked when relevant.",
    "Final acceptance is defined.",
)


class ValidationFailure(RuntimeError):
    """Generation or validation cannot proceed without risking inconsistency."""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationFailure("File is not valid UTF-8: {0}".format(path)) from exc


def write_utf8(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def frontmatter(text: str) -> dict[str, str]:
    try:
        return split_frontmatter(text)[0]
    except PlanParseError as exc:
        raise ValidationFailure(str(exc)) from exc


def readme_digest(readme_text: str) -> str:
    lines = readme_text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                break
            if ":" not in lines[index]:
                continue
            key = lines[index].split(":", 1)[0].strip()
            if key in OPERATIONAL_PROJECTION_KEYS:
                lines[index] = "{0}: <operational-state-projection>".format(key)
    canonical = "\n".join(lines)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def scalar_yaml(value: Any) -> str:
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_.:/+-]+", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def prompt_frontmatter(values: dict[str, Any]) -> str:
    lines = ["---"]
    lines.extend(
        "{0}: {1}".format(key, scalar_yaml(value))
        for key, value in values.items()
    )
    lines.append("---")
    return "\n".join(lines)


def _context_markdown(plan: PlanIR, wave: WaveIR) -> str:
    return "\n\n".join(section.raw for section in plan.context_sections(wave))


def _fields_markdown(
    fields: dict[str, Any], field_ids: Sequence[str]
) -> str:
    return "\n\n".join(
        fields[field_id].raw for field_id in field_ids if field_id in fields
    )


def _global_protocol_markdown(plan: PlanIR) -> str:
    protocol = plan.section("execution_protocol")
    return protocol.raw if protocol else ""


def _execution_scope_markdown(wave: WaveIR) -> str:
    parts = [
        "{0}\n{1}".format(
            prompt_entity_marker("assigned-wave", wave.wave_id),
            _fields_markdown(
                wave.fields,
                (
                    "general_objective", "requirements_addressed",
                    "execution_instructions", "parallelism_rationale",
                    "ownership_boundaries",
                ),
            ),
        )
    ]
    for item in wave.items:
        parts.append(
            "{0}\n#### {1}\n\n{2}".format(
                prompt_entity_marker("assigned-item", item.item_id),
                item.title,
                _fields_markdown(
                    item.fields,
                    (
                        "objective", "context", "inputs_prerequisites", "scope",
                        "ownership", "outputs", "restrictions",
                    ),
                ),
            )
        )
    return "\n\n".join(parts)


def _predecessor_markdown(plan: PlanIR, wave: WaveIR) -> str:
    predecessors = plan.predecessors(wave)
    parts: list[str] = []
    prerequisites = wave.fields.get("prerequisites")
    if prerequisites:
        parts.append(prerequisites.raw)
    for predecessor in predecessors:
        parts.append(
            "{0}\n## {1}\n\n{2}".format(
                prompt_entity_marker("predecessor", predecessor.wave_id),
                predecessor.title,
                _fields_markdown(
                    predecessor.fields,
                    (
                        "general_objective", "general_acceptance_criteria",
                        "completion_gate", "evidence_requirements",
                        "integration_handoff",
                    ),
                ),
            )
        )
        for item in predecessor.items:
            parts.append(
                "{0}\n#### {1}\n\n{2}".format(
                    prompt_entity_marker("predecessor-item", item.item_id),
                    item.title,
                    _fields_markdown(
                        item.fields,
                        (
                            "outputs", "acceptance_criteria",
                            "verification_evidence", "handoff_requirements",
                        ),
                    ),
                )
            )
    return "\n\n".join(parts)


def _completion_markdown(wave: WaveIR) -> str:
    parts = [
        _fields_markdown(
            wave.fields,
            (
                "general_acceptance_criteria", "completion_gate",
                "evidence_requirements", "integration_handoff",
            ),
        )
    ]
    parts.extend(
        "{0}\n#### {1}\n\n{2}".format(
            prompt_entity_marker("completion-item", item.item_id),
            item.title,
            _fields_markdown(
                item.fields,
                (
                    "acceptance_criteria", "verification_evidence",
                    "handoff_requirements",
                ),
            ),
        )
        for item in wave.items
    )
    return "\n\n".join(part for part in parts if part)


def _assignment_metadata(plan: PlanIR, wave: WaveIR) -> dict[str, str]:
    assigned_items = [item.item_id for item in wave.items]
    all_items = [item.item_id for candidate in plan.waves for item in candidate.items]
    non_authorized_items = [
        item_id for item_id in all_items if item_id not in assigned_items
    ]
    wave_index = plan.waves.index(wave)
    successors = [candidate.wave_id for candidate in plan.waves[wave_index + 1:]]
    predecessors = [candidate.wave_id for candidate in plan.predecessors(wave)]
    return {
        "authorized_items": ",".join(assigned_items),
        "non_authorized_items": ",".join(non_authorized_items) or "none",
        "predecessor_waves": ",".join(predecessors) or "none",
        "blocked_successor_waves": ",".join(successors) or "none",
    }


def generate_wave_prompt(
    plan: PlanIR,
    wave: WaveIR,
    digest: str,
) -> str:
    assignment = _assignment_metadata(plan, wave)
    header = prompt_frontmatter(
        {
            "artifact": "wop-wave-prompt",
            "plan_id": plan.metadata["plan_id"],
            "plan_version": plan.metadata["version"],
            "plan_title": plan.metadata["title"],
            "wave_id": wave.wave_id,
            "authorized_items": assignment["authorized_items"],
            "non_authorized_items": assignment["non_authorized_items"],
            "predecessor_waves": assignment["predecessor_waves"],
            "blocked_successor_waves": assignment["blocked_successor_waves"],
            "language": plan.metadata["language"],
            "source_readme": "README.md",
            "source_readme_sha256": digest,
        }
    )
    return (
        "{0}\n\n# {1}\n\n"
        "{2}\n{3}\n\n"
        "{4}\n{5}\n\n"
        "{6}\n{7}\n\n"
        "{8}\n{9}\n\n"
        "{10}\n{11}\n"
    ).format(
        header,
        wave.title,
        prompt_marker("global_protocol"),
        _global_protocol_markdown(plan),
        prompt_marker("execution_scope"),
        _execution_scope_markdown(wave),
        prompt_marker("predecessor_verification"),
        _predecessor_markdown(plan, wave),
        prompt_marker("shared_context"),
        _context_markdown(plan, wave),
        prompt_marker("completion_contract"),
        _completion_markdown(wave),
    )


def generate_execute_all(plan: PlanIR, digest: str) -> str:
    refs = "\n".join(
        "- prompts/wave-{0:02d}.md — {1} — {2}".format(
            index, wave.wave_id, wave.name
        )
        for index, wave in enumerate(plan.waves, start=1)
    )
    header = prompt_frontmatter(
        {
            "artifact": "wop-execute-all",
            "plan_id": plan.metadata["plan_id"],
            "plan_version": plan.metadata["version"],
            "plan_title": plan.metadata["title"],
            "language": plan.metadata["language"],
            "source_readme": "README.md",
            "source_readme_sha256": digest,
        }
    )
    orchestration = "\n\n".join(
        section.raw for section in plan.orchestration_sections()
    )
    return (
        "{0}\n\n# {1}\n\n"
        "{2}\n{3}\n\n"
        "{4}\n{5}\n"
    ).format(
        header,
        plan.title,
        prompt_marker("wave_prompts"),
        refs,
        prompt_marker("orchestration"),
        orchestration,
    )


def _replace_prompt_directory(package: Path, generated: dict[str, str]) -> None:
    prompts = package / "prompts"
    stage = package / ".generate-prompts-{0}".format(uuid.uuid4().hex)
    backup = package / ".previous-prompts-{0}".format(uuid.uuid4().hex)
    stage.mkdir()
    swapped = False
    try:
        for name, content in generated.items():
            write_utf8(stage / name, content)
        staged_files = {path.name for path in stage.iterdir() if path.is_file()}
        if staged_files != set(generated):
            raise ValidationFailure("Staged prompt set is incomplete.")
        if prompts.exists():
            prompts.rename(backup)
        stage.rename(prompts)
        swapped = True
    except Exception as exc:
        if swapped and prompts.exists():
            failed = package / ".failed-prompts-{0}".format(uuid.uuid4().hex)
            prompts.rename(failed)
            if backup.exists():
                backup.rename(prompts)
            shutil.rmtree(failed, ignore_errors=True)
        elif backup.exists() and not prompts.exists():
            backup.rename(prompts)
        raise ValidationFailure(
            "Prompt generation was rolled back; active prompts were preserved: {0}".format(
                exc
            )
        ) from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    if backup.exists():
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            raise ValidationFailure(
                "New prompts are active, but old prompt backup requires cleanup at "
                "{0}: {1}".format(backup, exc)
            ) from exc


def parse_readme(readme_text: str) -> PlanIR:
    try:
        return parse_plan(readme_text)
    except PlanParseError as exc:
        raise ValidationFailure(str(exc)) from exc


def generate_prompts(package: Path) -> dict[str, Any]:
    package = package.resolve()
    readme = package / "README.md"
    if not readme.is_file():
        raise ValidationFailure("Missing README.md: {0}".format(readme))
    text = read_text(readme)
    plan = parse_readme(text)
    missing = [key for key in REQUIRED_METADATA if not plan.metadata.get(key)]
    if missing:
        raise ValidationFailure(
            "Cannot generate prompts; metadata is missing: {0}".format(
                ", ".join(missing)
            )
        )
    if not plan.waves:
        raise ValidationFailure("Cannot generate prompts; no waves were found.")
    digest = readme_digest(text)
    generated: dict[str, str] = {}
    for index, wave in enumerate(plan.waves, start=1):
        generated["wave-{0:02d}.md".format(index)] = generate_wave_prompt(
            plan, wave, digest
        )
    generated["execute-all.md"] = generate_execute_all(plan, digest)
    _replace_prompt_directory(package, generated)
    return {
        "generated": sorted(generated),
        "wave_count": len(plan.waves),
        "source_readme_sha256": digest,
        "language": plan.metadata["language"],
        "intermediate_representation": {
            "sections": sorted(plan.sections),
            "waves": [wave.wave_id for wave in plan.waves],
            "items": [
                item.item_id for wave in plan.waves for item in wave.items
            ],
        },
    }


def add_error(report: dict[str, Any], code: str, message: str, path: Path) -> None:
    report["errors"].append(
        {"status": "invalid", "code": code, "message": message, "path": str(path)}
    )


def add_conflict(report: dict[str, Any], code: str, message: str, path: Path) -> None:
    report["errors"].append(
        {"status": "conflict", "code": code, "message": message, "path": str(path)}
    )


def add_warning(report: dict[str, Any], code: str, message: str, path: Path) -> None:
    report["warnings"].append(
        {"status": "unchecked", "code": code, "message": message, "path": str(path)}
    )


def validate_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.tzinfo is not None
    except ValueError:
        return False


def _validate_metadata(
    report: dict[str, Any], metadata: dict[str, str], readme: Path
) -> None:
    for key in REQUIRED_METADATA:
        if not metadata.get(key):
            add_error(report, "metadata", "Missing metadata key: {0}".format(key), readme)
    if metadata.get("plan_id"):
        try:
            parsed = uuid.UUID(metadata["plan_id"])
            if str(parsed) != metadata["plan_id"].lower():
                raise ValueError
        except ValueError:
            add_error(report, "plan_id", "plan_id must be a canonical UUID.", readme)
    version = metadata.get("version", "")
    if not version.isdigit() or int(version or "0") < 1:
        add_error(report, "version", "version must be an integer of at least 1.", readme)
    language = metadata.get("language", "")
    if language and not is_language_tag(language):
        add_error(
            report,
            "language",
            "language must be a structurally valid BCP 47-style tag.",
            readme,
        )
    if metadata.get("complexity") not in ("compact", "standard", "extensive"):
        add_error(report, "complexity", "Invalid complexity.", readme)
    if metadata.get("plan_status") not in (
        "draft", "ready", "in_progress", "blocked", "completed", "accepted",
        "cancelled", "superseded", "archived",
    ):
        add_error(report, "plan_status", "Invalid plan_status.", readme)
    if metadata.get("execution_status") not in (
        "not_started", "in_progress", "partially_executed",
        "blocked", "executed", "abandoned",
    ):
        add_error(report, "execution_status", "Invalid execution_status.", readme)
    if metadata.get("acceptance_status") not in (
        "not_evaluated", "pending", "accepted", "rejected",
    ):
        add_error(report, "acceptance_status", "Invalid acceptance_status.", readme)
    for key in ("created_at", "updated_at"):
        if metadata.get(key) and not validate_timestamp(metadata[key]):
            add_error(
                report,
                "timestamp",
                "{0} must be ISO 8601 with a UTC offset.".format(key),
                readme,
            )


def _validate_ir(report: dict[str, Any], plan: PlanIR, readme: Path) -> set[str]:
    complexity = plan.metadata.get("complexity")
    compact = complexity == "compact"
    if compact:
        required_sections = COMPACT_REQUIRED_SECTION_IDS
    elif complexity == "standard":
        required_sections = STANDARD_REQUIRED_SECTION_IDS + (
            ("dependency_map",) if len(plan.waves) > 1 else ()
        )
    else:
        required_sections = REQUIRED_SECTION_IDS
    required_wave_fields = (
        COMPACT_REQUIRED_WAVE_FIELD_IDS if compact else REQUIRED_WAVE_FIELD_IDS
    )
    required_item_fields = (
        COMPACT_REQUIRED_ITEM_FIELD_IDS if compact else REQUIRED_ITEM_FIELD_IDS
    )
    for warning in plan.warnings:
        add_error(report, "plan_structure", warning, readme)
    for section_id in required_sections:
        if section_id not in plan.sections or not plan.sections[section_id].content:
            add_error(
                report,
                "readme_section",
                "Missing structural section: {0}".format(section_id),
                readme,
            )
    expected_waves = [
        "W{0:03d}".format(index) for index in range(1, len(plan.waves) + 1)
    ]
    actual_waves = [wave.wave_id for wave in plan.waves]
    if not plan.waves:
        add_error(report, "waves", "At least one wave is required.", readme)
    elif actual_waves != expected_waves:
        add_error(
            report,
            "wave_ids",
            "Wave IDs must be sequential: expected {0}, found {1}.".format(
                expected_waves, actual_waves
            ),
            readme,
        )
    seen_items: set[str] = set()
    item_to_wave: dict[str, str] = {}
    wave_positions = {
        wave.wave_id: position for position, wave in enumerate(plan.waves)
    }
    for wave in plan.waves:
        for item in wave.items:
            item_to_wave[item.item_id] = wave.wave_id
    protocol = plan.section("execution_protocol")
    if protocol:
        protocol_items = technical_ids(protocol.content, "I")
        if protocol_items:
            add_error(
                report,
                "global_protocol_item_assignment",
                "Global execution protocol contains item-specific assignments: {0}."
                .format(", ".join(sorted(set(protocol_items)))),
                readme,
            )
    for index, wave in enumerate(plan.waves, start=1):
        assigned_items = {item.item_id for item in wave.items}
        for field_id in required_wave_fields:
            if not wave.value(field_id):
                add_error(
                    report,
                    "wave_field",
                    "{0} is missing field {1}.".format(wave.wave_id, field_id),
                    readme,
                )
        if not wave.value("execution_instructions"):
            add_warning(
                report,
                "legacy_wave_execution_instructions",
                "{0} has no explicit execution_instructions field; the prompt scope "
                "is derived from its existing wave and item fields.".format(
                    wave.wave_id
                ),
                readme,
            )
        prerequisite_refs = technical_ids(wave.value("prerequisites"), "W")
        for reference in prerequisite_refs:
            if reference not in wave_positions:
                add_error(
                    report,
                    "unknown_wave_dependency",
                    "{0} references unknown prerequisite {1}.".format(
                        wave.wave_id, reference
                    ),
                    readme,
                )
            elif wave_positions[reference] >= index - 1:
                add_error(
                    report,
                    "forward_wave_dependency",
                    "{0} cannot depend on itself or later wave {1}.".format(
                        wave.wave_id, reference
                    ),
                    readme,
                )
        if index > 1:
            expected_predecessor = "W{0:03d}".format(index - 1)
            actual_predecessors = {
                predecessor.wave_id for predecessor in plan.predecessors(wave)
            }
            if expected_predecessor not in actual_predecessors:
                add_error(
                    report,
                    "predecessor_gate",
                    "{0} must identify predecessor {1} in prerequisites.".format(
                        wave.wave_id, expected_predecessor
                    ),
                    readme,
                )
        if not wave.items:
            add_error(
                report, "items", "{0} has no work items.".format(wave.wave_id), readme
            )
        if compact and len(wave.items) > 1:
            for field_id in ("parallelism_rationale", "ownership_boundaries"):
                if not wave.value(field_id):
                    add_error(
                        report,
                        "compact_parallelism_field",
                        "{0} has multiple items and therefore requires {1}.".format(
                            wave.wave_id, field_id
                        ),
                        readme,
                    )
        instruction_items = set(
            technical_ids(wave.value("execution_instructions"), "I")
        )
        if instruction_items and instruction_items != assigned_items:
            add_error(
                report,
                "wave_instruction_item_conflict",
                "{0} execution instructions reference {1}; assigned items are {2}."
                .format(
                    wave.wave_id,
                    ", ".join(sorted(instruction_items)),
                    ", ".join(sorted(assigned_items)),
                ),
                readme,
            )
        for reference in technical_ids(wave.value("execution_instructions"), "W"):
            if reference not in wave_positions:
                add_error(
                    report,
                    "unknown_wave_instruction",
                    "{0} execution instructions reference unknown wave {1}.".format(
                        wave.wave_id, reference
                    ),
                    readme,
                )
            elif wave_positions[reference] > index - 1:
                add_error(
                    report,
                    "future_wave_instruction",
                    "{0} execution instructions reference later wave {1}.".format(
                        wave.wave_id, reference
                    ),
                    readme,
                )
        ownership_refs = set(
            technical_ids(wave.value("ownership_boundaries"), "I")
        )
        if ownership_refs - assigned_items:
            add_error(
                report,
                "wave_ownership_conflict",
                "{0} ownership boundaries reference items outside the wave: {1}."
                .format(
                    wave.wave_id,
                    ", ".join(sorted(ownership_refs - assigned_items)),
                ),
                readme,
            )
        for item in wave.items:
            if item.item_id in seen_items:
                add_error(
                    report,
                    "duplicate_item",
                    "Duplicate item ID: {0}".format(item.item_id),
                    readme,
                )
            seen_items.add(item.item_id)
            item_ownership_refs = set(technical_ids(item.value("ownership"), "I"))
            if item_ownership_refs - {item.item_id}:
                add_error(
                    report,
                    "item_ownership_conflict",
                    "{0} ownership references another item: {1}.".format(
                        item.item_id,
                        ", ".join(sorted(item_ownership_refs - {item.item_id})),
                    ),
                    readme,
                )
            item_fields = required_item_fields
            if compact and len(wave.items) > 1:
                item_fields = required_item_fields + ("ownership",)
            for field_id in item_fields:
                if not item.value(field_id):
                    add_error(
                        report,
                        "item_field",
                        "{0} is missing field {1}.".format(item.item_id, field_id),
                        readme,
                    )
    for section in plan.sections.values():
        if not section.custom and (
            section.scope != "global" or section.wave_ids or section.item_ids
        ):
            add_error(
                report,
                "standard_section_scope",
                "Standard section {0} must remain global.".format(section.section_id),
                readme,
            )
    for section in plan.custom_sections():
        for message in section.marker_errors:
            add_error(
                report,
                "custom_section_scope",
                "Custom section {0}: {1}".format(section.section_id, message),
                readme,
            )
        for wave_id in section.wave_ids:
            if not re.fullmatch(r"W\d{3}", wave_id) or wave_id not in wave_positions:
                add_error(
                    report,
                    "custom_section_wave",
                    "Custom section {0} references unknown wave {1}.".format(
                        section.section_id, wave_id
                    ),
                    readme,
                )
        for item_id in section.item_ids:
            if not re.fullmatch(r"I\d{3}", item_id) or item_id not in item_to_wave:
                add_error(
                    report,
                    "custom_section_item",
                    "Custom section {0} references unknown item {1}.".format(
                        section.section_id, item_id
                    ),
                    readme,
                )
    return seen_items


def _validate_prompts(
    report: dict[str, Any],
    package: Path,
    plan: PlanIR,
    digest: str,
) -> None:
    prompts = package / "prompts"
    expected_names = {
        "wave-{0:02d}.md".format(index)
        for index in range(1, len(plan.waves) + 1)
    }
    actual_names = (
        {path.name for path in prompts.glob("wave-*.md")}
        if prompts.is_dir() else set()
    )
    missing = sorted(expected_names - actual_names)
    extra = sorted(actual_names - expected_names)
    if missing:
        add_error(
            report, "missing_prompts", "Missing prompts: {0}".format(", ".join(missing)),
            prompts,
        )
    if extra:
        add_conflict(
            report, "extra_prompts", "Obsolete prompts: {0}".format(", ".join(extra)),
            prompts,
        )
    for index, wave in enumerate(plan.waves, start=1):
        prompt = prompts / "wave-{0:02d}.md".format(index)
        if not prompt.is_file():
            continue
        prompt_text = read_text(prompt)
        try:
            prompt_meta = frontmatter(prompt_text)
        except ValidationFailure as exc:
            add_error(report, "prompt_frontmatter", str(exc), prompt)
            continue
        assignment = _assignment_metadata(plan, wave)
        expected = {
            "artifact": "wop-wave-prompt",
            "plan_id": plan.metadata.get("plan_id"),
            "plan_version": plan.metadata.get("version"),
            "plan_title": plan.metadata.get("title"),
            "wave_id": wave.wave_id,
            "authorized_items": assignment["authorized_items"],
            "non_authorized_items": assignment["non_authorized_items"],
            "predecessor_waves": assignment["predecessor_waves"],
            "blocked_successor_waves": assignment["blocked_successor_waves"],
            "language": plan.metadata.get("language"),
            "source_readme": "README.md",
            "source_readme_sha256": digest,
        }
        for key, expected_value in expected.items():
            if prompt_meta.get(key) != expected_value:
                add_conflict(
                    report,
                    "prompt_metadata",
                    "{0} is stale or incorrect; expected {1!r}.".format(
                        key, expected_value
                    ),
                    prompt,
                )
        expected_prompt = generate_wave_prompt(plan, wave, digest)
        if prompt_text != expected_prompt:
            add_conflict(
                report,
                "prompt_content",
                "Prompt content is not the exact source-derived rendering for its wave.",
                prompt,
            )
        for marker_id in (
            "global_protocol", "execution_scope", "predecessor_verification",
            "shared_context", "completion_contract",
        ):
            if prompt_marker(marker_id) not in prompt_text:
                add_error(
                    report,
                    "prompt_structure",
                    "Prompt is missing structural marker {0}.".format(marker_id),
                    prompt,
                )
        assigned_markers = set(
            re.findall(
                r"<!--[ \t]*wop:prompt-assigned-item[ \t]+(I\d{3})[ \t]*-->",
                prompt_text,
            )
        )
        expected_assigned = {item.item_id for item in wave.items}
        if assigned_markers != expected_assigned:
            add_error(
                report,
                "prompt_item_assignment",
                "Prompt assigned-item markers are {0}; expected {1}.".format(
                    ", ".join(sorted(assigned_markers)) or "none",
                    ", ".join(sorted(expected_assigned)) or "none",
                ),
                prompt,
            )
        for item in wave.items:
            if item.item_id not in prompt_text:
                add_error(
                    report,
                    "prompt_item_coverage",
                    "Prompt omits assigned item {0}.".format(item.item_id),
                    prompt,
                )
        for predecessor in plan.predecessors(wave):
            if predecessor.wave_id not in prompt_text:
                add_error(
                    report,
                    "prompt_predecessor",
                    "Prompt omits predecessor {0}.".format(predecessor.wave_id),
                    prompt,
                )
            for item in predecessor.items:
                if item.item_id not in prompt_text:
                    add_error(
                        report,
                        "prompt_predecessor_item",
                        "Prompt omits predecessor producer {0}.".format(item.item_id),
                        prompt,
                    )
    execute_all = prompts / "execute-all.md"
    if not execute_all.is_file():
        add_error(report, "execute_all", "Missing execute-all.md.", execute_all)
        return
    master = read_text(execute_all)
    try:
        master_meta = frontmatter(master)
        for key, expected_value in (
            ("artifact", "wop-execute-all"),
            ("plan_id", plan.metadata.get("plan_id")),
            ("plan_version", plan.metadata.get("version")),
            ("language", plan.metadata.get("language")),
            ("source_readme", "README.md"),
            ("source_readme_sha256", digest),
        ):
            if master_meta.get(key) != expected_value:
                add_conflict(
                    report,
                    "execute_all_metadata",
                    "{0} is stale or incorrect.".format(key),
                    execute_all,
                )
    except ValidationFailure as exc:
        add_error(report, "execute_all_frontmatter", str(exc), execute_all)
    expected_master = generate_execute_all(plan, digest)
    if master != expected_master:
        add_conflict(
            report,
            "execute_all_content",
            "execute-all content is not the exact source-derived rendering.",
            execute_all,
        )
    for marker_id in ("wave_prompts", "orchestration"):
        if prompt_marker(marker_id) not in master:
            add_error(
                report,
                "execute_all_structure",
                "execute-all is missing marker {0}.".format(marker_id),
                execute_all,
            )
    positions: list[int] = []
    for name in sorted(expected_names):
        reference = "prompts/{0}".format(name)
        position = master.find(reference)
        if position < 0:
            add_error(
                report,
                "execute_all_reference",
                "Missing reference: {0}".format(reference),
                execute_all,
            )
        else:
            positions.append(position)
            if not (package / reference).is_file():
                add_error(
                    report,
                    "broken_reference",
                    "Reference does not exist: {0}".format(reference),
                    execute_all,
                )
    if positions != sorted(positions):
        add_error(
            report,
            "execute_all_order",
            "Wave prompt references are not in wave order.",
            execute_all,
        )


def _database_cycles(conn: sqlite3.Connection) -> list[list[str]]:
    graph: dict[str, set[str]] = {}
    for row in conn.execute(
        "SELECT source_plan_id,target_plan_id FROM plan_relations "
        "WHERE relation_type='depends_on'"
    ):
        graph.setdefault(row["source_plan_id"], set()).add(row["target_plan_id"])
        graph.setdefault(row["target_plan_id"], set())
    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in active_set:
            start = active.index(node)
            cycles.append(active[start:] + [node])
            return
        if node in visited:
            return
        active.append(node)
        active_set.add(node)
        for target in graph.get(node, set()):
            visit(target)
        active.pop()
        active_set.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def _package_hash(package: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        path for path in package.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in (".pyc", ".sqlite3")
        and not path.name.startswith((
            ".generate-prompts-", ".previous-prompts-", ".failed-prompts-"
        ))
    )
    for path in files:
        digest.update(path.relative_to(package).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_database(
    report: dict[str, Any],
    package: Path,
    root: Path,
    plan: PlanIR,
) -> None:
    db = root.resolve() / ".wop" / "wop.sqlite3"
    if not db.exists() or not plan.metadata.get("plan_id"):
        return
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        row = conn.execute(
            "SELECT * FROM plans WHERE plan_id=?", (plan.metadata["plan_id"],)
        ).fetchone()
        if row is None:
            add_warning(
                report,
                "database_missing",
                "Package is not registered in SQLite.",
                db,
            )
        else:
            expected_path = package.relative_to(root.resolve()).as_posix()
            if row["current_relative_path"] != expected_path:
                add_conflict(
                    report, "database_path", "SQLite path differs from package path.", db
                )
            for key in (
                "plan_id", "title", "created_at", "updated_at", "version",
                "language", "complexity", "plan_status", "execution_status",
                "acceptance_status",
            ):
                if str(row[key]) != str(plan.metadata.get(key)):
                    add_conflict(
                        report,
                        "database_metadata",
                        "SQLite {0} differs from README projection.".format(key),
                        db,
                    )
            if row["current_directory_name"] != package.name:
                add_conflict(
                    report,
                    "database_directory",
                    "SQLite directory name differs from filesystem.",
                    db,
                )
            if row["content_hash"] != _package_hash(package):
                add_conflict(
                    report,
                    "database_hash",
                    "SQLite artifact hash differs from the package.",
                    db,
                )
        relation_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        if relation_issues:
            add_error(
                report,
                "relationship_integrity",
                "Database foreign-key integrity failed.",
                db,
            )
        for cycle in _database_cycles(conn):
            add_conflict(
                report,
                "dependency_cycle",
                "depends_on cycle: {0}".format(" -> ".join(cycle)),
                db,
            )
        tombstone = conn.execute(
            "SELECT 1 FROM plan_tombstones WHERE plan_id=?",
            (plan.metadata["plan_id"],),
        ).fetchone()
        if tombstone:
            add_conflict(
                report, "tombstone_reuse", "README reuses a tombstoned plan ID.", db
            )
        conn.close()
    except sqlite3.Error as exc:
        add_error(report, "database_error", str(exc), db)


def audit_profile_for(plan: PlanIR) -> dict[str, str]:
    """Return the audit depth without changing universal correctness rules."""
    complexity = plan.metadata.get("complexity", "standard")
    has_parallel_wave = any(len(wave.items) > 1 for wave in plan.waves)
    if complexity == "compact":
        independence = (
            "when_multiple_items" if has_parallel_wave else "not_applicable_single_item"
        )
        return {
            "complexity": "compact",
            "planning": "essential",
            "independence": independence,
            "coverage": "direct_verification",
            "writing": "essential",
            "risk_analysis": "when_relevant",
            "recovery_analysis": "when_relevant",
            "final_acceptance": "mandatory",
            "workspace_integrity": "mandatory",
            "reporting": "concise_unless_findings_exist",
        }
    if complexity == "extensive":
        return {
            "complexity": "extensive",
            "planning": "detailed",
            "independence": "pairwise_with_isolation_analysis",
            "coverage": "full_traceability",
            "writing": "complete",
            "risk_analysis": "detailed",
            "recovery_analysis": "detailed_when_applicable",
            "final_acceptance": "mandatory",
            "workspace_integrity": "mandatory",
            "reporting": "detailed_evidence",
        }
    return {
        "complexity": "standard",
        "planning": "complete",
        "independence": "pairwise" if has_parallel_wave else "per_wave",
        "coverage": "traceability_matrix",
        "writing": "complete",
        "risk_analysis": "domain_dependent",
        "recovery_analysis": "risk_dependent",
        "final_acceptance": "mandatory",
        "workspace_integrity": "mandatory",
        "reporting": "findings_and_evidence",
    }


def semantic_review_for(plan: PlanIR) -> list[str]:
    """Scale review presentation while preserving all universal invariants."""
    complexity = plan.metadata.get("complexity", "standard")
    has_parallel_wave = any(len(wave.items) > 1 for wave in plan.waves)
    shared = [
        "Confirm the global protocol is universal, each wave authorizes exactly "
        "its assigned work, and scoped context reaches only its intended prompts.",
        "Confirm generated prompts contain all execution-critical context and do "
        "not contradict technical authorization metadata.",
        "Confirm plan-authored prose consistently uses the declared language; "
        "technical literals and identifiers may remain unchanged.",
        "Confirm final acceptance proves the requested outcome from observable "
        "item and wave criteria.",
    ]
    if complexity == "compact":
        result = [
            "Confirm direct coverage from the outcome and deliverables to each item, "
            "its output, verification, and final acceptance."
        ]
        if has_parallel_wave:
            result.append(
                "Confirm every same-wave item pair is genuinely independent and "
                "has non-interfering ownership."
            )
        result.extend(shared)
        result.append(
            "Confirm risk and recovery detail was added only where task consequences "
            "make it relevant."
        )
        return result
    result = [
        "Confirm same-wave items are genuinely independent and non-interfering.",
        "Confirm item objectives cover each wave objective.",
        "Confirm item criteria logically imply each wave acceptance gate.",
        "Confirm every material requirement is traceable to work and evidence.",
    ]
    result.extend(shared)
    result.append(
        "Confirm risk and recovery depth matches domain consequences and reversibility."
    )
    if complexity == "extensive":
        result.extend(
            [
                "Confirm pairwise isolation covers shared resources, external effects, "
                "integration, and multi-agent coordination.",
                "Confirm detailed risks, stakeholders, operational controls, rollback, "
                "and recovery have owners, triggers, evidence, and authority boundaries.",
            ]
        )
    return result


def validate_package(
    package: Path,
    root: Optional[Path] = None,
    check_database: bool = True,
) -> dict[str, Any]:
    package = package.resolve()
    report: dict[str, Any] = {
        "valid": False,
        "integrity_status": "unchecked",
        "package": str(package),
        "errors": [],
        "warnings": [],
        "mechanical_checks": [],
        "audit_profile": {},
        "universal_audit_invariants": list(UNIVERSAL_AUDIT_INVARIANTS),
        "semantic_review_required": [],
    }
    readme = package / "README.md"
    if not package.is_dir():
        report["integrity_status"] = "missing"
        add_error(report, "missing_package", "Package directory does not exist.", package)
        return report
    if not DIRECTORY_PATTERN.fullmatch(package.name):
        add_error(
            report,
            "directory_name",
            "Directory must match YYYY_MM_DD_hh_mm_ss-name_snake_case.",
            package,
        )
    if not readme.is_file():
        report["integrity_status"] = "missing"
        add_error(report, "missing_readme", "README.md is required.", readme)
        return report
    try:
        text = read_text(readme)
        plan = parse_readme(text)
    except ValidationFailure as exc:
        report["integrity_status"] = "invalid"
        add_error(report, "plan_parse", str(exc), readme)
        return report
    report["mechanical_checks"].append(
        "README parsed into the language-neutral Plan Intermediate Representation"
    )
    report["audit_profile"] = audit_profile_for(plan)
    report["semantic_review_required"] = semantic_review_for(plan)
    _validate_metadata(report, plan.metadata, readme)
    seen_items = _validate_ir(report, plan, readme)
    digest = readme_digest(text)
    _validate_prompts(report, package, plan, digest)
    if check_database and root is not None:
        _validate_database(report, package, root, plan)
    report["valid"] = not report["errors"]
    if report["valid"]:
        report["integrity_status"] = "valid"
    elif any(error.get("status") == "conflict" for error in report["errors"]):
        report["integrity_status"] = "conflict"
    else:
        report["integrity_status"] = "invalid"
    report["mechanical_checks"].extend(
        [
            "Validated {0} structural sections".format(len(plan.sections)),
            "Validated {0} waves".format(len(plan.waves)),
            "Validated {0} work items".format(len(seen_items)),
            "Validated prompt count, language, exact assignments, metadata, source hash, and references",
            "Validated global protocol, dependency direction, ownership references, and custom context selectors",
            "Validated exact source-derived prompt content without translation catalogs",
        ]
    )
    return report


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description=__doc__)
    main.add_argument("--root", required=True, type=Path, help="Project root")
    main.add_argument("--directory", required=True, help="Plan package path")
    main.add_argument(
        "--generate-prompts",
        action="store_true",
        help="Atomically regenerate wave prompts and execute-all.md before validation",
    )
    main.add_argument("--json", action="store_true", help="Emit JSON")
    main.add_argument(
        "--skip-database", action="store_true", help="Skip SQLite consistency checks"
    )
    return main


def resolve_cli_package(root: Path, directory: str) -> Path:
    package = Path(directory)
    if not package.is_absolute():
        package = root / package
    package = package.resolve()
    allowed_parents = {
        (root / ".wop" / "plans").resolve(),
        (root / ".wop" / "archive").resolve(),
    }
    if package.parent not in allowed_parents:
        raise ValidationFailure(
            "Package must be a direct child of PROJECT/.wop/plans or "
            "PROJECT/.wop/archive."
        )
    return package


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        package = resolve_cli_package(root, args.directory)
        generated = generate_prompts(package) if args.generate_prompts else None
        report = validate_package(
            package, root=root, check_database=not args.skip_database
        )
        if generated:
            report["generation"] = generated
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("valid: {0}".format(report["valid"]))
            print("integrity_status: {0}".format(report["integrity_status"]))
            profile = report.get("audit_profile", {})
            if profile:
                print(
                    "audit_profile: {0} ({1}; {2})".format(
                        profile.get("complexity"),
                        profile.get("planning"),
                        profile.get("reporting"),
                    )
                )
            for error in report["errors"]:
                print(
                    "ERROR {0} [{1}]: {2}".format(
                        error["code"], error.get("status", "invalid"), error["message"]
                    )
                )
            for warning in report["warnings"]:
                print("WARNING {0}: {1}".format(warning["code"], warning["message"]))
            print("Semantic review is required:")
            for item in report["semantic_review_required"]:
                print("- {0}".format(item))
        return 0 if report["valid"] else 2
    except (ValidationFailure, OSError, sqlite3.Error, UnicodeError) as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "valid": False,
                        "integrity_status": "unchecked",
                        "error": str(exc),
                    }
                ),
                file=sys.stderr,
            )
        else:
            print("error: {0}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
