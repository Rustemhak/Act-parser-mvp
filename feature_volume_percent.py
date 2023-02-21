from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline, pipeline
from yargy import rule, and_, Parser, or_
from yargy_utils import TOKENIZER, ID_TOKENIZER, DECIMAL, PERCENT, INT


def extract_volumes_feature_percents(text):
    tokens = list(TOKENIZER(text))

    SHORT_FEATURE = morph_pipeline([
        'ПАА',
        'ХКК',
        'СА',
        'ПАВ',
        'СКА',
    ])
    STAGE = morph_pipeline(['композиция'])
    FRINGE = pipeline(['оторочка'])
    VOLUME = morph_pipeline(['объём'])
    UNIT_VOLUME = rule(or_(DECIMAL, rule(INT)), morph_pipeline(['м3']))
    UNIT_PERCENT = rule(DECIMAL, PERCENT)
    parser = Parser(or_(STAGE, VOLUME, SHORT_FEATURE, UNIT_VOLUME, UNIT_PERCENT, rule(INT, FRINGE)),
                    tokenizer=ID_TOKENIZER)
    matches = parser.findall(tokens)
    spans = [_.span for _ in matches]
    print(spans)

    def is_inside_span(token, span):
        token_span = token.span
        return span.start <= token_span.start and token_span.stop <= span.stop

    def select_span_tokens(tokens, spans):
        for token in tokens:
            if any(is_inside_span(token, _) for _ in spans):
                yield token

    tokens = list(select_span_tokens(tokens, spans))
    Feature = fact(
        'Feature',
        ['field_name', 'value']
    )
    FEATURES = rule(
        or_(rule(or_(STAGE, rule(INT, FRINGE)), VOLUME.optional().interpretation(Feature.field_name.normalized()),
                 UNIT_VOLUME.interpretation(Feature.value)),
            rule(SHORT_FEATURE.interpretation(Feature.field_name),
                 UNIT_PERCENT.interpretation(Feature.value)))).interpretation(Feature)
    parser = Parser(FEATURES, tokenizer=ID_TOKENIZER)
    matches = list(parser.findall(tokens))
    facts = []
    if matches:
        for match in matches:
            fact_feature = match.fact
            if fact_feature.field_name is None:
                fact_feature.field_name = 'объём'
            facts.append(fact_feature)
    return facts


def count_sum_volume(volumes):
    a = list(map(lambda v: v.replace('м3', ''), volumes))
    sum_volumes = sum(list(map(float, list(map(lambda v: v.replace('м3', '').replace(',', '.'), volumes)))))
    return f'{sum_volumes}м3'.replace('.', ',')


def select_text_stages(text):
    lines = text.split('\n')
    i_stages = []
    for i, line in enumerate(lines):
        facts_stage = extract_volumes_feature_percents(line)
        if (len(facts_stage)) > 0:
            i_stages.append(i)
    return i_stages
