import re
import unicodedata


PROHIBITED_TERMS = {
    "amk", "aq", "siktir", "sikik", "sikiyim", "sikeyim", "sikerim",
    "orospu", "piç", "pic", "yarrak", "yarak", "göt", "got", "ibne",
    "gerizekalı", "gerizekali", "salak", "aptal", "pezevenk", "kahpe",
    "fuck", "fucking", "motherfucker", "bitch", "asshole", "bastard",
}


def _normalized_tokens(text):
    value = unicodedata.normalize("NFKC", str(text or "")).casefold()
    value = value.translate(str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}))
    value = re.sub(r"(.)\1{2,}", r"\1\1", value)
    return re.findall(r"[a-zçğıöşü]+", value)


def contains_prohibited_language(text):
    tokens = _normalized_tokens(text)
    compact = "".join(tokens)
    for term in PROHIBITED_TERMS:
        normalized_term = "".join(_normalized_tokens(term))
        if normalized_term in tokens or (len(normalized_term) >= 4 and normalized_term in compact):
            return True
    return False
