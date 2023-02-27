from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline, pipeline
from yargy import rule, and_, Parser, or_
from yargy.predicates import eq

from yargy_utils import TOKENIZER, ID_TOKENIZER, DECIMAL, PERCENT, INT


def extract_hes(text):
    tokens = list(TOKENIZER(text))
    HES_WORD = morph_pipeline(['ГЭР', 'гидрофобная эмульсия'])
    UNIT_VOLUME = rule(or_(DECIMAL, rule(INT)), morph_pipeline(['м3']))
    UNIT_PERCENT = rule(or_(DECIMAL, rule(INT)), rule(eq('-'), or_(DECIMAL, rule(INT))).optional().repeatable(),
                        PERCENT)
    parser = Parser(or_(UNIT_VOLUME, UNIT_PERCENT, HES_WORD), tokenizer=ID_TOKENIZER)
    matches = parser.findall(tokens)
    spans = [_.span for _ in matches]

    # print(spans)

    def is_inside_span(token, span):
        token_span = token.span
        return span.start <= token_span.start and token_span.stop <= span.stop

    def select_span_tokens(tokens, spans):
        for token in tokens:
            if any(is_inside_span(token, _) for _ in spans):
                yield token

    tokens = list(select_span_tokens(tokens, spans))
    Hes = fact(
        'Hes',
        ['volume_value', 'percent_value']
    )
    HES = rule(
        or_(rule(UNIT_VOLUME.interpretation(Hes.volume_value), UNIT_PERCENT.interpretation(Hes.percent_value),
                 HES_WORD), rule(HES_WORD, UNIT_VOLUME.interpretation(Hes.volume_value),
                                 UNIT_PERCENT.interpretation(Hes.percent_value)))).interpretation(Hes)
    parser = Parser(HES, tokenizer=ID_TOKENIZER)
    matches = list(parser.findall(tokens))
    if matches:
        for match in matches:
            return match.fact
