"""upload_files.py: the local file steps of an upload, the same on every computer.

    sh '<scripts path>/run.sh' upload_files.py put '<uploads file>' '<local folder>'

        Reads the `uploads` list `request_file_uploads` returned, written to a local file once, and
        sends each file's bytes from the local folder to its own signed address. Every address is
        read off the file, so none is ever retyped. Prints one line per file, `sent <filename>` or
        `not sent <filename>: <reason>`, then `sent <n> of <m>`. Exits 1 when any file was not sent.

    sh '<scripts path>/run.sh' upload_files.py duplicates <file> [<file> ...]

        Groups the files whose bytes are identical. Prints one line per group of two or more,
        `same file: <first> = <second> [= ...]`, then `<n> distinct of <m> read`, and last
        `could not read: <file>, ...` with exit 1 when a file could not be opened.

The bytes go out through curl, which trusts the computer's own certificates, so an office network
that inspects secure traffic still lets the upload through.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def put(uploads_file: str, folder: str) -> int:
    try:
        data = json.loads(Path(uploads_file).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        print(f'not read: the uploads file could not be read ({exc.__class__.__name__})')
        return 1
    uploads = data.get('uploads') if isinstance(data, dict) else data
    if not isinstance(uploads, list) or not uploads:
        print('not read: the uploads file holds no uploads list')
        return 1
    # On Windows, a name lookup tries the current folder before PATH unless this is set, so a file
    # named curl in a folder of received drawings would run in its place and see every address.
    os.environ['NoDefaultCurrentDirectoryInExePath'] = '1'
    curl = shutil.which('curl')
    if not curl:
        print('not sent: this computer has no way to send files')
        return 1
    sent = 0
    for row in uploads:
        name = str(row.get('filename', ''))
        url = row.get('signedUrl')
        path = Path(folder) / name
        if not name or not url:
            print(f'not sent {name or "(no name)"}: the uploads file has no address for it')
            continue
        if not path.is_file():
            print(f'not sent {name}: the file is not in the folder')
            continue
        result = subprocess.run(
            [curl, '-fsS', '--retry', '2', '-X', 'PUT', url,
             '-H', 'Content-Type: application/pdf', '--data-binary', f'@{path}'],
            capture_output=True, text=True)
        if result.returncode == 0:
            sent += 1
            print(f'sent {name}')
        else:
            reason = (result.stderr.strip().splitlines() or ['no answer'])[-1]
            reason = reason.split('?', 1)[0]  # never print the signed part of an address
            print(f'not sent {name}: {reason}')
    print(f'sent {sent} of {len(uploads)}')
    return 0 if sent == len(uploads) else 1


def duplicates(files: list[str]) -> int:
    groups: dict[str, list[str]] = {}
    unread: list[str] = []
    for f in files:
        digest = hashlib.sha256()
        try:
            with open(f, 'rb') as handle:
                for block in iter(lambda: handle.read(1 << 20), b''):
                    digest.update(block)
        except OSError:
            unread.append(f)
            continue
        groups.setdefault(digest.hexdigest(), []).append(f)
    for names in groups.values():
        if len(names) > 1:
            print('same file: ' + ' = '.join(names))
    print(f'{len(groups)} distinct of {len(files) - len(unread)} read')
    if unread:
        print('could not read: ' + ', '.join(unread))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='The local file steps of an upload.')
    sub = parser.add_subparsers(dest='mode', required=True)
    p_put = sub.add_parser('put', help="send each file to its signed address")
    p_put.add_argument('uploads_file')
    p_put.add_argument('folder')
    p_dup = sub.add_parser('duplicates', help='group files whose bytes are identical')
    p_dup.add_argument('files', nargs='+')
    args = parser.parse_args()
    if args.mode == 'put':
        return put(args.uploads_file, args.folder)
    return duplicates(args.files)


if __name__ == '__main__':
    sys.exit(main())
