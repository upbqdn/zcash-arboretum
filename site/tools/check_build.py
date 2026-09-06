#!/usr/bin/env python3
"""Build every retained document and enforce the repository's PDF gate.

Outputs and logs stay in build/pdf; --update-pdfs copies passing PDFs beside
their sources only after the entire gate passes.
"""

import argparse
import re
import shutil
import subprocess

import sitegen


def source_errors(text):
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    if any(text.count(token) != 1 for token in
           (r"\begin{document}", r"\end{document}")):
        return ["expected exactly one document environment"]
    if text.split(r"\end{document}", 1)[1].strip():
        return ["non-comment content after end of document"]
    return []


def log_errors(text):
    return re.findall(
        r"^.*(?:Overfull \\[hv]box|LaTeX Warning:.*(?:undefined|multiply defined)"
        r"|Missing character:|destination with the same identifier"
        r"|^! ).*$", text, re.M)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-pdfs", action="store_true")
    args = parser.parse_args()
    out = sitegen.ROOT / "build" / "pdf"
    out.mkdir(parents=True, exist_ok=True)
    sources = [sitegen.ROOT / f"{vol}.tex" for vol in sitegen.VOLUMES]
    sources += sorted((sitegen.ROOT / "parked").glob("*-guide.tex"))
    sources += sorted((sitegen.ROOT / "talks").glob("*.tex"))
    sitegen.omnibus()
    sources.append(sitegen.ROOT / "arboretum-complete.tex")
    failed = []
    for source in sources:
        if errors := source_errors(source.read_text()):
            failed.append(source.name)
            print(f"FAIL {source.name}: {'; '.join(errors)}", flush=True)
            continue
        result = subprocess.run(
            ["tectonic", "-Z", "shell-escape", "--keep-logs",
             "--outdir", str(out), str(source)], cwd=sitegen.ROOT,
            capture_output=True, text=True)
        (out / f"{source.stem}.build-output").write_text(
            result.stdout + result.stderr)
        log = out / f"{source.stem}.log"
        errors = log_errors(log.read_text()) if log.exists() else ["missing log"]
        if result.returncode or errors:
            failed.append(source.name)
            print(f"FAIL {source.name}: {log}", flush=True)
            print("\n".join(errors) or result.stderr[-2000:], flush=True)
        else:
            print(f"PASS {source.relative_to(sitegen.ROOT)}", flush=True)
    if failed:
        raise SystemExit("PDF gate failed: " + ", ".join(failed))
    if args.update_pdfs:
        for source in sources:
            shutil.copyfile(out / f"{source.stem}.pdf", source.with_suffix(".pdf"))
    print(f"PDF gate passed: {len(sources)} documents")


if __name__ == "__main__":
    main()
