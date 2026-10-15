"""Spec 0030 (lean pipeline), Story 1, success criterion #1: the report total matches the manual dedupe.

Success criterion #1 asks that ``aiadev metrics --tokens`` on a real session
agree "within 1%" with a manual deduplication of the same session. Plan
Article IV says the manual deduplication uses **the same rule** as the code:

* an assistant event counts once per ``message.id``, at the **maximum** of
  each ``usage`` field (streaming ``usage`` is partial and only grows);
* an event without ``message.id`` is unique and is summed on its own;
* the same ``message.id`` in two files (main threads, subagents, or one of
  each) counts once.

``manual_dedupe`` below is that rule written from scratch, in plain Python,
over the JSONL files themselves (the snippet in ``docs/metrics.md`` is the
same procedure). It shares nothing with ``token_metrics``: only the public
``build_token_report`` and the CLI are called, so a bug in the reader cannot
hide behind a reference that has the same bug. The assertions use **exact**
equality, which is stricter than the 1% tolerance of the spec: both sides are
integer sums over the same data, so there is no rounding to absorb.

What is compared is the main thread **plus** the subagents, per usage field,
against the manual sum over every file. How a repeated id is split between
the main thread and a subagent (the main thread claims it first) is attribution,
not the total, and is tested in ``tests/test_token_metrics.py``
(``test_message_id_repeated_between_main_and_subagent_counts_once`` and
``test_message_id_repeated_between_two_subagents_counts_once``).

Spec 0031 (context hygiene), success criterion #1 extends the same comparison to the
context distribution: ``reference_distribution`` below puts every deduplicated request
in a band (``<50k``, ``50k-150k``, ``150k-200k``, ``>200k`` by prompt size, the edges
50.000 / 150.000 / 200.000 / 200.001 included), and the report's bands, main-thread
bands, shares by model and subagent share must equal it. A message counts as main
thread when any of its occurrences is in a main file (the main thread claims first).

The transcripts come from a seeded ``random.Random``, so every run writes the
same files. Each seed keeps a fixed skeleton (every shape of repetition the
spec names is always there) and fills it with random values, filler messages
and a random order inside the files. Layout under the transcripts directory::

    main-a.jsonl, main-b.jsonl                  two sessions that share ids
    main-a/subagents/agent-a1.jsonl, agent-a2.jsonl
    main-a/subagents/workflows/wf_one/agent-w1.jsonl     nested workflow agent
    main-a/subagents/workflows/wf_one/journal.jsonl      not a transcript: never read
    main-b/subagents/agent-b1.jsonl
    orphan/subagents/agent-o1.jsonl                      no orphan.jsonl beside it: never read
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import random
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner

from aiadev import token_metrics as tm
from aiadev.cli import main
from tests.test_token_metrics import _assistant, _write_transcript

# The four usage fields of a transcript event, and the name each one has on
# ``SessionTokens`` / ``SubagentTokens`` (and as a key in the JSON report).
USAGE_KEYS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)
REPORT_FIELD = {
    "input_tokens": "input_tokens",
    "cache_creation_input_tokens": "cache_creation_tokens",
    "cache_read_input_tokens": "cache_read_tokens",
    "output_tokens": "output_tokens",
}

# What a finished message may carry per field (always at least 1, so a
# repetition always has something to over-count).
FINAL_RANGE = {
    "input_tokens": (1, 60),
    "cache_creation_input_tokens": (1, 6_000),
    "cache_read_input_tokens": (1, 90_000),
    "output_tokens": (2, 4_000),
}

MAIN_A = "main-a.jsonl"
MAIN_B = "main-b.jsonl"
AGENT_A1 = "main-a/subagents/agent-a1.jsonl"
AGENT_A2 = "main-a/subagents/agent-a2.jsonl"
AGENT_W1 = "main-a/subagents/workflows/wf_one/agent-w1.jsonl"
AGENT_B1 = "main-b/subagents/agent-b1.jsonl"
AGENT_FILES = (AGENT_A1, AGENT_A2, AGENT_W1, AGENT_B1)
ALL_FILES = (MAIN_A, MAIN_B) + AGENT_FILES
# Not transcripts of any session; each is written with absurd usage on a real id.
NOT_TRANSCRIPTS = ("main-a/subagents/workflows/wf_one/journal.jsonl", "orphan/subagents/agent-o1.jsonl")

SEEDS = list(range(20))

# Models the generated messages are spread over (``<synthetic>`` reads as ``unknown``).
MODELS = ("claude-opus-5", "claude-sonnet-5", "claude-haiku-5", "<synthetic>")

# Prompt sizes of the band skeleton: inside every band and on each edge of the bands.
CONTEXT_TARGETS = (10, 49_999, 50_000, 149_999, 150_000, 200_000, 200_001, 260_000)

# The streaming chain of the spec (output 1, then 40, then 214).
STREAMING_CHAIN = [
    {"input_tokens": 3, "cache_creation_input_tokens": 500, "cache_read_input_tokens": 0, "output_tokens": out}
    for out in (1, 40, 214)
]


# ---------------------------------------------------------------------
# Transcript generator
# ---------------------------------------------------------------------


@dataclasses.dataclass
class Planned:
    """One logical assistant message and the files its occurrences land in (in growth order).

    ``message_id`` is ``None`` for an event without ``message.id``; ``chain``
    fixes the successive partials instead of drawing them.
    """

    message_id: Optional[str]
    files: List[str]
    chain: Optional[List[Dict[str, int]]] = None
    model: Optional[str] = None


def _plan(rng: random.Random) -> List[Planned]:
    """The fixed skeleton (every repetition shape) plus random filler messages."""
    plan = [
        # Streaming partials inside one main thread: output 1 -> 40 -> 214.
        Planned("msg_stream", [MAIN_A, MAIN_A, MAIN_A], STREAMING_CHAIN),
        # A second main session repeating an id of the first (and its own partials).
        Planned("msg_main_twice", [MAIN_A, MAIN_B, MAIN_B]),
        # Main thread and subagent of the same session; the agent holds the larger partial.
        Planned("msg_main_and_agent", [MAIN_A, AGENT_A1, AGENT_A1]),
        # Two subagents of one session and a nested workflow agent.
        Planned("msg_agent_agent", [AGENT_A1, AGENT_A2, AGENT_W1]),
        # Subagents of two different sessions.
        Planned("msg_cross_session_agents", [AGENT_A2, AGENT_B1, AGENT_B1, AGENT_W1]),
        # The second main session and its own subagent.
        Planned("msg_main_b_and_agent", [MAIN_B, AGENT_B1]),
        # Partials only inside a nested workflow agent.
        Planned("msg_nested_only", [AGENT_W1, AGENT_W1, AGENT_W1]),
    ]
    # Events without message.id, in every file.
    for name in ALL_FILES:
        plan.extend(Planned(None, [name]) for _ in range(rng.randint(1, 3)))
    # Random filler: other ids, one to four occurrences each, anywhere.
    for index in range(rng.randint(15, 30)):
        plan.append(Planned(f"msg_filler_{index:02d}", [rng.choice(ALL_FILES) for _ in range(rng.randint(1, 4))]))
    # Context spread over the bands: each target as main only, subagent only and shared by both.
    for index, target in enumerate(CONTEXT_TARGETS):
        main = MAIN_A if index % 2 == 0 else MAIN_B
        agent = rng.choice(AGENT_FILES)
        plan.append(Planned(f"msg_ctx_main_{index}", [main, main], _context_chain(rng, target, 2)))
        plan.append(Planned(f"msg_ctx_agent_{index}", [agent], _context_chain(rng, target, 1)))
        plan.append(Planned(f"msg_ctx_shared_{index}", [agent, main], _context_chain(rng, target, 2)))
        plan.append(Planned(None, [rng.choice(ALL_FILES)], _context_chain(rng, target, 1)))
    return plan


def _context_chain(rng: random.Random, context: int, occurrences: int) -> List[Dict[str, int]]:
    """Partials of one message whose final prompt size (the three input fields) is exactly ``context``.

    Earlier partials are smaller, so the band of a partial is often lower than the final one.
    """
    fresh = rng.randint(0, min(context, 50))
    written = rng.randint(0, min(context - fresh, 6_000))
    final = {
        "input_tokens": fresh,
        "cache_creation_input_tokens": written,
        "cache_read_input_tokens": context - fresh - written,
        "output_tokens": rng.randint(2, 4_000),
    }
    columns = {
        key: sorted(rng.randint(0, final[key]) for _ in range(occurrences - 1)) + [final[key]] for key in USAGE_KEYS
    }
    if occurrences > 1:
        columns["output_tokens"][0] = 1
    return [{key: columns[key][i] for key in USAGE_KEYS} for i in range(occurrences)]


def _chain(rng: random.Random, occurrences: int) -> List[Dict[str, int]]:
    """``occurrences`` partials of one message: every field only grows and ends at a random final value."""
    columns: Dict[str, List[int]] = {}
    for key in USAGE_KEYS:
        last = rng.randint(*FINAL_RANGE[key])
        if occurrences == 1 or rng.random() < 0.4:
            values = [last] * occurrences  # carried unchanged, like input and the cache counters
        else:
            values = sorted(rng.randint(1, last) for _ in range(occurrences - 1)) + [last]
            if key == "output_tokens":
                values[0] = 1  # a stream starts with output_tokens 1
        columns[key] = values
    return [{key: columns[key][i] for key in USAGE_KEYS} for i in range(occurrences)]


def _event(
    second: int, message_id: Optional[str], usage: Dict[str, int], sidechain: bool, model: Optional[str] = None
) -> Dict[str, Any]:
    event = _assistant(
        f"2026-09-16T10:{second // 60:02d}:{second % 60:02d}.000Z",
        message_id=message_id,
        inp=usage["input_tokens"],
        cache_w=usage["cache_creation_input_tokens"],
        cache_r=usage["cache_read_input_tokens"],
        output=usage["output_tokens"],
    )
    if model is not None:
        event["message"]["model"] = model
    return dict(event, isSidechain=True) if sidechain else event


def build_transcripts(root: pathlib.Path, seed: int) -> None:
    """Write the layout from the module docstring under ``root``, deterministically for ``seed``."""
    rng = random.Random(seed)
    events: Dict[str, List[Dict[str, Any]]] = {name: [] for name in ALL_FILES}
    second = 0
    for planned in _plan(rng):
        chain = planned.chain or _chain(rng, len(planned.files))
        planned.model = rng.choice(MODELS)
        for name, usage in zip(planned.files, chain):
            second += 1
            events[name].append(
                _event(second, planned.message_id, usage, sidechain=name in AGENT_FILES, model=planned.model)
            )

    for name, file_events in events.items():
        # main-a keeps the natural streaming order; the other files are shuffled for about half
        # of the seeds, so that "the last occurrence" is not always the largest one.
        if name != MAIN_A and rng.random() < 0.5:
            rng.shuffle(file_events)
        _write_transcript(root / name, file_events)

    canary = {key: 9_999_999 for key in USAGE_KEYS}
    for name in NOT_TRANSCRIPTS:
        _write_transcript(root / name, [_event(0, None, canary, True), _event(1, "msg_stream", canary, True)])


# ---------------------------------------------------------------------
# The manual rule, written independently of token_metrics
# ---------------------------------------------------------------------


@dataclasses.dataclass
class Manual:
    combined: Dict[str, int]  # the manual total, per usage key, over every file
    counted: int  # distinct message.id plus events without one
    naive: Dict[str, int]  # every event summed, no deduplication at all


def manual_dedupe(root: pathlib.Path) -> Manual:
    """Reproduce the number by hand: a ``dict`` keyed by ``message.id`` keeping the max per field.

    Files are the sessions (``*.jsonl`` at the top of ``root``) and the
    ``agent-*.jsonl`` transcripts under each session's own ``subagents/``.
    Nothing else: not ``journal.jsonl``, not a ``subagents/`` without its session.
    """
    mains = sorted(root.glob("*.jsonl"))
    files = mains + [p for m in mains for p in sorted((root / m.stem).glob("subagents/**/agent-*.jsonl"))]

    best: Dict[str, Dict[str, int]] = {}
    loose = dict.fromkeys(USAGE_KEYS, 0)  # events without message.id, each one unique
    naive = dict.fromkeys(USAGE_KEYS, 0)
    anonymous = 0
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            message = json.loads(line)["message"]
            usage = message["usage"]
            for key in USAGE_KEYS:
                naive[key] += usage[key]
            if message.get("id") is None:
                anonymous += 1
                for key in USAGE_KEYS:
                    loose[key] += usage[key]
            else:
                kept = best.setdefault(message["id"], dict.fromkeys(USAGE_KEYS, 0))
                for key in USAGE_KEYS:
                    kept[key] = max(kept[key], usage[key])

    combined = {key: sum(kept[key] for kept in best.values()) + loose[key] for key in USAGE_KEYS}
    return Manual(combined=combined, counted=len(best) + anonymous, naive=naive)


@dataclasses.dataclass
class Reference:
    """The context distribution of the manual rule: every figure is an int or a dict of ints."""

    requests: Dict[str, int]  # per band, main thread plus subagents
    tokens: Dict[str, int]
    main_requests: Dict[str, int]  # per band, main thread only
    main_tokens: Dict[str, int]
    model_tokens: Dict[str, int]  # per model, models with no tokens left out
    sub_requests: int
    sub_tokens: int
    total_requests: int
    total_tokens: int


LABELS = ("<50k", "50k-150k", "150k-200k", ">200k")


def _band_of(context: int) -> str:
    """Written out by hand from the spec: 50.000 and 150.000 open a band, 200.000 still closes one."""
    if context < 50_000:
        return "<50k"
    if context < 150_000:
        return "50k-150k"
    if context <= 200_000:
        return "150k-200k"
    return ">200k"


def reference_distribution(root: pathlib.Path) -> Reference:
    """Dedupe by ``message.id`` (max per field), then band, split and total the requests by hand."""
    mains = sorted(root.glob("*.jsonl"))
    files = [(p, True) for p in mains]
    files += [(p, False) for m in mains for p in sorted((root / m.stem).glob("subagents/**/agent-*.jsonl"))]

    best: Dict[str, Dict[str, int]] = {}
    is_main: Dict[str, bool] = {}
    model_of: Dict[str, str] = {}
    requests: List[Any] = []  # (usage, is_main, model) of every event without message.id
    for path, main in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            message = json.loads(line)["message"]
            model = message.get("model")
            model = "unknown" if not isinstance(model, str) or model.startswith("<") else model
            usage = {key: message["usage"][key] for key in USAGE_KEYS}
            if message.get("id") is None:
                requests.append((usage, main, model))
                continue
            kept = best.setdefault(message["id"], dict.fromkeys(USAGE_KEYS, 0))
            for key in USAGE_KEYS:
                kept[key] = max(kept[key], usage[key])
            is_main[message["id"]] = is_main.get(message["id"], False) or main
            model_of[message["id"]] = model
    requests += [(best[i], is_main[i], model_of[i]) for i in best]

    ref = Reference(
        requests=dict.fromkeys(LABELS, 0),
        tokens=dict.fromkeys(LABELS, 0),
        main_requests=dict.fromkeys(LABELS, 0),
        main_tokens=dict.fromkeys(LABELS, 0),
        model_tokens={},
        sub_requests=0,
        sub_tokens=0,
        total_requests=0,
        total_tokens=0,
    )
    for usage, main, model in requests:
        context = usage["input_tokens"] + usage["cache_creation_input_tokens"] + usage["cache_read_input_tokens"]
        band = _band_of(context)
        ref.total_requests += 1
        ref.total_tokens += context
        ref.requests[band] += 1
        ref.tokens[band] += context
        if main:
            ref.main_requests[band] += 1
            ref.main_tokens[band] += context
        else:
            ref.sub_requests += 1
            ref.sub_tokens += context
        if context:
            ref.model_tokens[model] = ref.model_tokens.get(model, 0) + context
    return ref


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


def _figures(row: Any) -> Dict[str, int]:
    """``turns`` and the four usage figures of a ``SessionTokens`` / ``SubagentTokens`` or of its JSON object."""
    get = row.get if isinstance(row, dict) else lambda name: getattr(row, name)
    return {name: get(name) for name in ("turns", *REPORT_FIELD.values())}


def _assert_report_matches(manual: Manual, main_row: Any, agents_row: Any) -> None:
    thread, agents = _figures(main_row), _figures(agents_row)

    # Success criterion #1: main thread + subagents, per usage field, against the manual sum
    # over every file. Exact equality is stricter than the spec's 1%.
    combined = {key: thread[REPORT_FIELD[key]] + agents[REPORT_FIELD[key]] for key in USAGE_KEYS}
    assert combined == manual.combined

    # No id is counted twice: one turn per distinct id (plus one per event without one).
    assert thread["turns"] + agents["turns"] == manual.counted


@pytest.mark.parametrize("seed", SEEDS)
def test_report_total_equals_the_independent_manual_dedupe(tmp_path: pathlib.Path, seed: int) -> None:
    build_transcripts(tmp_path, seed)
    manual = manual_dedupe(tmp_path)
    # The fixture discriminates: without deduplication every field is off by far more than 1%.
    for key in USAGE_KEYS:
        assert manual.naive[key] > manual.combined[key] * 1.01, key

    report = tm.build_token_report(tmp_path)

    _assert_report_matches(manual, report.totals, report.subagent_totals)


@pytest.mark.parametrize("seed", [0, 7, 13])
def test_cli_json_total_equals_the_independent_manual_dedupe(tmp_path: pathlib.Path, seed: int) -> None:
    """The same figures through ``aiadev metrics --tokens --format json``."""
    build_transcripts(tmp_path, seed)
    manual = manual_dedupe(tmp_path)

    result = CliRunner().invoke(
        main, ["metrics", "--tokens", "--transcripts-dir", str(tmp_path), "--format", "json"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    _assert_report_matches(manual, data["totals"], data["subagent_totals"])


def _assert_distribution_matches(
    ref: Reference,
    main_row: Any,
    agents_row: Any,
    all_bands: Dict[str, Dict[str, int]],
    main_bands: Dict[str, Dict[str, int]],
    model_shares: List[Dict[str, Any]],
    subagent_share: Dict[str, float],
) -> None:
    """``all_bands`` / ``main_bands`` are ``{"requests": {...}, "context_tokens": {...}}``."""
    thread, agents = _figures(main_row), _figures(agents_row)
    input_keys = ("input_tokens", "cache_creation_tokens", "cache_read_tokens")
    total_input = sum(thread[k] + agents[k] for k in input_keys)
    total_turns = thread["turns"] + agents["turns"]

    # (a) context per band, exactly, and the four bands add up to the input total (the spec's 1% is slack).
    assert all_bands["context_tokens"] == ref.tokens
    assert sum(all_bands["context_tokens"].values()) == total_input == ref.total_tokens
    assert abs(sum(all_bands["context_tokens"].values()) - ref.total_tokens) <= ref.total_tokens * 0.01

    # (b) requests per band, and they add up to the turns of the main thread plus the subagents.
    assert all_bands["requests"] == ref.requests
    assert sum(all_bands["requests"].values()) == total_turns == ref.total_requests

    # (c) the main thread alone.
    assert main_bands["requests"] == ref.main_requests
    assert main_bands["context_tokens"] == ref.main_tokens
    assert sum(main_bands["context_tokens"].values()) == sum(thread[k] for k in input_keys)
    assert sum(main_bands["requests"].values()) == thread["turns"]

    # (d) shares by model: the same tokens per model, largest first, adding up to the input total.
    assert {row["model"]: row["tokens"] for row in model_shares} == ref.model_tokens
    assert [row["tokens"] for row in model_shares] == sorted((row["tokens"] for row in model_shares), reverse=True)
    assert sum(row["tokens"] for row in model_shares) == total_input
    for row in model_shares:
        assert row["share"] == pytest.approx(row["tokens"] / ref.total_tokens)

    # (e) the subagent share.
    assert subagent_share["requests"] == pytest.approx(ref.sub_requests / ref.total_requests)
    assert subagent_share["tokens"] == pytest.approx(ref.sub_tokens / ref.total_tokens)


@pytest.mark.parametrize("seed", SEEDS)
def test_context_distribution_equals_the_independent_reference(tmp_path: pathlib.Path, seed: int) -> None:
    build_transcripts(tmp_path, seed)
    ref = reference_distribution(tmp_path)
    # The fixture discriminates: every band, main thread and subagents, has requests; the edges are in.
    assert all(ref.requests[label] > 0 and ref.main_requests[label] > 0 for label in LABELS)
    assert ref.sub_requests > 0 and len(ref.model_tokens) > 1
    assert {_band_of(c) for c in CONTEXT_TARGETS} == set(LABELS)

    report = tm.build_token_report(tmp_path)

    _assert_distribution_matches(
        ref,
        report.totals,
        report.subagent_totals,
        {"requests": report.band_requests, "context_tokens": report.band_context_tokens},
        {"requests": report.main_band_requests, "context_tokens": report.main_band_context_tokens},
        report.model_shares,
        report.subagent_share,
    )


@pytest.mark.parametrize("seed", [0, 7, 13])
def test_cli_json_context_distribution_equals_the_independent_reference(tmp_path: pathlib.Path, seed: int) -> None:
    build_transcripts(tmp_path, seed)
    ref = reference_distribution(tmp_path)

    result = CliRunner().invoke(
        main, ["metrics", "--tokens", "--transcripts-dir", str(tmp_path), "--format", "json"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    distribution = data["context_distribution"]
    _assert_distribution_matches(
        ref,
        data["totals"],
        data["subagent_totals"],
        distribution["all"],
        distribution["main_thread"],
        data["model_shares"],
        data["subagent_share"],
    )
