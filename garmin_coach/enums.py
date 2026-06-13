"""Enums canoniques du projet."""

from enum import StrEnum


class GoalPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ConstraintType(StrEnum):
    AVAILABILITY = "availability"
    HEALTH = "health"
    MENTAL_STATE = "mental_state"
    PREFERENCE = "preference"
    SCHEDULE = "schedule"
    EQUIPMENT = "equipment"


class ConstraintStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ConstraintScope(StrEnum):
    TRAINING = "training"
    LIFE = "life"
    DAY = "day"
    SESSION = "session"


class ConstraintSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BlockType(StrEnum):
    BUILD = "build"
    RECOVER = "recover"
    PEAK = "peak"
    TAPER = "taper"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SENT = "sent"  # Deprecated: kept for backward-compat reading only
    ARCHIVED = "archived"


class SessionStatus(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    EXPORTED = "exported"
    DONE = "done"
    SKIPPED = "skipped"
    CANCELED = "canceled"


class ReviewOutcome(StrEnum):
    KEPT = "kept"
    ADAPTED = "adapted"
    RESET = "reset"


class MatchType(StrEnum):
    MANUAL = "manual"
    INFERRED = "inferred"
    IMPORTED = "imported"


class ActivitySource(StrEnum):
    GARMIN = "garmin"
    MANUAL = "manual"


class DebriefStatus(StrEnum):
    PENDING = "pending"
    PROMPTED = "prompted"
    COMPLETED = "completed"
    DISMISSED = "dismissed"
