"""Encrypted Eitr desktop backup and restore library."""

FORMAT_VERSION = 1
ARCHIVE_EXTENSION = ".eitrbackup"


class BackupError(RuntimeError):
    """Expected, user-facing failure during backup, inspection, restore or undo."""


class UnsupportedFormatError(BackupError):
    """Backup archive uses a format version newer than this Eitr installation."""


class PassphraseError(BackupError):
    """Provided passphrase could not decrypt the backup archive."""
