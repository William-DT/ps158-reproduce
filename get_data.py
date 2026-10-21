"""Download original Federal Reserve SCF files; never transcribe chart values.

Run: python get_data.py   (Python 3; curl recommended, no Python packages needed)
The 2026 release's summary extracts are already expressed in 2025 dollars.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
YEARS = list(range(1989, 2026, 3))
BASE = 'https://www.federalreserve.gov/econres/'


def download(url, path, refresh=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not refresh:
        return
    temporary = path.with_suffix(path.suffix + '.part')
    try:
        if shutil.which('curl'):
            subprocess.run(['curl', '--fail', '--location', '--silent',
                            '--show-error', '--retry', '2', '--max-time', '90',
                            '--output', str(temporary), url], check=True)
        else:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                temporary.write_bytes(response.read())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Download fresh copies of all files')
    args = parser.parse_args()
    documentation = ROOT / 'data' / 'documentation'
    index = documentation / 'scfindex.html'
    download(BASE + 'scfindex.htm', index, args.refresh)
    # Do not silently use a later release with a different inflation base.
    if 'inflation-adjusted to 2025 dollars' not in index.read_text(errors='replace'):
        raise RuntimeError('The source release has changed. Review the dollar base before continuing.')
    tasks = [(BASE + 'scfindex.htm', index),
             (BASE + 'files/bulletin.macro.txt', documentation / 'bulletin.macro.txt')]
    tasks += [(BASE + f'files/scfp{year}excel.zip',
               ROOT / 'data' / 'raw' / f'scfp{year}excel.zip') for year in YEARS]

    def fetch(task):
        url, path = task
        # The index was fetched and checked above.
        if path != index:
            download(url, path, args.refresh)
        if path.suffix == '.zip':
            with zipfile.ZipFile(path) as archive:
                csvs = [n for n in archive.namelist() if n.lower().endswith('.csv')]
                if len(csvs) != 1 or archive.testzip() is not None:
                    raise ValueError(f'Unexpected or corrupt archive: {path}')
        print(f'Validated {path.relative_to(ROOT)}', flush=True)
        return {'url': url, 'path': str(path.relative_to(ROOT)),
                'bytes': path.stat().st_size,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(fetch, tasks))
    manifest = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
                'dollar_base': 2025, 'survey_years': YEARS, 'files': entries}
    (ROOT / 'data' / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Downloads complete. Next: python plot.py', flush=True)


if __name__ == '__main__':
    main()
