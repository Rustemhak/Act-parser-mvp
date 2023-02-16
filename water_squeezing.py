from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline, pipeline
from yargy import rule, and_, Parser, or_
from yargy_utils import TOKENIZER, ID_TOKENIZER, DECIMAL, PERCENT, INT


def extract_water_volumes(text):
    tokens = list(TOKENIZER(text))
    SQUEEZING = morph_pipeline(['продавить', 'продавка'])
    FRINGE = pipeline(['Оторочка'])
    STAGE = morph_pipeline(['композицию'])
    UNIT_VOLUME = rule(or_(DECIMAL, rule(INT)), morph_pipeline(['м3']))
    parser = Parser(or_(UNIT_VOLUME, SQUEEZING, FRINGE, STAGE), tokenizer=ID_TOKENIZER)
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
    Squeezing_volume = fact(
        'Squeezing_volume',
        ['value']
    )
    SQUEEZING_VOLUMES = rule(or_(SQUEEZING, FRINGE), UNIT_VOLUME.interpretation(Squeezing_volume.value)).interpretation(
        Squeezing_volume)
    parser = Parser(SQUEEZING_VOLUMES, tokenizer=ID_TOKENIZER)
    matches = list(parser.findall(tokens))
    facts = []
    if matches:
        for match in matches:
            fact_feature = match.fact
            facts.append(fact_feature)
    return facts
