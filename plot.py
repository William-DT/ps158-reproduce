"""Reproduce the median family wealth chart from downloaded SCF microdata.

Run get_data.py first. No chart coordinates or transcribed wealth values are
used as data. All estimates come from NETWORTH, WGT, EDCL, and KIDS.
"""
import hashlib
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
GROUPS = [('BA or more', [4], '#202020'), ('HS or less', [1, 2], '#999999')]


def weighted_median(values, weights):
    """Inverse weighted empirical CDF at 0.5; midpoint at an exact half split."""
    values, weights = np.asarray(values, float), np.asarray(weights, float)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError('Missing or empty net-worth data')
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError('Weights must be finite and positive')
    order = np.argsort(values, kind='stable')
    values, weights = values[order], weights[order]
    cumulative = np.cumsum(weights)
    halfway = cumulative[-1] / 2
    index = np.searchsorted(cumulative, halfway, side='left')
    if cumulative[index] == halfway and index + 1 < len(values):
        return float((values[index] + values[index + 1]) / 2)
    return float(values[index])


def estimates():
    manifest_path = ROOT / 'data' / 'manifest.json'
    if not manifest_path.exists():
        raise SystemExit('Run python get_data.py first.')
    manifest = json.loads(manifest_path.read_text())
    if manifest['dollar_base'] != 2025:
        raise ValueError('Expected data expressed in 2025 dollars')
    records = {entry['path']: entry for entry in manifest['files']}
    rows = []
    for year in manifest['survey_years']:
        relative = f'data/raw/scfp{year}excel.zip'
        path = ROOT / relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != records[relative]['sha256']:
            raise ValueError(f'Source checksum mismatch: {relative}')
        with zipfile.ZipFile(path) as archive:
            filename, = [name for name in archive.namelist() if name.lower().endswith('.csv')]
            with archive.open(filename) as stream:
                df = pd.read_csv(stream, usecols=lambda c: c.upper() in
                                 {'NETWORTH', 'WGT', 'EDCL', 'KIDS'})
        df.columns = df.columns.str.upper()
        if not {'NETWORTH', 'WGT', 'EDCL', 'KIDS'}.issubset(df.columns):
            raise ValueError(f'Missing required columns for {year}')
        if df.isna().any().any():
            raise ValueError(f'Missing data in required variables for {year}')
        # KIDS counts children living in the household, not children ever born.
        parents = df.loc[df.KIDS > 0]
        for label, education_codes, _ in GROUPS:
            subset = parents.loc[parents.EDCL.isin(education_codes)]
            rows.append({'year': year, 'education': label,
                         'median_net_worth_2025_dollars': weighted_median(subset.NETWORTH, subset.WGT),
                         'implicate_records': len(subset),
                         'sum_of_weights': subset.WGT.sum()})
    return pd.DataFrame(rows)


def draw(data):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 15,
                         'axes.edgecolor': '#555555', 'axes.linewidth': 1.2})
    fig, ax = plt.subplots(figsize=(12.3, 10.0), dpi=160)
    fig.subplots_adjust(left=0.15, right=0.93, top=0.84, bottom=0.205)
    fig.text(0.016, 0.985, 'Growing wealth gap', ha='left', va='top',
             fontsize=23, weight='bold')
    fig.text(0.016, 0.934,
             'Median net worth by parental education, in constant (2025) dollars, 1989–2025',
             ha='left', va='top', fontsize=16.5)
    # The supplied figure begins the shaded area at the 2013 point even though
    # its annotation identifies the new observations as 2016–2025.
    ax.axvspan(2013, 2026, color='#f0f0f0', zorder=0)
    ax.text(2013.4, 685000, 'Added since Putnam (2015)\n2016–2025',
            ha='left', va='top', fontsize=12.5, color='#777777')
    for label, _, color in GROUPS:
        series = data.loc[data.education.eq(label)].sort_values('year')
        ax.plot(series.year, series.median_net_worth_2025_dollars,
                color=color, linewidth=3.4, solid_capstyle='round', label=label)
        last = series.iloc[-1]
        ax.text(last.year + .65, last.median_net_worth_2025_dollars,
                f'${last.median_net_worth_2025_dollars / 1000:,.0f}K',
                ha='left', va='center', fontsize=14, color='#444444', clip_on=False)
    ax.set_xlim(1988, 2026)
    ax.set_ylim(0, 700000)
    ax.set_xticks(sorted(data.year.unique()))
    ax.set_yticks(np.arange(0, 700001, 100000))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'${value:,.0f}'))
    ax.set_ylabel('Median family net worth', weight='bold', fontsize=15)
    ax.grid(axis='y', color='#dddddd', linewidth=1.1)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='both', labelsize=14, length=5, width=1.1, colors='#444444', pad=6)
    legend = ax.legend(loc='upper left', bbox_to_anchor=(.025, .975),
                       frameon=True, fancybox=False, facecolor='white',
                       edgecolor='#c4c4c4', framealpha=1, fontsize=16,
                       handlelength=1.6, borderpad=.5, labelspacing=.6)
    legend.get_frame().set_linewidth(1.3)
    fig.text(.016, .105,
             'Families with a child of the reference person living at home. Education of the SCF reference person.\n'
             'All dollar values are already inflation-adjusted to 2025 dollars in the Federal Reserve summary extracts.',
             fontsize=11.5, color='#666666', va='top', linespacing=1.35)
    fig.text(.016, .043,
             'Source: Survey of Consumer Finances, Federal Reserve Board, '
             'https://www.federalreserve.gov/econres/scfindex.htm',
             fontsize=10.7, color='#666666', va='top')
    fig.savefig(ROOT / 'figure.png', facecolor='white', dpi=160)
    plt.close(fig)


def report(data):
    pivot = data.pivot(index='year', columns='education', values='median_net_worth_2025_dollars')
    first, last = pivot.iloc[0], pivot.iloc[-1]
    lines = [
        '# Reproduction report', '',
        '## Source and method', '',
        'All estimates were calculated from the original Federal Reserve SCF CSV extracts downloaded by get_data.py.',
        'The extracts cover every triennial survey from 1989 through 2025 and are already in 2025 dollars.',
        'Filter: KIDS > 0. Groups: EDCL = 4 (BA or more); EDCL in {1, 2} (HS or less).',
        'Some college/associate degree (EDCL = 3) is excluded, as in the original.',
        'Use the survey weight WGT and pool all five imputed records per family. The Federal Reserve macro',
        'already divides the original weight by five. Do not divide again. No additional inflation adjustment is applied.',
        'The median is the first net-worth value whose cumulative weight reaches half the group weight',
        '(using the midpoint if the cumulative weight is exactly half). No standard errors are estimated.', '',
        '## Calculated results', '',
        '| Survey year | BA or more | HS or less |',
        '|---|---:|---:|',
    ]
    for year, row in pivot.iterrows():
        lines.append(f'| {year} | ${row["BA or more"]:,.2f} | ${row["HS or less"]:,.2f} |')
    lines += ['', '## Check against the supplied figure', '',
              f'The calculated 2025 endpoints are ${last["BA or more"]:,.0f} and ${last["HS or less"]:,.0f}.',
              'These round to the supplied figure\'s $626K and $72K endpoint labels.',
              'Those two labels are used only for this comparison; they are not inputs to the calculation or plot.',
              'A visual check should compare the full line shapes, dates, grouping, scale, and end labels.',
              'Font and spacing may differ. The original author\'s plotting code and exact quantile convention are not supplied,',
              'so agreement of rounded endpoints is not a claim that every underlying estimate is identical.', '',
              f'The calculated dollar gap increases from ${first["BA or more"] - first["HS or less"]:,.0f}',
              f'in 1989 to ${last["BA or more"] - last["HS or less"]:,.0f} in 2025.', '',
              '## Reproducibility', '',
              'data/manifest.json records the source URLs, downloaded file sizes, SHA-256 hashes, dollar base, and timestamp.',
              'plot.py checks source hashes before calculation. data/estimates.csv contains the complete calculated series.',
              'No wealth value was typed in or extracted from the pixels of the reference figure.', '']
    (ROOT / 'REPORT.md').write_text('\n'.join(lines))


def main():
    data = estimates()
    data.to_csv(ROOT / 'data' / 'estimates.csv', index=False)
    draw(data)
    report(data)
    print(data.to_string(index=False))
    print('\nWrote figure.png, data/estimates.csv, and REPORT.md')


if __name__ == '__main__':
    main()
