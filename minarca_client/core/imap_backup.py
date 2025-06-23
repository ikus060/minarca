# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import argparse
import email
import fnmatch
import imaplib
import logging
import re
import sys
from email.header import decode_header as _decode
from email.utils import parsedate_to_datetime
from pathlib import Path

from minarca_client.core import compat
from minarca_client.locale import _

from .exceptions import BackupError, IMAPListFolderError

LAST_UID_FILE = '.last_uid'

logger = logging.getLogger(__name__)

CHAR_MAP = str.maketrans(
    {
        '<': '\u2039',
        '>': '\u203A',
        ':': '\uA789',
        '"': '\u201C',
        '/': '\u2044',
        '\\': '\u29F5',
        '|': '\u01C0',
        '?': '\uFF1F',
        '*': '\u204E',
        '\x00': '',  # remove NULL
        '\r': '',  # remove Return
        '\n': '',  # remove Newline
    }
)


def match_any(name, patterns, default=True):
    if not patterns:
        return default
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def should_sync_folder(name, include_patterns, exclude_patterns):
    return match_any(name, include_patterns) and not match_any(name, exclude_patterns, default=False)


def decode_header(subject):
    """Decode non-ascii subject header"""
    decoded_subject = _decode(subject)
    all_parts = []
    for part, encoding in decoded_subject:
        if isinstance(part, bytes):
            try:
                part = part.decode(encoding or 'utf-8')
            except Exception:
                part = part.decode('latin1', errors='replace')
        all_parts.append(part)
    return ''.join(all_parts)


def sanitize_folder(name):
    """Replace invalid characters by utf-8 counter part."""
    # < > : " / \\ | ? *
    return name.translate(CHAR_MAP)


def uid_state_file(imap_folder, output_dir):
    return output_dir / sanitize_folder(imap_folder) / '.last_uid'


def load_last_uid(imap_folder, output_dir):
    path = uid_state_file(imap_folder, output_dir)
    if path.exists():
        try:
            return int(path.read_text().strip())
        except ValueError:
            pass  # Ignore invalid uid
    return None


def save_last_uid(folder, uid, output_dir):
    path = uid_state_file(folder, output_dir)
    path.write_text(str(uid))


def save_eml_file(folder, uid, msg, output_dir):
    folder_path = output_dir / sanitize_folder(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    # Extract <Date>
    try:
        dt = parsedate_to_datetime(msg.get('Date'))
        date_str = dt.strftime('%Y%m%d')
    except Exception:
        date_str = 'unknown_date'

    # Extract <From>
    from_header = decode_header(msg.get('From', 'unknown_sender'))
    from_email = re.findall(r'[\w\.-]+@[\w\.-]+', from_header)
    from_email = from_email[0] if from_email else 'unknown'

    # Extract <Subject>
    subject = decode_header(msg.get('Subject', 'no-subject'))

    # Sanitize filename parts
    from_part = sanitize_folder(from_email)
    subject_part = sanitize_folder(subject)[0:50]

    filename = f'{uid}-{date_str}-{from_part}-{subject_part}.eml'

    # Write file to disk compress or not
    with open(folder_path / filename, 'wb') as f:
        f.write(msg.as_bytes())

    logger.info(f'Saved: {folder_path / filename}')


def list_folders(conn):
    """Query list of folder from imap mailbox."""
    result, folders = conn.list()
    if result != 'OK':
        raise IMAPListFolderError()

    for entry in folders:
        parts = entry.decode().split(' "/" ')
        if len(parts) != 2:
            continue
        yield parts[1].strip('"')


def fetch_and_store(conn, imap_folder, output_dir):
    logger.info(_("Syncing folder: %s"), imap_folder)
    result, data = conn.select(f'"{imap_folder}"', readonly=True)
    if result != 'OK':
        logger.error(_("Error selecting folder %s: %s"), imap_folder, data[0].decode())
        return

    last_uid = load_last_uid(imap_folder, output_dir)
    if last_uid:
        new_uid = int(last_uid) + 1
        criteria = f'(UID {new_uid}:*)'
    else:
        criteria = 'ALL'

    result, data = conn.uid('search', None, criteria)
    if result != 'OK':
        logger.error(_("Error searching %s"), imap_folder)
        return

    # Check if response include new messages.
    # IMAP Server return a single message with our uids.
    uids = data[0].split()
    if not uids or (len(uids) == 1 and uids[0].decode() == str(last_uid)):
        logger.info(_("No new messages in folder %s"), imap_folder)
        return

    for uid in uids:
        uid_str = uid.decode()
        result, msg_data = conn.uid('fetch', uid, '(BODY.PEEK[])')
        if result != 'OK' or msg_data is None or msg_data[0] is None:
            logger.error(_("Failed to fetch UID %s"), uid_str)
            continue

        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        save_eml_file(imap_folder, uid_str, msg, output_dir)

        # Save the Last UID on every email.
        save_last_uid(imap_folder, uid.decode(), output_dir)

    logger.info(_("Synced %s message(s) from folder %s."), len(uids), imap_folder)


def parse_args(args):
    """
    Configure imap-backup parser.
    """
    parser = argparse.ArgumentParser(description='Minarca IMAP Backup used to archive mailbox.')

    def _not_empty(value):
        if not value.strip():
            parser.error("Username cannot be empty or whitespace.")
        return value.strip()

    def _read_password(value):
        """Used to read password file."""
        if value.startswith('@'):
            # Read the password file if starting with "@"
            filepath = value[1:]
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    value = f.read().strip()
            except IOError as e:
                parser.error(f"Failed to read password from file '{filepath}': {e}")
            # Verify if the file is properly protected
            try:
                compat.check_secure_file(filepath)
            except PermissionError as e:
                parser.error(str(e))
        return value

    parser.add_argument('--server', required=True, help='IMAP server. e.g: imap.gmail.com')
    parser.add_argument('--port', default=993, type=int, help='Server port. Default to 993.')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL')
    parser.add_argument('--username', required=True, type=_not_empty, help='IMAP user or email address')
    parser.add_argument('--password', required=True, type=_read_password, help='Password or App password')
    parser.add_argument('--output', default='.', help='Output directory')
    parser.add_argument(
        '--include-folder', action='append', help='Glob pattern to include folders (e.g. "INBOX", "Work/*")'
    )
    parser.add_argument(
        '--exclude-folder', action='append', help='Glob pattern to exclude folders', default=["?Gmail*"]
    )
    parsed_args = parser.parse_args(args)
    return parsed_args


def _configure_logging(output_dir):

    file_handler = logging.FileHandler(output_dir / "imap-backup.log", mode='w')
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s"))
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def main_run(args):
    cfg = parse_args(args)

    # Create output directory
    output_dir = Path(cfg.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    _configure_logging(output_dir)

    # Connect to IMAP server
    logger.info(_("Start backup of %s IMAP mailbox from %s:%s"), cfg.username, cfg.server, cfg.port)
    imap = imaplib.IMAP4 if cfg.no_ssl else imaplib.IMAP4_SSL
    conn = imap(cfg.server, cfg.port)
    conn.login(cfg.username, cfg.password)

    try:
        for folder in list_folders(conn):
            if should_sync_folder(folder, cfg.include_folder, cfg.exclude_folder):
                fetch_and_store(conn, folder, output_dir)
            else:
                logger.info(_("Ignore excluded folder %s"), folder)
        logger.info(_("Done"))
    except BackupError as e:
        # Print message to stdout and log file.
        logging.error(e.message)
        if e.detail:
            logging.error(e.detail)
        sys.exit(e.error_code)
    except KeyboardInterrupt:
        logger.error('IMAP Backup interupted')
        exit(130)
    except Exception as e:
        logger.error(str(e), exc_info=1)
        exit(BackupError.error_code)
    finally:
        conn.logout()


def main():
    sys.exit(main_run(sys.argv[1:]))


if __name__ == '__main__':
    main()
