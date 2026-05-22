# SPDX-FileCopyrightText: 2021-2024 CERN.
# SPDX-License-Identifier: MIT

"""Files processing engine."""

import os


class ProcessorRunner:
    """Runner for file processors."""

    def __init__(self, processors):
        """Initialize the runner."""
        self._processors = processors

    def run(self, file_record):
        """Run file processors or a given file record."""
        for p in self._processors:
            if p.can_process(file_record):
                p.process(file_record)


class FileProcessor:
    """Base class for file processors."""

    @staticmethod
    def file_extension(file_record):
        """Determine if the key has a specific extension."""
        return os.path.splitext(file_record.key)[-1].lower()

    def can_process(self, file_record):
        """Determine if this processor can process a given file record."""
        return False

    def process(self, file_record):
        """Process a file."""
        pass
