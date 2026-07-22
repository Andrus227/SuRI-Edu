from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

MOTOR_COUNT = 6
MIN_ANGLE = 0
MAX_ANGLE = 180

logger = logging.getLogger(__name__)

MotorSender = Callable[[int, int], bool]
StateObserver = Callable[["MotorStateSnapshot"], None]
CancellationCheck = Callable[[], bool]


@dataclass(frozen=True, slots=True)
class MotorStateSnapshot:
    desired: tuple[int | None, ...]
    commanded: tuple[int | None, ...]
    confirmed: tuple[int | None, ...]
    updated_at: float
    source: str | None = None
    changed_motor: int | None = None
    connected: bool = False
    routine_state: str = "idle"
    stop_state: str = "idle"
    error: str | None = None


@dataclass(frozen=True, slots=True)
class MovementResult:
    attempted: tuple[int, ...]
    sent: tuple[int, ...]
    failed: tuple[int, ...]
    cancelled: bool = False


class MotorController:
    """Owns requested and transmitted motor state independently of the GUI."""

    def __init__(
        self,
        sender: MotorSender,
        *,
        initial_desired: Sequence[int] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._sender = sender
        self._clock = clock
        desired = (
            tuple(self.normalize_angle(angle) for angle in initial_desired)
            if initial_desired is not None
            else (None,) * MOTOR_COUNT
        )
        if len(desired) != MOTOR_COUNT:
            raise ValueError(f"A pose deve conter {MOTOR_COUNT} angulos")
        self._snapshot = MotorStateSnapshot(
            desired=desired,
            commanded=(None,) * MOTOR_COUNT,
            confirmed=(None,) * MOTOR_COUNT,
            updated_at=self._clock(),
        )
        self._observers: list[StateObserver] = []

    @staticmethod
    def normalize_angle(angle: int | float) -> int:
        if isinstance(angle, bool) or not isinstance(angle, (int, float)):
            raise TypeError("O angulo deve ser numerico")
        return max(MIN_ANGLE, min(MAX_ANGLE, int(angle)))

    @staticmethod
    def validate_motor(motor: int) -> None:
        if isinstance(motor, bool) or not isinstance(motor, int) or not 1 <= motor <= MOTOR_COUNT:
            raise ValueError(f"Motor deve estar entre 1 e {MOTOR_COUNT}")

    @property
    def snapshot(self) -> MotorStateSnapshot:
        return self._snapshot

    def subscribe(self, observer: StateObserver) -> Callable[[], None]:
        self._observers.append(observer)
        observer(self._snapshot)

        def unsubscribe() -> None:
            if observer in self._observers:
                self._observers.remove(observer)

        return unsubscribe

    def set_connection(self, connected: bool, *, invalidate: bool = False) -> None:
        commanded = self._snapshot.commanded
        confirmed = self._snapshot.confirmed
        if invalidate:
            commanded = (None,) * MOTOR_COUNT
            confirmed = (None,) * MOTOR_COUNT
        self._publish(connected=connected, commanded=commanded, confirmed=confirmed)

    def set_routine_state(self, state: str) -> None:
        self._publish(routine_state=state)

    def set_stop_state(self, state: str, error: str | None = None) -> None:
        self._publish(stop_state=state, error=error)

    def invalidate_commanded_state(self) -> None:
        self._publish(
            commanded=(None,) * MOTOR_COUNT,
            confirmed=(None,) * MOTOR_COUNT,
        )

    def set_desired_motor(self, motor: int, angle: int | float, *, source: str) -> int:
        self.validate_motor(motor)
        normalized = self.normalize_angle(angle)
        desired = list(self._snapshot.desired)
        desired[motor - 1] = normalized
        self._publish(
            desired=tuple(desired),
            source=source,
            changed_motor=motor,
            error=None,
        )
        return normalized

    def command_motor(
        self,
        motor: int,
        angle: int | float,
        *,
        source: str,
        should_continue: CancellationCheck | None = None,
    ) -> MovementResult:
        self.validate_motor(motor)
        normalized = self.normalize_angle(angle)
        desired = list(self._snapshot.desired)
        desired[motor - 1] = normalized
        self._publish(
            desired=tuple(desired),
            source=source,
            changed_motor=motor,
            error=None,
        )

        if should_continue is not None and not should_continue():
            return MovementResult((), (), (), cancelled=True)

        if not self._sender(motor, normalized):
            self._publish(
                source=source,
                changed_motor=motor,
                error=f"Falha ao transmitir motor {motor}",
            )
            return MovementResult((motor,), (), (motor,))

        commanded = list(self._snapshot.commanded)
        commanded[motor - 1] = normalized
        self._publish(
            commanded=tuple(commanded),
            source=source,
            changed_motor=motor,
            error=None,
        )
        return MovementResult((motor,), (motor,), ())

    def command_pose(
        self,
        angles: Sequence[int | float],
        *,
        source: str,
        should_continue: CancellationCheck | None = None,
    ) -> MovementResult:
        desired, changed = self.prepare_pose(angles, source=source)
        sent: list[int] = []
        failed: list[int] = []

        for motor in changed:
            if should_continue is not None and not should_continue():
                return MovementResult(changed, tuple(sent), tuple(failed), cancelled=True)
            result = self.command_motor(
                motor,
                desired[motor - 1],
                source=source,
                should_continue=should_continue,
            )
            sent.extend(result.sent)
            failed.extend(result.failed)
            if result.cancelled:
                return MovementResult(changed, tuple(sent), tuple(failed), cancelled=True)

        return MovementResult(changed, tuple(sent), tuple(failed))

    def prepare_pose(
        self,
        angles: Sequence[int | float],
        *,
        source: str,
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Record a desired pose and return its normalized targets and changed motors."""
        if len(angles) != MOTOR_COUNT:
            raise ValueError(f"A pose deve conter {MOTOR_COUNT} angulos")

        desired = tuple(self.normalize_angle(angle) for angle in angles)
        changed = tuple(
            motor
            for motor, (target, current) in enumerate(
                zip(desired, self._snapshot.commanded, strict=True), start=1
            )
            if current is None or target != current
        )
        self._publish(desired=desired, source=source, changed_motor=None, error=None)
        return desired, changed

    def confirm_motor(self, motor: int, angle: int | float, *, source: str = "controller") -> None:
        self.validate_motor(motor)
        normalized = self.normalize_angle(angle)
        confirmed = list(self._snapshot.confirmed)
        confirmed[motor - 1] = normalized
        self._publish(
            confirmed=tuple(confirmed),
            source=source,
            changed_motor=motor,
            error=None,
        )

    def _publish(self, **changes: object) -> None:
        self._snapshot = replace(self._snapshot, updated_at=self._clock(), **changes)
        for observer in tuple(self._observers):
            try:
                observer(self._snapshot)
            except Exception:
                logger.exception("Falha em observador de estado dos motores")
