# Reproduction report

## Source and method

All estimates were calculated from the original Federal Reserve SCF CSV extracts downloaded by get_data.py.
The extracts cover every triennial survey from 1989 through 2025 and are already in 2025 dollars.
Filter: KIDS > 0. Groups: EDCL = 4 (BA or more); EDCL in {1, 2} (HS or less).
Some college/associate degree (EDCL = 3) is excluded, as in the original.
Use the survey weight WGT and pool all five imputed records per family. The Federal Reserve macro
already divides the original weight by five. Do not divide again. No additional inflation adjustment is applied.
The median is the first net-worth value whose cumulative weight reaches half the group weight
(using the midpoint if the cumulative weight is exactly half). No standard errors are estimated.

## Calculated results

| Survey year | BA or more | HS or less |
|---|---:|---:|
| 1989 | $330,789.20 | $56,468.82 |
| 1992 | $283,439.87 | $45,305.03 |
| 1995 | $256,627.70 | $61,424.59 |
| 1998 | $364,163.54 | $56,151.03 |
| 2001 | $481,831.29 | $59,450.29 |
| 2004 | $448,807.54 | $62,334.38 |
| 2007 | $520,243.88 | $64,051.70 |
| 2010 | $381,729.93 | $45,588.17 |
| 2013 | $366,627.34 | $30,505.85 |
| 2016 | $375,750.23 | $35,904.00 |
| 2019 | $455,113.58 | $61,527.55 |
| 2022 | $571,232.71 | $70,885.08 |
| 2025 | $625,800.00 | $71,790.00 |

## Check against the supplied figure

The calculated 2025 endpoints are $625,800 and $71,790.
These round to the supplied figure's $626K and $72K endpoint labels.
Those two labels are used only for this comparison; they are not inputs to the calculation or plot.
A visual check should compare the full line shapes, dates, grouping, scale, and end labels.
Font and spacing may differ. The original author's plotting code and exact quantile convention are not supplied,
so agreement of rounded endpoints is not a claim that every underlying estimate is identical.

The calculated dollar gap increases from $274,320
in 1989 to $554,010 in 2025.

## Reproducibility

data/manifest.json records the source URLs, downloaded file sizes, SHA-256 hashes, dollar base, and timestamp.
plot.py checks source hashes before calculation. data/estimates.csv contains the complete calculated series.
No wealth value was typed in or extracted from the pixels of the reference figure.
