"""Transactional ISO-to-loose-assets import for the portable launcher."""
import argparse
import contextlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path


def import_iso(image, output, progress_file=None, cancel_file=None):
    if sys.version_info < (3,11):raise ValueError('ISO import requires Python 3.11 or newer')
    from loose_assets import import_disc
    image=Path(image).resolve(strict=True)
    output=Path(output).absolute()
    if not image.is_file() or image.suffix.lower()!='.iso':
        raise ValueError('Choose an Xbox 360 .iso file')
    if output.exists():raise ValueError('Installation folder already exists; select it in the launcher or choose a new destination')
    if not output.parent.is_dir():raise ValueError('Choose an existing parent folder for the installation')
    last_update=0
    def progress(done=0,total=0,message=None):
        nonlocal last_update
        if cancel_file and Path(cancel_file).exists():raise InterruptedError('ISO import cancelled')
        now=time.monotonic()
        if progress_file and (message or done==total or now-last_update>=0.25):
            path=Path(progress_file)
            temporary=path.with_suffix('.tmp')
            label=message or ('Preparing loose resource maps...' if total and done==total else f'Extracting assets: {done}/{total}')
            temporary.write_text(json.dumps(dict(done=done,total=total,message=label)),encoding='utf-8')
            temporary.replace(path)
            last_update=now
    progress(message='Reading Xbox ISO and preparing loose assets...')
    # Keep incomplete output separate. Only our own temporary directory is ever
    # removed; an existing installation is never overwritten or cleaned up.
    staging=Path(tempfile.mkdtemp(prefix='.ch2k8-import-',dir=output.parent))
    try:
        with contextlib.redirect_stdout(sys.stderr):
            import_disc(image,staging/'game',direct=True,progress=progress)
        progress(message='Finalizing loose asset installation...')
        if output.exists():raise ValueError('Installation destination appeared during import; it was left untouched')
        # Windows rename refuses existing destinations, including empty folders.
        (staging/'game').rename(output)
    finally:
        if staging.resolve().parent!=output.parent.resolve() or staging.is_symlink():
            raise ValueError('Unexpected import staging location; cleanup refused')
        shutil.rmtree(staging)
    return dict(game_data=str(output.resolve()),storage='loose-resources')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--progress-file',type=Path)
    parser.add_argument('--cancel-file',type=Path)
    args=parser.parse_args()
    try:
        result=import_iso(args.image,args.output,args.progress_file,args.cancel_file)
    except (Exception,SystemExit) as error:
        print(str(error),file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__=='__main__':sys.exit(main())
