"""Shared name normalization for provinces and regencies."""
import re

PROVINCE_ALIASES = {
    "nad": "aceh", "nanggroeacehdarussalam": "aceh",
    "sumut": "sumaterautara", "sumbar": "sumaterabarat", "sumsel": "sumateraselatan",
    "kepri": "kepulauanriau", "babel": "bangkabelitung",
    "kepulauanbangkabelitung": "bangkabelitung",
}
SUMATRA = {"aceh", "sumaterautara", "sumaterabarat", "riau", "kepulauanriau", "jambi",
           "bengkulu", "sumateraselatan", "bangkabelitung", "lampung"}


def norm_province(name) -> str:
    if not isinstance(name, str) or not name.strip():
        return ""
    s = name.lower().replace("sumatra", "sumatera").replace("provinsi", "")
    s = re.sub(r"[^a-z]", "", s)
    return PROVINCE_ALIASES.get(s, s)


def norm_regency(name) -> tuple[str, bool]:
    """Return (normalized name, is_city)."""
    if not isinstance(name, str) or not name.strip():
        return "", False
    s = name.lower().strip()
    is_city = s.startswith("kota ")
    s = re.sub(r"^(kota|kabupaten|kab\.?|regency of)\s+", "", s)
    s = re.sub(r"\s+(regency|city)$", "", s)
    return re.sub(r"[^a-z]", "", s), is_city
