#!/usr/bin/env python3
"""Language-neutral Markdown parser and intermediate representation for WOP plans."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple


HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
MARKER_RE = re.compile(
    r"<!--[ \t]*wop:(section|wave|item|field)[ \t]+([A-Za-z0-9_-]+)"
    r"(?P<attributes>.*?)[ \t]*-->",
    re.IGNORECASE,
)
MARKER_ATTRIBUTE_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)=([^\s]+)")
LANGUAGE_TAG_RE = re.compile(
    r"^(?:[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*|"
    r"[A-Za-z](?:-[A-Za-z0-9]{1,8})+)$"
)


# These aliases preserve plans created before structural markers were introduced.
# They are compatibility shims, not a list of supported generation languages. Any
# language is structurally supported when visible headings carry wop:* markers.
SECTION_ALIASES = {
    "outcome": ("outcome", "resultado", "resultado esperado", "resultado final"),
    "execution_context": (
        "execution context", "contexto de execucao", "contexto de ejecucion"
    ),
    "confirmed_facts": (
        "confirmed facts", "fatos confirmados", "hechos confirmados"
    ),
    "scope": ("scope", "escopo", "alcance"),
    "stakeholders": (
        "stakeholders", "stakeholders and authority",
        "partes interessadas", "partes interessadas e autoridade",
        "interesados", "interesados y autoridad",
    ),
    "assumptions": ("assumptions", "premissas", "suposicoes", "supuestos"),
    "unknowns": ("unknowns", "desconhecidos", "incertezas", "incognitas"),
    "requirements": ("requirements", "requisitos"),
    "constraints": ("constraints", "restricoes", "restricciones"),
    "decisions": ("decisions", "decisoes", "decisiones"),
    "risks": ("risks", "riscos", "riesgos"),
    "operations": (
        "environments and operations", "operations", "ambientes e operacoes",
        "operacoes", "entornos y operaciones", "operaciones",
    ),
    "global_contracts": (
        "global contracts", "contratos globais", "contratos globales"
    ),
    "wave_sequence": (
        "wave sequence", "sequencia de ondas", "secuencia de ondas"
    ),
    "requirement_traceability": (
        "requirement traceability", "rastreabilidade de requisitos",
        "trazabilidad de requisitos",
    ),
    "dependency_map": (
        "dependency map", "mapa de dependencias", "mapa de dependencias"
    ),
    "verification_strategy": (
        "verification strategy", "estrategia de verificacao",
        "estrategia de verificacion",
    ),
    "rollback_recovery": (
        "rollback and recovery", "rollback e recuperacao",
        "reversao e recuperacao", "rollback y recuperacion",
    ),
    "final_acceptance": (
        "final acceptance", "aceite final", "aceitacao final", "aceptacion final"
    ),
    "execution_protocol": (
        "execution protocol", "protocolo de execucao", "protocolo de ejecucion"
    ),
    "revision_history": (
        "revision history", "historico de revisoes", "historial de revisiones"
    ),
}

FIELD_ALIASES = {
    "general_objective": ("general objective", "objetivo geral", "objetivo general"),
    "prerequisites": ("prerequisites", "pre-requisitos", "prerrequisitos"),
    "requirements_addressed": (
        "requirements addressed", "requisitos atendidos", "requisitos abordados"
    ),
    "general_acceptance_criteria": (
        "general acceptance criteria", "criterios gerais de aceite",
        "criterios generales de aceptacion",
    ),
    "completion_gate": (
        "completion gate", "portao de conclusao", "puerta de finalizacion"
    ),
    "evidence_requirements": (
        "evidence requirements", "requisitos de evidencia", "requisitos de evidencia"
    ),
    "parallelism_rationale": (
        "parallelism rationale", "justificativa de paralelismo",
        "justificacion de paralelismo",
    ),
    "ownership_boundaries": (
        "ownership boundaries", "limites de ownership", "limites de propriedade",
        "limites de propiedad",
    ),
    "execution_instructions": (
        "wave execution instructions", "execution instructions",
        "instrucoes de execucao da onda", "instrucoes de execucao",
        "instrucciones de ejecucion de la ola", "instrucciones de ejecucion",
    ),
    "integration_handoff": (
        "integration and handoff", "integracao e handoff", "integracao e transferencia",
        "integracion y transferencia",
    ),
    "objective": ("objective", "objetivo"),
    "context": ("context", "contexto"),
    "inputs_prerequisites": (
        "inputs and prerequisites", "entradas e pre-requisitos",
        "insumos y prerrequisitos",
    ),
    "scope": ("scope", "escopo", "alcance"),
    "ownership": ("ownership", "propriedade", "responsabilidade"),
    "outputs": ("outputs", "saidas", "resultados"),
    "acceptance_criteria": (
        "acceptance criteria", "criterios de aceite", "criterios de aceptacion"
    ),
    "restrictions": ("restrictions", "restricoes", "restricciones"),
    "verification_evidence": (
        "verification evidence", "evidencias de verificacao",
        "evidencia de verificacion",
    ),
    "handoff_requirements": (
        "handoff requirements", "requisitos de handoff",
        "requisitos de transferencia",
    ),
}

REQUIRED_SECTION_IDS = (
    "outcome", "execution_context", "confirmed_facts", "assumptions", "unknowns",
    "requirements", "global_contracts", "wave_sequence",
    "requirement_traceability", "dependency_map", "verification_strategy",
    "final_acceptance", "execution_protocol", "revision_history",
)
COMPACT_REQUIRED_SECTION_IDS = (
    "outcome", "wave_sequence", "verification_strategy", "final_acceptance",
    "execution_protocol", "revision_history",
)
STANDARD_REQUIRED_SECTION_IDS = (
    "outcome", "execution_context", "requirements", "wave_sequence",
    "requirement_traceability", "verification_strategy", "final_acceptance",
    "execution_protocol", "revision_history",
)
REQUIRED_WAVE_FIELD_IDS = (
    "general_objective", "prerequisites", "requirements_addressed",
    "general_acceptance_criteria", "completion_gate", "evidence_requirements",
    "parallelism_rationale", "ownership_boundaries", "integration_handoff",
)
COMPACT_REQUIRED_WAVE_FIELD_IDS = (
    "general_objective", "general_acceptance_criteria", "completion_gate",
)
REQUIRED_ITEM_FIELD_IDS = (
    "objective", "context", "inputs_prerequisites", "scope", "ownership",
    "outputs", "acceptance_criteria", "restrictions",
    "verification_evidence", "handoff_requirements",
)
COMPACT_REQUIRED_ITEM_FIELD_IDS = (
    "objective", "scope", "outputs", "acceptance_criteria",
)
CONTEXT_SECTION_IDS = (
    "outcome", "execution_context", "confirmed_facts", "scope", "stakeholders",
    "requirements", "constraints", "decisions", "assumptions", "unknowns",
    "risks", "operations", "global_contracts", "dependency_map",
    "requirement_traceability", "verification_strategy", "rollback_recovery",
    "final_acceptance",
)
ORCHESTRATION_SECTION_IDS = (
    "outcome", "execution_context", "confirmed_facts", "scope", "stakeholders",
    "requirements", "constraints", "decisions", "assumptions", "unknowns",
    "risks", "operations", "global_contracts", "wave_sequence", "dependency_map",
    "requirement_traceability", "verification_strategy", "rollback_recovery",
    "final_acceptance", "execution_protocol",
)


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def technical_ids(value: str, prefix: str) -> list[str]:
    """Find WOP IDs without treating adjacent non-Latin text as an ID character."""
    pattern = r"(?<![A-Za-z0-9_]){0}\d{{3}}(?![A-Za-z0-9_])".format(
        re.escape(prefix)
    )
    return [match.upper() for match in re.findall(pattern, value, re.IGNORECASE)]


def is_language_tag(value: str) -> bool:
    """Accept structurally valid BCP 47-style tags without a language registry."""
    return bool(value and len(value) <= 63 and LANGUAGE_TAG_RE.fullmatch(value))


def select_language(
    explicit_user_language: Optional[str],
    predominant_conversation_language: Optional[str],
) -> str:
    """Apply WOP's language hierarchy to already identified language tags."""
    if explicit_user_language and explicit_user_language.strip():
        selected = explicit_user_language.strip()
    elif predominant_conversation_language and predominant_conversation_language.strip():
        selected = predominant_conversation_language.strip()
    else:
        selected = "en"
    if not is_language_tag(selected):
        raise ValueError("Invalid language tag: {0}".format(selected))
    return selected


SECTION_LOOKUP = {
    normalize_label(alias): section_id
    for section_id, aliases in SECTION_ALIASES.items()
    for alias in aliases
}
FIELD_LOOKUP = {
    normalize_label(alias): field_id
    for field_id, aliases in FIELD_ALIASES.items()
    for alias in aliases
}


@dataclass
class Heading:
    level: int
    title: str
    marker_type: Optional[str]
    marker_id: Optional[str]
    marker_attributes: dict[str, str]
    marker_errors: list[str]
    start: int
    end: int


@dataclass
class SectionIR:
    section_id: str
    title: str
    content: str
    raw: str
    scope: str = "global"
    wave_ids: tuple[str, ...] = ()
    item_ids: tuple[str, ...] = ()
    custom: bool = False
    marker_errors: tuple[str, ...] = ()


@dataclass
class ItemIR:
    item_id: str
    title: str
    name: str
    fields: dict[str, SectionIR]
    raw: str

    def value(self, field_id: str) -> str:
        value = self.fields.get(field_id)
        return value.content if value else ""


@dataclass
class WaveIR:
    wave_id: str
    title: str
    name: str
    fields: dict[str, SectionIR]
    items: list[ItemIR]
    raw: str

    def value(self, field_id: str) -> str:
        value = self.fields.get(field_id)
        return value.content if value else ""


@dataclass
class PlanIR:
    metadata: dict[str, str]
    title: str
    sections: dict[str, SectionIR]
    extra_sections: list[SectionIR]
    waves: list[WaveIR]
    raw_body: str
    warnings: list[str] = field(default_factory=list)

    def section(self, section_id: str) -> Optional[SectionIR]:
        return self.sections.get(section_id)

    def wave(self, wave_id: str) -> Optional[WaveIR]:
        for wave in self.waves:
            if wave.wave_id == wave_id:
                return wave
        return None

    def predecessors(self, wave: WaveIR) -> list[WaveIR]:
        references = technical_ids(wave.value("prerequisites"), "W")
        result: list[WaveIR] = []
        for reference in references:
            predecessor = self.wave(reference)
            if predecessor and predecessor.wave_id != wave.wave_id and predecessor not in result:
                result.append(predecessor)
        return result

    def context_sections(self, wave: WaveIR) -> list[SectionIR]:
        result = [
            self.sections[section_id]
            for section_id in CONTEXT_SECTION_IDS
            if section_id in self.sections
        ]
        item_ids = {item.item_id for item in wave.items}
        for section in self.custom_sections():
            if section.scope == "global":
                result.append(section)
            elif section.scope == "wave" and wave.wave_id in section.wave_ids:
                result.append(section)
            elif section.scope == "item" and item_ids.intersection(section.item_ids):
                result.append(section)
        return result

    def orchestration_sections(self) -> list[SectionIR]:
        result = [
            self.sections[section_id]
            for section_id in ORCHESTRATION_SECTION_IDS
            if section_id in self.sections
        ]
        result.extend(
            section for section in self.custom_sections()
            if section.scope == "global"
        )
        return result

    def custom_sections(self) -> list[SectionIR]:
        result = [section for section in self.sections.values() if section.custom]
        result.extend(self.extra_sections)
        return result


class PlanParseError(RuntimeError):
    """The plan cannot be converted into a reliable intermediate representation."""


def split_frontmatter(text: str) -> Tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PlanParseError("README must start with YAML front matter.")
    metadata: dict[str, str] = {}
    closing: Optional[int] = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing = index
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise PlanParseError("Unsupported YAML line: {0}".format(line))
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    if closing is None:
        raise PlanParseError("README front matter is not closed.")
    return metadata, "\n".join(lines[closing + 1:]).lstrip()


def _headings(body: str) -> list[Heading]:
    result: list[Heading] = []
    for match in HEADING_RE.finditer(body):
        raw_title = match.group(2).strip()
        marker = MARKER_RE.search(raw_title)
        clean = MARKER_RE.sub("", raw_title).strip()
        attributes: dict[str, str] = {}
        attribute_errors: list[str] = []
        if marker:
            attribute_text = marker.group("attributes").strip()
            cursor = 0
            for attribute in MARKER_ATTRIBUTE_RE.finditer(attribute_text):
                if attribute_text[cursor:attribute.start()].strip():
                    attribute_errors.append(
                        "Malformed marker attributes: {0}".format(attribute_text)
                    )
                    break
                key = attribute.group(1).lower()
                if key in attributes:
                    attribute_errors.append("Duplicate marker attribute: {0}".format(key))
                attributes[key] = attribute.group(2)
                cursor = attribute.end()
            if attribute_text[cursor:].strip():
                attribute_errors.append(
                    "Malformed marker attributes: {0}".format(attribute_text)
                )
        result.append(
            Heading(
                level=len(match.group(1)),
                title=clean,
                marker_type=marker.group(1).lower() if marker else None,
                marker_id=marker.group(2) if marker else None,
                marker_attributes=attributes,
                marker_errors=attribute_errors,
                start=match.start(),
                end=match.end(),
            )
        )
    return result


def _end_for(headings: Sequence[Heading], index: int, body_length: int) -> int:
    current = headings[index]
    for later in headings[index + 1:]:
        if later.level <= current.level:
            return later.start
    return body_length


def _content(body: str, heading: Heading, end: int) -> str:
    return body[heading.end:end].strip()


def _entity_name(title: str, entity_id: str) -> str:
    position = title.find(entity_id)
    if position >= 0:
        remainder = title[position + len(entity_id):].strip()
        remainder = re.sub(r"^(?:—|–|-|:)[ \t]*", "", remainder)
        if remainder:
            return remainder
    return title


def _fallback_entity_id(title: str, prefix: str) -> Optional[str]:
    identifiers = technical_ids(title, prefix)
    return identifiers[0] if identifiers else None


def _section_id(heading: Heading) -> Optional[str]:
    if heading.marker_type == "section" and heading.marker_id:
        return heading.marker_id.lower()
    return SECTION_LOOKUP.get(normalize_label(heading.title))


def _field_id(heading: Heading) -> Optional[str]:
    if heading.marker_type == "field" and heading.marker_id:
        return heading.marker_id.lower()
    return FIELD_LOOKUP.get(normalize_label(heading.title))


def _selector_ids(value: str) -> tuple[str, ...]:
    return tuple(
        identifier.strip().upper()
        for identifier in value.split(",")
        if identifier.strip()
    )


def _section_scope(
    heading: Heading,
) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    attributes = heading.marker_attributes
    errors = list(heading.marker_errors)
    unknown = sorted(set(attributes) - {"scope", "waves", "items"})
    if unknown:
        errors.append("Unknown section marker attributes: {0}".format(", ".join(unknown)))
    scope = attributes.get("scope", "global").lower()
    wave_ids = _selector_ids(attributes.get("waves", ""))
    item_ids = _selector_ids(attributes.get("items", ""))
    if scope not in ("global", "wave", "item"):
        errors.append("Invalid section scope: {0}".format(scope))
    elif scope == "global" and (wave_ids or item_ids):
        errors.append("Global sections cannot declare wave or item selectors.")
    elif scope == "wave":
        if not wave_ids:
            errors.append("Wave-scoped sections must declare waves=.")
        if item_ids:
            errors.append("Wave-scoped sections cannot declare items=.")
    elif scope == "item":
        if not item_ids:
            errors.append("Item-scoped sections must declare items=.")
        if wave_ids:
            errors.append("Item-scoped sections cannot declare waves=.")
    return scope, wave_ids, item_ids, tuple(errors)


def _parse_fields(
    body: str,
    headings: Sequence[Heading],
    expected_level: int,
) -> dict[str, SectionIR]:
    fields: dict[str, SectionIR] = {}
    for index, heading in enumerate(headings):
        if heading.level != expected_level:
            continue
        field_id = _field_id(heading)
        if not field_id:
            continue
        end = _end_for(headings, index, len(body))
        if expected_level == 3:
            for later in headings[index + 1:]:
                if later.level <= heading.level:
                    break
                is_item = later.level == 4 and (
                    later.marker_type == "item"
                    or _fallback_entity_id(later.title, "I") is not None
                )
                if is_item:
                    end = later.start
                    break
        fields[field_id] = SectionIR(
            field_id,
            heading.title,
            _content(body, heading, end),
            body[heading.start:end].strip(),
        )
    return fields


def _parse_items(wave_body: str) -> list[ItemIR]:
    headings = _headings(wave_body)
    result: list[ItemIR] = []
    for index, heading in enumerate(headings):
        if heading.level != 4:
            continue
        item_id = (
            heading.marker_id.upper()
            if heading.marker_type == "item" and heading.marker_id
            else _fallback_entity_id(heading.title, "I")
        )
        if not item_id:
            continue
        end = _end_for(headings, index, len(wave_body))
        raw = wave_body[heading.start:end].strip()
        result.append(
            ItemIR(
                item_id=item_id,
                title=heading.title,
                name=_entity_name(heading.title, item_id),
                fields=_parse_fields(raw, _headings(raw), 5),
                raw=raw,
            )
        )
    return result


def parse_plan(text: str) -> PlanIR:
    metadata, body = split_frontmatter(text)
    headings = _headings(body)
    title = next((heading.title for heading in headings if heading.level == 1), "")
    sections: dict[str, SectionIR] = {}
    extras: list[SectionIR] = []
    waves: list[WaveIR] = []
    warnings: list[str] = []
    for heading in headings:
        if heading.marker_type != "section" and heading.marker_attributes:
            warnings.append(
                "Marker attributes are supported only on plan sections: {0}".format(
                    heading.title
                )
            )
        if heading.marker_type != "section":
            warnings.extend(heading.marker_errors)
    for index, heading in enumerate(headings):
        if heading.level != 2:
            continue
        end = _end_for(headings, index, len(body))
        raw = body[heading.start:end].strip()
        wave_id = (
            heading.marker_id.upper()
            if heading.marker_type == "wave" and heading.marker_id
            else _fallback_entity_id(heading.title, "W")
        )
        if wave_id:
            waves.append(
                WaveIR(
                    wave_id=wave_id,
                    title=heading.title,
                    name=_entity_name(heading.title, wave_id),
                    fields=_parse_fields(raw, _headings(raw), 3),
                    items=_parse_items(raw),
                    raw=raw,
                )
            )
            continue
        section_id = _section_id(heading)
        scope, wave_ids, item_ids, scope_errors = _section_scope(heading)
        custom = section_id not in SECTION_ALIASES if section_id else True
        section = SectionIR(
            section_id or "unclassified",
            heading.title,
            _content(body, heading, end),
            raw,
            scope,
            wave_ids,
            item_ids,
            custom,
            scope_errors,
        )
        if section_id:
            if section_id in sections:
                warnings.append("Duplicate section identifier: {0}".format(section_id))
            sections[section_id] = section
        else:
            extras.append(section)
    return PlanIR(metadata, title, sections, extras, waves, body, warnings)


def prompt_marker(marker_id: str) -> str:
    return "<!-- wop:prompt-section {0} -->".format(marker_id)


def prompt_entity_marker(kind: str, identifier: str) -> str:
    return "<!-- wop:prompt-{0} {1} -->".format(kind, identifier)


def structural_marker(kind: str, identifier: str) -> str:
    return "<!-- wop:{0} {1} -->".format(kind, identifier)
