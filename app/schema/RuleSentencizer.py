from spacy.matcher.matcher import Matcher
from spacy.tokens.doc import Doc


class RuleSentencizer(object):
    """
    Simple component that correct some over-segmentation errors of the sentencizer using exception rules.
    Each rule must have a IS_SENT_START token pattern and this sentence boundary is removed from the final output.
    For example the text
    "Une indemnité de 100. 000 Frs"
    is by default segmented after the 100. but it shouldn't
    With this simple rule:
    [{"IS_DIGIT": True}, {"IS_SENT_START": True, "IS_PUNCT" : True}, {"IS_DIGIT": True}]
    The sentence corrector does the trick.

    The component is initialized this way:
    overrides = defaultdict(dict)
    overrides["rule_sentencizer"]["split"] = [
        # Split on double line breaks
        [{"IS_SPACE": True, "TEXT": { "REGEX" : "[\n]{2,}" }}, {}],
        # Split on hard punctuation
        [{"ISPUNCT": True, "TEXT" : { "IN" : [".", "!", "?"]}}, {}]
    ]
    overrides["rule_sentencizer"]["join"] = [
        # Une indemnité de 100. 000 Frs
        [{"IS_DIGIT": True}, {"IS_SENT_START": True, "IS_PUNCT" : True}, {"IS_DIGIT": True}]
    ]
    nlp = spacy.load(model)
    custom = RuleSentencizer(nlp, **overrides)
    nlp.add_pipe(custom)
    """
    name = "rule_sentencizer"
    split_matcher = None
    join_matcher = None
    def __init__(self, nlp, **cfg):
        if self.name in cfg:
            split_patterns = cfg[self.name].get('split', None)
            if split_patterns:
                self.split_matcher = Matcher(nlp.vocab)
                self.split_matcher.add("split", None, *split_patterns)
            join_patterns = cfg[self.name].get('join', None)
            if join_patterns:
                self.join_matcher = Matcher(nlp.vocab)
                self.join_matcher.add("join", None, *join_patterns)

    def __call__(self, doc : Doc):
        save_parsed = doc.is_parsed
        doc.is_parsed = False
        if self.split_matcher:
            matches = self.split_matcher(doc)
            for match_id, start, end in matches:
                token = doc[end-1]
                token.is_sent_start = True
                if end-2>=0 and doc[end-2].is_sent_start is True:
                    doc[end-2].is_sent_start = False
        if self.join_matcher:
            matches = self.join_matcher(doc)
            for match_id, start, end in matches:
                # If there is a sent start in the match, just remove it
                for token in doc[start:end]:
                    if token.is_sent_start:
                        token.is_sent_start = False
        doc.is_parsed = save_parsed
        return doc
