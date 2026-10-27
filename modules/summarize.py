import nltk
from functools import lru_cache
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from typing import List
import random

def _ensure_nltk_tokenizer():
    # Ensure both classic punkt and new punkt_tab are available
    for resource in ['punkt', 'punkt_tab']:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            nltk.download(resource)

@lru_cache(maxsize=1)
def _ensure_nltk_paraphrase_resources():
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        try:
            nltk.data.find('corpora/wordnet.zip')
        except LookupError:
            nltk.download('wordnet')
    # POS tagger resources (newer NLTK uses different names on some installs)
    taggers = ['averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng']
    available = False
    for t in taggers:
        try:
            nltk.data.find(f'taggers/{t}')
            available = True
            break
        except LookupError:
            pass
    if not available:
        for t in taggers:
            try:
                nltk.download(t)
            except Exception:
                pass


def quick_abstract(summary_text: str, max_sentences: int = 2) -> str:
    if not summary_text or not summary_text.strip():
        return ""
    _ensure_nltk_tokenizer()
    return " ".join(nltk.sent_tokenize(summary_text)[:max_sentences])


def lexrank_summarize(text: str, num_sentences: int = 6) -> str:
    if not text or not text.strip():
        return ""
    
    _ensure_nltk_tokenizer()  # Ensures punkt is available

    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    # Hybrid summarization: LexRank + LSA with deduplication and length cap
    lexrank = LexRankSummarizer()
    lsa = LsaSummarizer()

    lex_sents = [str(s) for s in lexrank(parser.document, max(1, num_sentences // 2 + num_sentences % 2))]
    lsa_sents = [str(s) for s in lsa(parser.document, max(1, num_sentences // 2))]

    combined = []
    seen = set()
    for s in lex_sents + lsa_sents:
        sn = s.strip()
        if not sn:
            continue
        key = sn.lower()
        if key in seen:
            continue
        seen.add(key)
        combined.append(sn)

    if not combined:
        sentences = nltk.sent_tokenize(text)
        combined = sentences[:num_sentences]

    total_sentences = max(1, len(nltk.sent_tokenize(text)))
    cap = max(1, min(num_sentences, int(0.3 * total_sentences)))
    return " ".join(combined[:cap])


def generate_abstract(summary_text: str, max_replacements_per_sentence: int = 2) -> str:
    """Paraphrase the summary to produce an abstract with similar meaning but different wording.

    Lightweight heuristic paraphraser using NLTK WordNet synonyms and POS tagging.
    """
    if not summary_text or not summary_text.strip():
        return ""

    _ensure_nltk_tokenizer()
    _ensure_nltk_paraphrase_resources()

    from nltk.corpus import wordnet as wn

    def is_content_pos(tag: str) -> bool:
        return tag.startswith(('NN', 'VB', 'JJ', 'RB'))

    def pick_synonym(word: str, pos_tag: str) -> str:
        pos_map = {
            'NN': wn.NOUN,
            'NNS': wn.NOUN,
            'NNP': wn.NOUN,
            'NNPS': wn.NOUN,
            'VB': wn.VERB,
            'VBD': wn.VERB,
            'VBG': wn.VERB,
            'VBN': wn.VERB,
            'VBP': wn.VERB,
            'VBZ': wn.VERB,
            'JJ': wn.ADJ,
            'JJR': wn.ADJ,
            'JJS': wn.ADJ,
            'RB': wn.ADV,
            'RBR': wn.ADV,
            'RBS': wn.ADV,
        }
        wn_pos = None
        for k, v in pos_map.items():
            if pos_tag.startswith(k):
                wn_pos = v
                break
        if wn_pos is None:
            return word
        synsets = wn.synsets(word, pos=wn_pos)
        candidates: List[str] = []
        for s in synsets[:3]:
            for lemma in s.lemmas()[:3]:
                name = lemma.name().replace('_', ' ')
                if name.lower() != word.lower() and name.isascii():
                    candidates.append(name)
        if not candidates:
            return word
        choice = random.choice(candidates)
        # Preserve capitalization
        if word.istitle():
            choice = choice.title()
        return choice

    sentences = nltk.sent_tokenize(summary_text)
    abstract_sentences: List[str] = []
    for s in sentences:
        tokens = nltk.word_tokenize(s)
        tags = nltk.pos_tag(tokens)
        # Choose indices for replacement
        candidate_indices = [i for i, (w, t) in enumerate(tags) if is_content_pos(t) and w.isalpha() and not w.istitle()]
        random.shuffle(candidate_indices)
        to_replace = set(candidate_indices[:max_replacements_per_sentence])
        new_tokens: List[str] = []
        for i, (w, t) in enumerate(tags):
            if i in to_replace:
                new_tokens.append(pick_synonym(w, t))
            else:
                new_tokens.append(w)
        # Reconstruct with simple rules
        out = []
        for i, tok in enumerate(new_tokens):
            if i > 0 and tok not in ",.;:!?%":
                if tok not in "'s 're 've n't 'll 'd":
                    out.append(' ')
            out.append(tok)
        abstract_sentences.append(''.join(out))

    return ' '.join(abstract_sentences)