# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import email
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from minarca_client.core.imap_backup import decode_header, fetch_and_store, sanitize_folder


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


if __name__ == '__main__':
    unittest.main()
