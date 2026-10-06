"""TeX's inline-formula break points, shared by the blog (Temml) and web (LaTeXML) builders.

Input is MathML in Temml's encoding: delimiters carry form="prefix"/"postfix" and fence (stretchy
"false" when plain), commas separator="true", big operators movablelimits, ordinary symbols are
mi. The web builder brings LaTeXML's MathML to that encoding first.
"""

SCRIPTED = {"msub", "msup", "msubsup", "munder", "mover", "munderover", "mmultiscripts"}


def breaks_after(e):
    """TeX breaks an inline formula after a relation or binary operator (TeXbook p. 173), scripts
    and all (⪰_lex); Temml also after a comma. Not after a fence, a unary sign or a big operator."""
    if e.tag in SCRIPTED and len(e):
        e = e[0]
    return (e.tag == "mo" and e.get("form") not in ("prefix", "postfix")
            and "fence" not in e.attrib and "movablelimits" not in e.attrib)


def pieces(top):
    """A formula's outer level cut after each break point, as MathJax cuts a display too. A plain
    delimiter pair is opened when it holds a relation or binary operator: \\{n ∈ S\\} is not a
    group in TeX (\\left\\{ … \\right\\} is: stretchy, kept); a tuple (f₁, …, fₘ) is not opened,
    as TeX does not break after a comma. Glue after the operator stays with it. Chromium
    drops the spacing of a piece holding one operator, so it joins the piece before."""
    def pair(e):
        return (e.tag == "mrow" and len(e) > 2 and e[0].tag == e[-1].tag == "mo"
                and e[0].get("stretchy") == e[-1].get("stretchy") == "false"
                and e[0].get("form") == "prefix" and e[-1].get("form") == "postfix")

    def outer(es):
        out = []
        for e in es:
            inner = outer(e) if pair(e) else []
            out += inner if any(breaks_after(x) and x.get("separator") != "true"
                                for x in inner[:-1]) else [e]
        return out

    top = outer(top)
    out, cur = [], []
    for e, nxt in zip(top, top[1:] + [None]):
        cur.append(e)
        last = next((x for x in reversed(cur) if x.tag != "mspace"), e)
        if nxt is not None and nxt.tag != "mspace" and breaks_after(last):
            if len(cur) == 1 and cur[0].tag == "mo" and out:
                out[-1] += cur
            else:
                out.append(cur)
            cur = []
    return out + [cur] if cur else out
