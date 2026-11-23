#!/usr/bin/env python3
"""Read the municipality's income statement (resultaträkning, kommunen) out of annual-report PDFs
and check every line against SCB's accounts (TAB6777).

    python3 scripts/extract_annual_reports.py /path/to/ekonomilabb-kallor

The PDFs and their manifest (arsredovisningar/manifest.csv) live in a separate private repository:
they are public documents, but their pictures can have other rights holders. This script writes
only numbers and page references:

- data/annual-reports/resultatrakning.csv: one row per report, year and line. `arsredovisning`
  is the amount printed in the report (mnkr), `scb` SCB's amount, `sida` the PDF page (1 = first
  page of the file; the printed page number can differ).
- data/annual-reports/jamforelsestorande.csv: every line that mentions jämförelsestörande items,
  with its page, for reading by hand. Such items are one-offs that the model takes out of the base
  year (see data/municipalities/CODE/annual-report-inputs.json).

A report prints several columns (kommunen and koncernen, this year and last, sometimes budget).
The script takes the column whose amount matches SCB within 1.5 mnkr for that year. A line with
no match gets status `ingen träff` and must be read by hand: it is either a difference between
the report and SCB or a layout the script does not read.
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

from prepare_municipality import jsonstat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/annual-reports'

# Labels as printed (patterns matched at the start of a line, lower case) and SCB TAB6777 items.
LINES = [
    ('verksamhetens intäkter', r'verksamhetens (externa )?intäkter', '010'),
    ('verksamhetens kostnader', r'verksamhetens (externa )?kostnader', '022'),
    ('avskrivningar', r'avskrivningar', '025'),
    ('verksamhetens nettokostnader', r'verksamhetens nettokostnad(er)?', '030'),
    ('skatteintäkter', r'skatteintäkter', '040'),
    ('generella statsbidrag och utjämning', r'(generella )?statsbidrag|kommunalekonomisk utjämning|bidrag och utjämning', '050'),
    ('verksamhetens resultat', r'verksamhetens resultat', '035'),
    ('finansiella intäkter', r'finansiella intäkter', '060'),
    ('finansiella kostnader', r'finansiella kostnader', '072'),
    ('resultat efter finansiella poster', r'resultat efter finansiella poster', '080'),
    ('årets resultat', r'årets resultat', '120'),
]
# An amount, optionally followed by a footnote marker: "-1 364 3" is -1 364 with footnote 3.
NUMBER = re.compile(r'^(-?\d{1,3}(?:[ \u00a0.]\d{3})*(?:,\d+)?)(?: \d{1,2})?$')
TOLERANCE = 1.5


def pages(pdf):
    text = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], capture_output=True, text=True, check=True).stdout
    # Some reports put zero-width spaces in the text.
    return text.replace('\u200b', '').replace('\ufeff', '').split('\f')


def numbers(line):
    values = []
    for cell in re.split(r'\s{2,}', line.strip()):
        cell = cell.strip().replace('−', '-').replace('–', '-')
        match = NUMBER.match(cell)
        if match:
            values.append(float(match.group(1).replace(' ', '').replace('\u00a0', '').replace('.', '').replace(',', '.')))
    return values


def statement_pages(texts):
    found = []
    for i, page in enumerate(texts, 1):
        low = page.lower()
        # The income statement: these lines near each other, whatever the heading says.
        if re.search(r'^\s*verksamhetens nettokostnad', low, re.M) and re.search(r'^\s*skatteintäkter', low, re.M) \
                and re.search(r'^\s*(årets resultat|resultat efter finansiella poster)', low, re.M) \
                and re.search(r'^\s*finansiella', low, re.M):
            found.append(i)
    return found


def extract(report, scb):
    texts = pages(report['path'])
    year = int(report['ar'])
    rows = []
    candidates = statement_pages(texts)
    for label, pattern, item in LINES:
        for y in (year, year - 1):
            expected = scb.get(item, {}).get(y)
            hit = None
            for page in candidates:
                lines = texts[page - 1].splitlines()
                for n, line in enumerate(lines):
                    if not re.match(pattern, line.strip().lower()):
                        continue
                    # A long row can wrap: read the amounts on the next line too.
                    following = lines[n + 1] if n + 1 < len(lines) else ''
                    for printed in numbers(line) + numbers(following):
                        # Reports print mnkr or tkr; costs with a minus sign in most and without in some.
                        for unit, value in (('mnkr', printed), ('tkr', printed / 1000)):
                            if expected is not None and min(abs(value - expected), abs(-value - expected)) <= TOLERANCE:
                                hit = (value if (value < 0) == (expected < 0) else -value, page, unit)
                                break
                        if hit:
                            break
                    if hit:
                        break
                if hit:
                    break
            rows.append({'kod': report['kod'], 'kommun': report['kommun'], 'rapport': year, 'ar': y,
                         'post': label, 'scb_post': item,
                         'arsredovisning': '' if not hit else f'{hit[0]:.1f}',
                         'scb': '' if expected is None else f'{expected:.1f}',
                         'skillnad': '' if not hit else f'{hit[0] - expected:.1f}',
                         'sida': '' if not hit else hit[1], 'enhet': '' if not hit else hit[2],
                         'status': 'stämmer' if hit else ('ingen träff' if candidates else 'resultaträkning ej hittad'),
                         'url': report['url']})
    notes = [{'kod': report['kod'], 'kommun': report['kommun'], 'rapport': year, 'sida': i,
              'rad': ' '.join(line.split())[:200], 'url': report['url']}
             for i, page in enumerate(texts, 1) for line in page.splitlines()
             if 'jämförelsestörande' in line.lower() and re.search(r'\d', line)]
    return rows, notes, candidates


def main():
    sources = Path(sys.argv[1]).resolve()
    reports = [dict(r, path=sources / r['fil'])
               for r in csv.DictReader(open(sources / 'arsredovisningar/manifest.csv', encoding='utf-8'))]
    all_rows, all_notes = [], []
    for report in sorted(reports, key=lambda r: (r['kod'], r['ar'], r['del'])):
        book = ROOT / f"data/municipalities/{report['kod']}/base-years.json"
        if report['kod'] == '0583':
            continue  # Motala's accounts are in research/data/annual-ledgers.json, read from the reports by hand
        import json
        archive = ROOT / json.loads(book.read_text())['archive']
        scb = jsonstat(archive / 'TAB6777.json')
        rows, notes, candidates = extract(report, scb)
        all_rows += rows
        all_notes += notes
        hits = sum(r['status'] == 'stämmer' for r in rows)
        print(f"{report['kod']} {report['kommun']} {report['ar']} {report['del'] or ''}: "
              f"sidor {candidates or '-'}, {hits}/{len(rows)} rader stämmer med SCB, "
              f"{len(notes)} rader om jämförelsestörande poster")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (('resultatrakning.csv', all_rows), ('jamforelsestorande.csv', all_notes)):
        if not rows:
            continue
        with open(OUT / name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == '__main__':
    main()
