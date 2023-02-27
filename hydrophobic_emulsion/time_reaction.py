from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline, pipeline
from yargy import rule, and_, Parser, or_
from yargy.predicates import eq

from yargy_utils import TOKENIZER, ID_TOKENIZER, DECIMAL, PERCENT, INT
from yargy_utils.duration import DURATION


def extract_time_reaction(text):
    tokens = list(TOKENIZER(text))
    REACTION = morph_pipeline(['реагирование'])
    parser = Parser(or_(REACTION,DURATION), tokenizer=ID_TOKENIZER)
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
    Time_reaction = fact('Time_reaction',
                         ['time_value']
                         )
    TIME_REACTION = rule(REACTION, DURATION.interpretation(Time_reaction.time_value)).interpretation(Time_reaction)
    parser = Parser(TIME_REACTION, tokenizer=ID_TOKENIZER)
    matches = list(parser.findall(tokens))
    if matches:
        for match in matches:
            return match.fact
