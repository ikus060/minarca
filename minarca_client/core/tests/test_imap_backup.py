# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import email
import os
import stat
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest import mock

from minarca_client.core.compat import secure_file
from minarca_client.core.imap_backup import decode_header, fetch_and_store, main_run, parse_args, sanitize_folder


class TestIMAPBackup(unittest.TestCase):

    @mock.patch("minarca_client.core.imap_backup.save_last_uid")
    @mock.patch("minarca_client.core.imap_backup.save_eml_file")
    @mock.patch("minarca_client.core.imap_backup.load_last_uid", return_value=None)
    def test_fetch_and_store_basic(self, mock_load_uid, mock_save_eml, mock_save_uid):
        # Given a mocked IMAP connection with 2 new messages
        conn = mock.MagicMock()
        conn.select.return_value = ("OK", [b""])
        conn.uid.side_effect = [
            ("OK", [b"101 102"]),  # search
            (
                "OK",
                [
                    (
                        b"101 (BODY[])",
                        b"From: test@example.com\r\nSubject: Hello\r\nDate: Mon, 1 Jan 2024 00:00:00 +0000\r\n\r\nBody",
                    )
                ],
            ),
            (
                "OK",
                [
                    (
                        b"102 (BODY[])",
                        b"From: test2@example.com\r\nSubject: World\r\nDate: Mon, 2 Jan 2024 00:00:00 +0000\r\n\r\nBody",
                    )
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # When fetching and storing the messages
            fetch_and_store(conn, "INBOX", output_dir)

            # Then it should save both emails and record their UIDs
            self.assertEqual(mock_save_eml.call_count, 2)
            self.assertEqual(mock_save_uid.call_count, 2)

            args1 = mock_save_eml.call_args_list[0][0]
            self.assertEqual(args1[0], "INBOX")  # folder name
            self.assertIsInstance(args1[2], email.message.Message)

    def test_sanitize_folder_removes_invalid_chars(self):
        # Given a folder name with invalid characters
        name = 'INBOX:Test/Folder*?"'

        # When calling sanitize_folder
        sanitized = sanitize_folder(name)

        # Then the result should not contain any forbidden characters
        self.assertEqual("INBOX\ua789Test\u2044Folder\u204e\uff1f\u201c", sanitized)

    def test_decode_header_handles_encoded_subject(self):
        # Given a subject encoded with UTF-8 Base64
        encoded = '=?UTF-8?B?VGVzdCDDqW1haWw=?='  # "Test émail"

        # When decoding the header
        decoded = decode_header(encoded)

        # Then the result should contain the proper Unicode string
        self.assertEqual("Test émail", decoded)

    def test_minimal_required_args(self):
        # Given a a list of arguments
        args = ['--server', 'imap.example.com', '--username', 'user@example.com', '--password', 'mypassword']
        # When parsing the argument list
        parsed = parse_args(args)
        # Then is return without error.
        self.assertEqual(parsed.server, 'imap.example.com')
        self.assertEqual(parsed.port, 993)
        self.assertFalse(parsed.no_ssl)
        self.assertEqual(parsed.username, 'user@example.com')
        self.assertEqual(parsed.password, 'mypassword')
        self.assertEqual(parsed.output, '.')
        self.assertEqual(parsed.exclude_folder, ['?Gmail*'])
        self.assertIsNone(parsed.include_folder)

    def test_password_from_file(self):
        # Given a password file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write('filepassword\n')
            f.flush()
            filepath = f.name
            secure_file(filepath, mode=0o400)
        # Given a minimal list of arguments
        try:
            args = ['--server', 'imap.example.com', '--username', 'user@example.com', '--password', f'@{filepath}']
            # When parsing the arguments list
            parsed = parse_args(args)
            # Then the password file get read.
            self.assertEqual(parsed.password, 'filepassword')
        finally:
            secure_file(filepath, mode=0o600)
            os.chmod(filepath, stat.S_IWRITE)
            os.remove(filepath)

    def test_username_cannot_be_empty(self):
        # Given an empty username
        args = ['--server', 'imap.example.com', '--username', '   ', '--password', 'mypassword']
        # When parsing the arguments
        with self.assertRaises(SystemExit):
            # Then an exception is raised
            parse_args(args)

    def test_missing_required_argument(self):
        # Given a missing "--server"
        args = ['--username', 'user@example.com', '--password', 'mypassword']
        # When parsing arguments
        with self.assertRaises(SystemExit):
            # Then an exception is raised.
            parse_args(args)

    def test_all_arguments(self):
        # Given all the arguments
        args = [
            '--server',
            'imap.example.com',
            '--port',
            '999',
            '--no-ssl',
            '--username',
            'user@example.com',
            '--password',
            'mypassword',
            '--output',
            '/tmp/output',
            '--include-folder',
            'INBOX',
            '--include-folder',
            'Work/*',
            '--exclude-folder',
            'Spam',
        ]
        # When parsing the arguments list
        parsed = parse_args(args)
        # Then all value are working.
        self.assertEqual(parsed.server, 'imap.example.com')
        self.assertEqual(parsed.port, 999)
        self.assertTrue(parsed.no_ssl)
        self.assertEqual(parsed.username, 'user@example.com')
        self.assertEqual(parsed.password, 'mypassword')
        self.assertEqual(parsed.output, '/tmp/output')
        self.assertEqual(parsed.include_folder, ['INBOX', 'Work/*'])
        self.assertEqual(parsed.exclude_folder, ['?Gmail*', 'Spam'])

    @mock.patch('imaplib.IMAP4_SSL')
    def test_main_run(self, mock_imap):
        # Given a IMAP Server with 3 folders
        mock_conn = mock_imap.return_value
        mock_conn.list.return_value = (
            'OK',
            [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Spam"', b'(\\HasChildren) "/" "[Gmail]"'],
        )
        mock_conn.select.return_value = ('OK', [b'42'])

        def uid_side_effect(command, charset, criteria):
            if command == 'search' and charset is None and criteria == 'ALL':
                return ('OK', [b'1 2 3'])
            return ('NO', [b'Invalid command'])

        mock_conn.uid.side_effect = uid_side_effect
        # When running the script
        # Then no error get raised.
        main_run(['--server', 'imap.example.com', '--username', 'u', '--password', 'p'])


if __name__ == '__main__':
    unittest.main()
