# правило для длительности
from yargy import and_, or_, rule
from yargy.predicates import normalized
from yargy.predicates import (
    lte,
    gte,
    dictionary
)
from yargy.interpretation import fact, attribute
from yargy.predicates import eq, caseless, normalized, type, length_eq
from yargy_utils import INT, DOT

Duration = fact(
    'Duration',
    ['hours', 'minutes', 'seconds']
)

HOURS = INT.interpretation(
    Duration.hours.custom(int)
)

HOUR_WORDS = normalized('час')

MINUTES = and_(
    INT,
    gte(0),
    lte(59)
).interpretation(
    Duration.minutes.custom(int)
)

MINUTE_WORDS = or_(
    rule(normalized('минута')),
    rule(caseless('мин'), DOT.optional())
)

SECONDS = and_(
    INT,
    gte(0),
    lte(59)
).interpretation(
    Duration.seconds.custom(int)
)

SECOND_WORDS = or_(
    rule(normalized('секунда')),
    rule(caseless('сек'), DOT.optional()),
)

DURATION = rule(
    rule(
        HOURS,
        HOUR_WORDS
    ),
    rule(
        MINUTES,
        MINUTE_WORDS
    ).optional(),
    rule(
        SECONDS,
        SECOND_WORDS
    ).optional()
).interpretation(
    Duration
)
