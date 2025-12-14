#!/usr/bin/env python3
import re
from pathlib import Path
from bs4 import BeautifulSoup

IN_DIR = Path("data/rag_text")
OUT_DIR = Path("data/rag_text_clean")
OUT_DIR.mkdir(exist_ok=True)


def looks_like_garbage(line: str) -> bool:
    if len(line) < 3:
        return True
    if line.strip().lower() in {
        "voltar", "imprimir", "download", "menu",
        "página inicial", "home", "buscar"
    }:
        return True
    if re.fullmatch(r"[0-9\s\W]+", line):
        return True
    return False


def clean_html_residual(text: str) -> str:
    # remove qualquer resto de tag HTML
    soup = BeautifulSoup(text, "lxml")
    text = soup.get_text("\n")

    # normalizações
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not looks_like_garbage(line):
            lines.append(line)

    return "\n".join(lines).strip()


def main():
    for p in IN_DIR.glob("*.txt"):
        raw = p.read_text(errors="ignore")
        cleaned = clean_html_residual(raw)

        out = OUT_DIR / p.name
        out.write_text(cleaned, encoding="utf-8")

        print(f"[OK] {p.name} -> {out.name} ({len(cleaned)} chars)")


if __name__ == "__main__":
    main()