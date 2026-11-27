#!/usr/bin/env python3
"""Restore the original NNUE checkpoints using only Python's standard library."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'restored')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    records = json.loads((root / 'COMPRESSION.json').read_text())
    for record in records:
        relative = Path(record['path'])
        stored = Path(record['stored_as'])
        if any(p.is_absolute() or '..' in p.parts for p in (relative, stored)):
            raise ValueError('Unsafe manifest path')
        target = args.output / relative
        temporary = target.with_suffix(target.suffix + '.part')
        output = None
        try:
            if not args.verify_only:
                target.parent.mkdir(parents=True, exist_ok=True)
                output = temporary.open('wb')
            h = hashlib.sha256()
            size = 0
            with gzip.open(root / stored, 'rb') as source:
                for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
                    h.update(block)
                    size += len(block)
                    if output:
                        output.write(block)
            if size != record['restored_bytes'] or h.hexdigest() != record['sha256']:
                raise ValueError('Checksum mismatch: ' + str(relative))
            if output:
                output.close()
                output = None
                temporary.replace(target)
        except BaseException:
            if output:
                output.close()
            if not args.verify_only:
                temporary.unlink(missing_ok=True)
            raise
        print(('VERIFIED ' if args.verify_only else 'RESTORED ') + str(relative), flush=True)
    print(str(len(records)) + ' checkpoints verified.')

if __name__ == '__main__':
    main()
