#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

import trafilatura
from bs4 import BeautifulSoup


IN_DIR = Path("data/rag_documents")
OUT_DIR = Path("data/rag_text")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(t: str) -> str:
    if not t:
        return ""
    # remove espaços/linhas em excesso
    t = t.replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def extract_from_html(path: Path) -> str:
    html = path.read_text(errors="ignore")
    # 1) trafilatura (muito bom pra páginas de lei/notícia)
    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
        favor_precision=True,
    )
    if extracted and len(extracted.strip()) > 300:
        return clean_text(extracted)

    # 2) fallback bs4: remove scripts/styles/nav/footer etc.
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        tag.decompose()

    # tenta achar main/article
    main = soup.find("main") or soup.find("article")
    text = (main.get_text("\n") if main else soup.get_text("\n"))
    return clean_text(text)


def extract_from_pdf(path: Path, out_txt: Path) -> str:
    subprocess.run(
        ["pdftotext", "-layout", str(path), str(out_txt)],
        check=False,
    )
    if out_txt.exists():
        return clean_text(out_txt.read_text(errors="ignore"))
    return ""


def extract_from_doc(path: Path) -> str:
    # antiword escreve em stdout
    proc = subprocess.run(["antiword", str(path)], capture_output=True, text=True)
    return clean_text(proc.stdout or "")


def main():
    for p in sorted(IN_DIR.glob("*")):
        suffix = p.suffix.lower()
        out_txt = OUT_DIR / (p.name + ".txt")

        try:
            if suffix in [".html", ".htm"]:
                txt = extract_from_html(p)

            elif suffix == ".pdf":
                tmp_txt = OUT_DIR / (p.name + ".__tmp.txt")
                txt = extract_from_pdf(p, tmp_txt)
                if tmp_txt.exists():
                    tmp_txt.unlink()

            elif suffix == ".doc":
                txt = extract_from_doc(p)

            else:
                # tenta como texto puro
                txt = clean_text(p.read_text(errors="ignore"))

            if len(txt) < 200:
                print(f"[WARN] very short text: {p.name} ({len(txt)} chars)")

            out_txt.write_text(txt, encoding="utf-8")
            print(f"[OK] {p.name} -> {out_txt.name} ({len(txt)} chars)")

        except Exception as e:
            print(f"[ERR] {p.name}: {e}")


if __name__ == "__main__":
    main()
    