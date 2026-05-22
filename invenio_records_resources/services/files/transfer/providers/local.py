# SPDX-FileCopyrightText: 2021-2024 CERN.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

"""Local transfer provider."""

from flask_babel import gettext as _

from ....errors import TransferException
from ..base import Transfer
from ..constants import LOCAL_TRANSFER_TYPE


class LocalTransfer(Transfer):
    """Local transfer.

    This transfers expects the file to be uploaded directly in one go to the
    server. The file content is stored in the record's bucket.
    """

    transfer_type = LOCAL_TRANSFER_TYPE

    def set_file_content(self, stream, content_length):
        """Set file content."""
        if self.file_record.file is not None:
            raise TransferException(
                _(f'File with key "{self.file_record.key}" is already committed.')
            )

        super().set_file_content(stream, content_length)
