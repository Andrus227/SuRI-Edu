from __future__ import annotations

import re
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass

DEFAULT_ROUTINE_NAME = "RotinaGravada"

_METHOD_DECLARATION = re.compile(
    r"^metodo\s+([a-zA-Z0-9_]+)\s*:",
    re.IGNORECASE,
)
_METHOD_NAME = re.compile(r"^[a-zA-Z0-9_]+$")
_MOVE_TO = re.compile(
    r"MoveTo\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)",
    re.IGNORECASE,
)
_MOVE_POSE = re.compile(
    r"MovePose\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
    re.IGNORECASE,
)
_WAIT = re.compile(r"Wait\s*\(\s*(\d+)\s*\)", re.IGNORECASE)


@dataclass(slots=True)
class RobixProgram:
    methods: dict[str, list[str]]
    setup: list[str]
    loop: list[str]


@dataclass(frozen=True, slots=True)
class MoveToCommand:
    motor: int
    angle: int


@dataclass(frozen=True, slots=True)
class MovePoseCommand:
    angles: tuple[int, int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class WaitCommand:
    milliseconds: int


RobixCommand = MoveToCommand | MovePoseCommand | WaitCommand


def parse_program(
    source: str,
    on_method: Callable[[str], None] | None = None,
) -> RobixProgram:
    """Parse source blocks while preserving the permissive legacy grammar."""
    methods: dict[str, list[str]] = {}
    setup: list[str] = []
    loop: list[str] = []
    target = "root"
    base_indentation = -1

    for raw_line in source.split("\n"):
        uncommented_line = raw_line.split("//")[0].rstrip().rstrip(";")
        if not uncommented_line.strip():
            continue

        indentation = len(uncommented_line) - len(uncommented_line.lstrip())
        command = uncommented_line.strip()

        method_match = _METHOD_DECLARATION.search(command)
        if method_match:
            name = method_match.group(1)
            methods[name] = []
            target = f"method_{name}"
            base_indentation = indentation
            if on_method is not None:
                on_method(name)
            continue

        if command.lower() == "setup:":
            target = "setup"
            base_indentation = indentation
            continue

        if command.lower() == "loop:":
            target = "loop"
            base_indentation = indentation
            continue

        if base_indentation != -1 and indentation > base_indentation:
            if target.startswith("method_"):
                methods[target.removeprefix("method_")].append(command)
            elif target == "setup":
                setup.append(command)
            elif target == "loop":
                loop.append(command)
        else:
            target = "root"
            base_indentation = -1
            setup.append(command)

    return RobixProgram(methods=methods, setup=setup, loop=loop)


def generate_routine(name: str, poses: Sequence[str]) -> str:
    """Generate source using the exact format emitted by the teach pendant."""
    method_name = name.strip() or DEFAULT_ROUTINE_NAME
    if _METHOD_NAME.fullmatch(method_name) is None:
        raise ValueError("Nome da rotina deve conter apenas letras, números e sublinhado (_).")
    code = f"metodo {method_name}:\n"

    for index, pose in enumerate(poses, start=1):
        code += f"    // Ponto {index}\n"
        code += f"    {pose}"
        code += "    Wait(1000)\n"

    code += "\nsetup:\n"
    code += "    // Posição inicial\n"
    code += f"    {poses[0]}"
    code += "\nloop:\n"
    code += "    // Execução contínua\n"
    code += f"    {method_name}\n"
    return code


def extract_method_sources(source: str) -> dict[str, str]:
    """Extract and normalize declared method blocks for later reuse."""
    lines = source.splitlines()
    methods: dict[str, str] = {}
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        command = raw_line.split("//", maxsplit=1)[0].strip()
        match = _METHOD_DECLARATION.search(command)
        if match is None:
            index += 1
            continue

        name = match.group(1)
        base_indentation = len(raw_line) - len(raw_line.lstrip())
        body: list[str] = []
        index += 1
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip():
                body.append(candidate)
                index += 1
                continue
            indentation = len(candidate) - len(candidate.lstrip())
            if indentation <= base_indentation:
                break
            body.append(candidate)
            index += 1

        body_text = textwrap.dedent("\n".join(body)).rstrip()
        method_source = f"metodo {name}:\n"
        if body_text:
            method_source += textwrap.indent(body_text, "    ") + "\n"
        methods[name] = method_source

    return methods


def parse_command(source: str) -> RobixCommand | None:
    """Recognize one built-in command using the legacy substring semantics."""
    move_to_match = _MOVE_TO.search(source)
    if move_to_match:
        return MoveToCommand(
            motor=int(move_to_match.group(1)),
            angle=int(move_to_match.group(2)),
        )

    move_pose_match = _MOVE_POSE.search(source)
    if move_pose_match:
        angles = tuple(int(move_pose_match.group(index)) for index in range(1, 7))
        return MovePoseCommand(angles=angles)

    wait_match = _WAIT.search(source)
    if wait_match:
        return WaitCommand(milliseconds=int(wait_match.group(1)))

    return None
