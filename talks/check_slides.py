"""Check that the slide theme preserves implicit Beamer subtitles and reveals.

Run after compiling: python3 -B talks/check_slides.py [path/to/deck.pdf]
Requires pdftotext (Poppler).
"""

from pathlib import Path
import subprocess
import sys
import unicodedata


pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name(
    "zcash-private-transactions.pdf")
text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
text = " ".join(unicodedata.normalize("NFKC", text).split())
# A body-start brace group is parsed as a subtitle; a custom title must show it.
for fragment, count in (
    ("validate(tx):", 7),  # validator plus all six hide-a-field reveals
    ("reads every amount", 1),
    ("Which of the four checks does a nullifier serve", 2),
    ("Why can’t the nullifier simply be the hash of the note commitment?", 2),
    ("Which clause would you delete to counterfeit, and what stops you?", 3),
    ("BN254", 1),  # the three-generations comparison table
):
    assert text.count(fragment) >= count, f"Missing slide content: {fragment}"
print("PASS slide subtitles, tables, checkpoint questions and reveals")
