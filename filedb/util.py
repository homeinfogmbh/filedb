#! /usr/bin/env python3
"""File database utility"""

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from json import dumps
from logging import DEBUG, INFO, basicConfig, getLogger
from pathlib import Path
from sys import argv, exit  # pylint: disable=W0622
from time import sleep
from typing import Iterable

from blessings import Terminal

# References.
from hinews.orm import Image as HinewsImage
from his.orm import CustomerSettings as HisCustomerSettings
from hisfs.orm import File as HisfsFile
from openimmodb import Anhang as OpenimmodbAnhang, Kontakt as OpenimmodbKontakt

from filedb.orm import File


__all__ = ['main']


TERMINAL = Terminal()
REFERENCES = [
    (OpenimmodbAnhang, 'file'),
    (OpenimmodbKontakt, 'foto'),
    (HisCustomerSettings, '_logo'),
    (HisfsFile, '_file'),
    (HinewsImage, '_file')
]
CLEANUP_QUESTION = 'Type YES if you really want to clean up: '
LOGGER = getLogger(Path(argv[0]).name)
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'


def get_args() -> Namespace:
    """Parses the CLI arguments."""

    parser = ArgumentParser(description='File database utility.')
    parser.add_argument(
        '--non-interactive', action='store_true', help='do not ask questions')
    parser.add_argument(
        '--this-is-not-a-drill', action='store_true',
        help='do not just simulate cleanup')
    parser.add_argument(
        '--debug', action='store_true', help='increase logging verbosity')
    subparsers = parser.add_subparsers(dest='action')
    subparsers.add_parser('refs', help='list references')
    subparsers.add_parser('list', help='list files')
    subparsers.add_parser('clean', help='cleanup orphans')
    return parser.parse_args()


def ask(question: str, default: bool = False,
        yes: Iterable[str] = ('yes', 'y'), ignorecase: bool = True) -> bool:
    """Ask a question and return accordingly."""

    try:
        reply = input(question)
    except EOFError:
        return False

    if not reply:
        return default

    if ignorecase:
        return reply.casefold() in {y.casefold() for y in yes}

    return reply in yes


def user_abort() -> int:
    """Indicate abort by user."""

    print(flush=True)
    LOGGER.error('Aborted by user.')
    return 1


def clean_no_hardlinks(file: File, interactive: bool, simulate: bool) -> bool:
    """Clean files without hardlinks."""

    LOGGER.info('File <%i> is not used.', file.id)

    if not interactive or ask(f'Delete file <{file.id}>? '):
        if not simulate:
            file.remove(force=True)

        LOGGER.info('DELETED <%i> (%s).', file.id, file.sha256sum)
        return True

    LOGGER.info('Keeping <%i>.', file.id)
    return False


def update_hardlinks(file: File, hardlinks: int, simulate: bool) -> bool:
    """Updates a file's hardlinks."""

    if file.hardlinks == hardlinks:
        return False

    old_hardlinks, file.hardlinks = file.hardlinks, hardlinks

    if not simulate:
        file.save()

    LOGGER.info(
        'Updated hardlinks of <%s> from %i to %i.',
        file.id, old_hardlinks, hardlinks)
    return True


def clean(files: dict[int, int], *, interactive: bool = True,
          simulate: bool = True):
    """Clean filedb records."""

    count = 0
    deleted = 0
    kept = 0
    updated = 0

    for count, file in enumerate(File, start=1):
        hardlinks = files[file.id]

        if hardlinks == 0:
            if clean_no_hardlinks(file, interactive, simulate):
                deleted += 1
            else:
                kept += 1
        else:
            kept += 1

            if update_hardlinks(file, hardlinks, simulate):
                updated += 1

    LOGGER.debug('Processed %i files.', count)
    LOGGER.debug('Deleted: %i, kept: %i, updated: %i.', deleted, kept, updated)


def make_clean(files: dict[int, int], interactive: bool,
               simulate: bool) -> int:
    """Invoke cleaning securely."""

    if simulate:
        LOGGER.info("Don't worry. I'm just simulating.")
    else:
        LOGGER.warning('THIS IS NOT A DRILL.')

    LOGGER.info('Starting in three seconds...')

    try:
        sleep(3)
    except KeyboardInterrupt:
        return user_abort()

    try:
        if not interactive or ask(
                CLEANUP_QUESTION, yes=('YES',), ignorecase=False):
            clean(files, interactive=interactive, simulate=simulate)
    except KeyboardInterrupt:
        return user_abort()

    return 0


def main():
    """Runs the file DB utility."""

    args = get_args()
    basicConfig(level=DEBUG if args.debug else INFO, format=LOG_FORMAT)
    interactive = not args.non_interactive
    simulate = not args.this_is_not_a_drill
    files = defaultdict(int)
    retval = 0

    for model, attribute in REFERENCES:
        for record in model:
            file = getattr(record, attribute)

            if file is not None:
                files[file] += 1

    if args.action == 'refs':
        print('Current references:')

        for ref in REFERENCES:
            print(' ' * 3, ref)
    elif args.action == 'list':
        print(dumps(files, indent=2))
    elif args.action == 'clean':
        # Notify user about simulation.
        retval = make_clean(files, interactive, simulate)

    exit(retval)
