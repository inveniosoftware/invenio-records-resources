# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Tests for what file requests disclose about records and files they can't access.

- Can't read the record: the record and its files are hidden, as if they didn't exist.
- Can read the record: a missing file is reported as such, a forbidden action as
  permission denied.
- Allowed to access a file without being able to read the record (e.g. resource
  access tokens): access to that file is granted.
"""

from io import BytesIO

import pytest
from flask_principal import Identity, Need
from invenio_access import any_user
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_permissions.generators import (
    AuthenticatedUser,
    Generator,
    SystemProcess,
)

from invenio_records_resources.services import FileService
from invenio_records_resources.services.errors import (
    FileKeyNotFoundError,
    PermissionDeniedError,
)
from tests.mock_module.config import FileServiceConfig
from tests.mock_module.permissions import PermissionPolicy


class FileGrant(Generator):
    """Grants access to a single file, like a resource access token."""

    def needs(self, file_key=None, **kwargs):
        """Enabling needs."""
        return [Need("file_grant", file_key)] if file_key else []


class RestrictedPermissionPolicy(PermissionPolicy):
    """Record readable by authenticated users, files restricted."""

    can_read = [AuthenticatedUser(), SystemProcess()]
    can_read_hidden = [SystemProcess()]
    can_read_files = [FileGrant(), SystemProcess()]
    can_get_content_files = [FileGrant(), SystemProcess()]
    can_delete_files = [SystemProcess()]


class RestrictedFileServiceConfig(FileServiceConfig):
    """File service config with restricted files."""

    permission_policy_cls = RestrictedPermissionPolicy


class HiddenRecordFileServiceConfig(RestrictedFileServiceConfig):
    """File service config guarded by a custom record read action."""

    record_read_action = "read_hidden"


@pytest.fixture(scope="module")
def restricted_file_service():
    """File service with restricted files."""
    return FileService(RestrictedFileServiceConfig)


@pytest.fixture()
def anonymous_identity():
    """Identity that can't read the record."""
    identity = Identity(None)
    identity.provides.add(any_user)
    return identity


@pytest.fixture()
def granted_identity(anonymous_identity):
    """Identity that can't read the record, but was granted access to a file."""
    anonymous_identity.provides.add(Need("file_grant", "article.txt"))
    return anonymous_identity


@pytest.fixture()
def recid(file_service, example_file_record, location):
    """Id of a record with a committed "article.txt" file."""
    recid = example_file_record["id"]
    file_service.init_files(system_identity, recid, [{"key": "article.txt"}])
    content = BytesIO(b"test file content")
    file_service.set_file_content(
        system_identity, recid, "article.txt", content, content.getbuffer().nbytes
    )
    file_service.commit_file(system_identity, recid, "article.txt")
    return recid


def _requests(service, identity, recid, file_key):
    """Read and write requests, as callables."""
    return {
        "read_file_metadata": lambda: service.read_file_metadata(
            identity, recid, file_key
        ),
        "get_file_content": lambda: service.get_file_content(identity, recid, file_key),
        "delete_file": lambda: service.delete_file(identity, recid, file_key),
    }


@pytest.mark.parametrize("file_key", ["article.txt", "missing.txt"])
def test_cannot_read_record_hides_record_and_files(
    restricted_file_service, anonymous_identity, recid, file_key
):
    """Users who can't read the record get the same error as for a missing record."""
    requests = _requests(restricted_file_service, anonymous_identity, recid, file_key)
    requests["list_files"] = lambda: restricted_file_service.list_files(
        anonymous_identity, recid
    )
    requests["delete_all_files"] = lambda: restricted_file_service.delete_all_files(
        anonymous_identity, recid
    )
    for request in requests.values():
        with pytest.raises(PIDDoesNotExistError):
            request()

    # indistinguishable from a record that doesn't exist
    with pytest.raises(PIDDoesNotExistError):
        restricted_file_service.read_file_metadata(
            anonymous_identity, "doesnotexist", file_key
        )


def test_can_read_record_missing_file(restricted_file_service, identity_simple, recid):
    """Users who can read the record are told the file doesn't exist."""
    for request in _requests(
        restricted_file_service, identity_simple, recid, "missing.txt"
    ).values():
        with pytest.raises(FileKeyNotFoundError):
            request()


def test_can_read_record_denied_action(restricted_file_service, identity_simple, recid):
    """Users who can read the record are told they lack the requested permission."""
    for request in _requests(
        restricted_file_service, identity_simple, recid, "article.txt"
    ).values():
        with pytest.raises(PermissionDeniedError):
            request()

    with pytest.raises(PermissionDeniedError):
        restricted_file_service.list_files(identity_simple, recid)


def test_allowed_action_without_record_read(
    restricted_file_service, granted_identity, recid
):
    """Access granted to a file only is honoured, without disclosing anything else."""
    result = restricted_file_service.read_file_metadata(
        granted_identity, recid, "article.txt"
    )
    assert result.file_id == "article.txt"
    result = restricted_file_service.get_file_content(
        granted_identity, recid, "article.txt"
    )
    assert result.file_id == "article.txt"

    # not granted, the record stays hidden
    with pytest.raises(PIDDoesNotExistError):
        restricted_file_service.delete_file(granted_identity, recid, "article.txt")
    with pytest.raises(PIDDoesNotExistError):
        restricted_file_service.read_file_metadata(
            granted_identity, recid, "missing.txt"
        )
    with pytest.raises(PIDDoesNotExistError):
        restricted_file_service.list_files(granted_identity, recid)


def test_allowed_action(restricted_file_service, recid):
    """Allowed requests succeed, missing files are reported as such."""
    result = restricted_file_service.get_file_content(
        system_identity, recid, "article.txt"
    )
    assert result.file_id == "article.txt"
    with pytest.raises(FileKeyNotFoundError):
        restricted_file_service.get_file_content(system_identity, recid, "missing.txt")


def test_record_read_action_is_configurable(identity_simple, recid):
    """The record read action is taken from the config, without the action prefix."""
    service = FileService(HiddenRecordFileServiceConfig)
    with pytest.raises(PIDDoesNotExistError):
        service.read_file_metadata(identity_simple, recid, "article.txt")
    with pytest.raises(PIDDoesNotExistError):
        service.read_file_metadata(identity_simple, recid, "missing.txt")
