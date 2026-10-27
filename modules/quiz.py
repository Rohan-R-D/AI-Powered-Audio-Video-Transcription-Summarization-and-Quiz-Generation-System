print("quiz.py loaded")
import random
from typing import Dict, List

import nltk
from rake_nltk import Rake


_NLTK_READY = False


def _ensure_nltk():
    global _NLTK_READY
    if _NLTK_READY:
        return
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    _NLTK_READY = True


def _extract_keywords(text: str, max_phrases: int = 20) -> List[str]:
    _ensure_nltk()
    rake = Rake()
    rake.extract_keywords_from_text(text)
    # RAKE returns (score, phrase)
    raw = [phrase for score, phrase in rake.get_ranked_phrases_with_scores()]
    phrases: List[str] = []
    for p in raw:
        s = str(p).strip()
        if len(s) < 3:
            continue
        if s.isnumeric():
            continue
        if all(ch.isdigit() or ch in ",.-/" for ch in s):
            continue
        phrases.append(s)
    return phrases[:max_phrases]


def _make_cloze_questions(text: str, keywords: List[str], num: int) -> List[Dict]:
    questions: List[Dict] = []
    if not text:
        return questions
    sentences = nltk.sent_tokenize(text)
    for kw in keywords:
        for s in sentences:
            if kw.lower() in s.lower() and len(s.split()) > 6:
                blanked = s.replace(kw, "_____", 1)
                questions.append({"question": blanked, "answer": kw})
                break
        if len(questions) >= num:
            break
    return questions


def _make_mcq_questions(text: str, keywords: List[str], num: int) -> List[Dict]:
    questions: List[Dict] = []
    distractors_pool = [k for k in keywords]
    sentences = nltk.sent_tokenize(text)

    for kw in keywords:
        kw_str = str(kw).strip()
        if not kw_str or kw_str.isnumeric():
            continue
        stem = None
        for s in sentences:
            if kw_str.lower() in s.lower():
                stem = f"In the context, what best matches: '{kw_str}'?"
                break
        if not stem:
            stem = f"What does '{kw_str}' refer to in the content?"

        distractors = [str(d).strip() for d in distractors_pool if str(d).strip() and str(d).strip() != kw_str]
        random.shuffle(distractors)
        options = [kw_str] + distractors[:3]
        random.shuffle(options)

        questions.append({
            "question": stem,
            "options": options,
            "answer": kw_str,
        })
        if len(questions) >= num:
            break

    return questions

def generate_quiz(text: str, num_mcq: int = 5, num_cloze: int = 5) -> Dict[str, List[Dict]]:
    if not text:
        return {"mcq": [], "cloze": []}

    keywords = _extract_keywords(text, max_phrases=max(num_mcq + num_cloze, 10))
    keywords = [str(k) for k in keywords if len(str(k).strip()) > 1]  # Sanitize keywords

    mcq = _make_mcq_questions(text, keywords, num_mcq)
    cloze = _make_cloze_questions(text, keywords, num_cloze)

    return {"mcq": mcq, "cloze": cloze}