#!/usr/bin/env python3
from typing import List, Any
from natasha import AddressExtractor, DatesExtractor
from yargy import rule, or_, and_
from yargy.interpretation import fact, attribute
from yargy.predicates import normalized, caseless, eq, gte, lte, dictionary
from yargy.pipelines import morph_pipeline
from natasha.grammars.address import DOT, STREET_LEVEL, SEP, DOM, ADDRESS, PRE_STREET_LEVEL, POST_STREET_LEVEL
from natasha.grammars.date import DATE

Metro = fact('Metro', ['name', 'type'])

Address = fact('Address', [attribute('parts').repeatable()])

METRO_STATIONS = rule(
    morph_pipeline(
        {
            'Автозаводская', 'Щукинская',
            'Академическая', 'Электрозаводская',
            'Александровский сад', 'Юго-Западная',
            'Алексеевская', 'Южная',
            'Алма-Атинская', 'Ясенево'
        }
    )
)

METRO_WORDS = or_(
    rule(normalized('метро')),
    rule(caseless('м'), DOT.optional()),
).interpretation(Metro.type.const('метро'))

METRO = or_(
    rule(METRO_WORDS.optional(), METRO_STATIONS),
    rule(METRO_STATIONS, METRO_WORDS.optional())
).interpretation(Metro)


STREET_LEVEL.rules.append(METRO)

ADDRESS.rule = rule(
    rule(PRE_STREET_LEVEL.interpretation(Address.parts), SEP.optional()).optional().repeatable(),
    STREET_LEVEL.interpretation(Address.parts),
    rule(SEP.optional(), DOM.interpretation(Address.parts)).optional(),
    rule(SEP.optional(), POST_STREET_LEVEL.interpretation(Address.parts)).optional().repeatable(),
).interpretation(Address)


Date = fact('Date', ['year', 'month', 'day', 'time', attribute('current_era', True)])

HOURS = and_(gte(0), lte(23)).interpretation(Date.time.custom(int))
HOURS_WORD = or_(rule('ч', eq('.').optional()), rule(normalized('час')))
WORD_AFTER = rule(normalized('через'))
WORD_IN = rule(normalized('в'))
MINUTES = and_(gte(0), lte(59)).interpretation(Date.time.custom(int))
SECONDS = and_(gte(0), lte(59)).interpretation(Date.time.custom(int))

MINUTES_WORD = or_(
    rule('мин', eq('.').optional()),
    rule('м', eq('.').optional()),
    rule(normalized('минута'))
)

TIME_WORDS = rule(
    dictionary({
        'завтра', 'сегодня', 'вчера', 'день', 'вечер', 'утро', 'ночь', 'сейчас',
        'через', 'один', 'два', 'три', 'четыре', 'пять',
    })
)


DATE.rule.rules.extend(
    [
        rule(WORD_AFTER.optional(), HOURS.optional(), HOURS_WORD),
        rule(HOURS_WORD, WORD_AFTER, TIME_WORDS),
        rule(WORD_AFTER, TIME_WORDS, HOURS_WORD),
        rule(WORD_AFTER.optional(), MINUTES.optional(), MINUTES_WORD),
        rule(MINUTES_WORD, WORD_AFTER.optional(), MINUTES.optional()),
        rule(normalized('следующих'), normalized('выходных')),
        rule(TIME_WORDS, WORD_IN, HOURS, ':', MINUTES),
        rule(HOURS, ':', MINUTES, normalized(':').optional(), SECONDS.optional()),
        TIME_WORDS,
    ]
)


def extractor_address(text: str) -> List[Any]:
    return [match for match in AddressExtractor()(text)]


def extractor_address_str(text: str) -> List[str]:
    return [text.__getitem__(slice(*match.span)) for match in AddressExtractor()(text)]


def extractor_date(text: str) -> List[Any]:
    return [match for match in DatesExtractor()(text)]


def extractor_date_str(text: str) -> List[str]:
    return [text.__getitem__(slice(*match.span)) for match in DatesExtractor()(text)]


# Примеры
# extractor_address('пошли к метро Щукинская')
# extractor_date('пойдем завтра в кино к 15:25')
