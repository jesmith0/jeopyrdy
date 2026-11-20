"""Generate j-archive game pages for offline parser tests.

The markup mirrors real j-archive pages (checked against game 9000, Show #9157,
and game 4705, which has unrevealed clues, in 2026-11) without copying their
clue text or contestant names:

- the clue page holds each clue in <td id="clue_J_1_1" class="clue_text">,
  plus a hidden response cell <td id="clue_J_1_1_r" class="clue_text"
  style="display:none;"> that the parser must NOT count as a clue
- unrevealed clues are an empty <td class="clue"> with no clue_text at all
- the responses page has one line per revealed clue with
  <em class="correct_response">, sometimes preceded by contestant chatter
- clues are listed row by row: J_1_1, J_2_1, ... J_6_1, J_1_2, ...

`tests/test_live_jarchive.py` checks the real site still looks like this.
"""

ROUNDS = (("J", "JEOPARDY"), ("DJ", "DOUBLE JEOPARDY"))


def clue_id(rnd, col, row):
    return f"{rnd}_{col}_{row}"


def clue_text(cid):
    return f"Clue {cid} text"


def response_text(cid):
    return f"Answer {cid}"


def game_pages(
    title="Show #1234 - Monday, January 1, 2024", unrevealed=(), clue_overrides=None, response_overrides=None
):
    """Return (clue_page_lines, responses_page_lines).

    unrevealed: clue ids ("J_1_1", "FJ", ...) that were never shown on air
    clue_overrides / response_overrides: {clue id: inner HTML} for markup variants
    """
    clue_overrides = clue_overrides or {}
    response_overrides = response_overrides or {}

    def clue_html(cid):
        return clue_overrides.get(cid, clue_text(cid))

    def response_html(cid):
        return response_overrides.get(cid, f'<em class="correct_response">{response_text(cid)}</em>')

    clue_page = [
        "<!DOCTYPE html>",
        "<html><head><title>J! Archive - Show #1234</title></head><body>",
        f'            <div id="game_title"><h1>{title}</h1></div>',
        '<table id="contestants_table"><tr><td class="contestants">Player A, a teacher</td></tr></table>',
    ]
    resp_page = list(clue_page)

    def clue_cell(cid, value):
        if cid in unrevealed:
            return ['    <td class="clue">', "    </td>"]
        return [
            '    <td class="clue">',
            f'<table><tr><td class="clue_header"><td class="clue_value">${value}</td></td></tr>',
            f'    <td id="clue_{cid}" class="clue_text">{clue_html(cid)}</td>',
            f'    <td id="clue_{cid}_r" class="clue_text" style="display:none;">{response_html(cid)}'
            '<br /><br /><table width="100%"><tr><td class="right">Player A</td></tr></table></td>',
            "</table>",
            "    </td>",
        ]

    def resp_line(cid):
        return (
            f'    <td class="clue_text">{response_html(cid)}<br /><br /><table width="100%">'
            '<tr><td class="right">Player A</td></tr></table></td>'
        )

    for r, (rnd, name) in enumerate(ROUNDS):
        clue_page.append(f'<div id="{name.lower().replace(" ", "_")}_round"><h2>{name} ROUND</h2>')
        for col in range(1, 7):
            category = f"{rnd} CATEGORY {col}"
            clue_page.append(f'  <tr><td class="category_name">{category}</td></tr>')
            clue_page.append('  <tr><td class="category_comments"></td></tr>')
        for row in range(1, 6):
            clue_page.append("  <tr>")
            for col in range(1, 7):
                cid = clue_id(rnd, col, row)
                clue_page.extend(clue_cell(cid, (r + 1) * row * 200))
                if cid not in unrevealed:
                    resp_page.append(resp_line(cid))
            clue_page.append("  </tr>")

    clue_page.append('  <tr><td class="category_name">FINAL CATEGORY</td></tr>')
    if "FJ" not in unrevealed:
        clue_page.append(f'    <td id="clue_FJ" class="clue_text">{clue_html("FJ")}</td>')
        clue_page.append(f'    <td id="clue_FJ_r" class="clue_text" style="display:none;">{response_html("FJ")}</td>')
        resp_page.append(resp_line("FJ"))
    clue_page.append("</body></html>")
    resp_page.append("</body></html>")

    return clue_page, resp_page


def all_clue_ids():
    """Clue ids in page (row-major) order, as the parser sees them."""
    ids = [clue_id(rnd, col, row) for rnd, _ in ROUNDS for row in range(1, 6) for col in range(1, 7)]
    return ids + ["FJ"]
