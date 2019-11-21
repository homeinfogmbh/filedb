#! /usr/bin/env python3
"""File database utility"""

from argparse import ArgumentParser
from collections import defaultdict
from json import dumps
from logging import DEBUG, INFO, basicConfig, getLogger
from pathlib import Path
from sys import argv, exit  # pylint: disable=W0622
from time import sleep

from blessings import Terminal

from filedb.orm import File

# References.
from hinews.orm import Image as HinewsImage
from his.orm import CustomerSettings as HisCustomerSettings
from hisfs.orm import File as HisfsFile
from openimmodb import Anhang as OpenimmodbAnhang, Kontakt as OpenimmodbKontakt


__all__ = ['main']


TERMINAL = Terminal()
REFERENCES = (
    (OpenimmodbAnhang, 'file'),
    (OpenimmodbKontakt, 'foto'),
    (HisCustomerSettings, '_logo'),
    (HisfsFile, '_file'),
    (HinewsImage, '_file'))
CLEANUP_QUESTION = 'Type YES if you really want to clean up: '
LOGGER = getLogger(Path(argv[0]).name)
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'


def get_args():
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


def ask(question, default=False, yes=('yes', 'y'), ignorecase=True):
    """Ask a question and return accordingly."""

    try:
        reply = input(question)
    except EOFError:
        return False

    if not reply:
        return default

    if ignorecase:
        return reply.lower() in (y.lower() for y in yes)

    return reply in yes


def user_abort():
    """Indicate abort by user."""

    print(flush=True)
    LOGGER.error('Aborted by user.')
    return 1


def clean(files, *, interactive=True, simulate=True):
    """Clean filedb records."""

    count = 0
    deleted = 0
    kept = 0
    updated = 0

    for count, file in enumerate(File, start=1):
        hardlinks = files[file.id]

        if hardlinks == 0:
            LOGGER.info('File <%i> is not used.', file.id)

            if not interactive or ask(f'Delete file <{file.id}>? '):
                if not simulate:
                    file.remove(force=True)

                deleted += 1
                LOGGER.info('DELETED <%i> (%s).', file.id, file.sha256sum)
            else:
                kept += 1
                LOGGER.info('Keeping <%i>.', file.id)
        else:
            kept += 1

            if file.hardlinks != hardlinks:
                old_hardlinks, file.hardlinks = file.hardlinks, hardlinks

                if not simulate:
                    file.save()

                updated += 1
                LOGGER.info(
                    'Updated hardlinks of <%s> from %i to %i.',
                    file.id, old_hardlinks, hardlinks)

    LOGGER.debug('Processed %i files.', count)
    LOGGER.debug('Deleted: %i, kept: %i, updated: %i.', deleted, kept, updated)


def make_clean(files, interactive, simulate):
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
