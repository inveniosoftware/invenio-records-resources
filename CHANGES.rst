..
    Copyright (C) 2020-2024 CERN.
    Copyright (C) 2024-2025 Graz University of Technology.
    Copyright (C) 2025 Northwestern University.

    Invenio-Records-Resources is free software; you can redistribute it and/or
    modify it under the terms of the MIT License; see LICENSE file for more
    details.

Changes
=======

Version v8.0.0 (released 2025-06-03)

- feat: Pluggable transfers and multipart transfer implementation
  * Implementation of RFC 0072
  * Pluggable transfer types
  * Implementation of multipart transfer in the same place
  * Permission generator for per-transfer-type permissions

Version v7.3.0 (released 2025-04-29)

- config: move allow_upload and allow_archive_download to service
- urls: locate Link warning more appropriately

Version v7.2.0 (released 2025-04-22)

- urls: introduce invenio_url_for-compatible links

Version v7.1.0 (released 2025-04-02)

- files: remove HTTP code from read_content
  * Should resolve file content issues with S3
- i18n: fix untranslated strings in facet
- il8n: replaced gettext with lazy gettext completely
- i18n: removed deprecated messages
- setup: dashes no longer work in setup.cfg babel options

Version v7.0.2 (released 2025-03-10)

- services: records: CompositeSuggestQueryParser: Filter out stopwords

Version v7.0.1 (released 2025-02-06)

- fix: file uploads for >100MB

Version 7.0.0 (release 2024-12-09)

- setup: change to reusable workflows
- setup: bump major dependencies

Version v6.5.0 (released 2024-11-26)

- queryparser: add CompositeSuggestQueryParser
    * Introduces a new query parser focused on better accuracy for
      mappings that contain search-as-you-type or ngram-analyzed fields but
      also secondary information fields that helps to
      disambiquate/narrow-down results.

Version v6.4.0 (released 2024-11-08)

- transformer: add new RestrictedTerm and RestrictedTermValue to restrict search for
  individual fields based on permissions

Version v6.3.1 (released 2024-10-01)

- uow: moved Unit of Work pattern and non-record Operations to invenio-db.
  Added backwards compatible imports.

Version v6.3.0 (released 2024-08-08)

- files: sync file access status
- files: syncing metadata changes for uploaded files
- files: update for retriveing files bucket

Version v6.2.0 (released 2024-08-02)

- service: add bulk create/update method

Version v6.1.1 (released 2024-07-30)

- services: reraise permission errors for records

Version 6.1.0 (released 2024-07-05)

- files: sync metadata on file edit

Version 6.0.0 (released 2024-06-04)

- uow: updated Task Operation to use `apply_async` instead of `delay`
- uow: added Revoke Task Operation

Version 5.9.2 (released 2024-05-22)

- isort: fix imports

Version 5.9.1 (released 2024-05-22)

- errors: add error handler for RecordPermissionDeniedError

Version 5.9.0 (released 2024-05-22)

- errors: add RecordPermissionDeniedError

Version 5.8.0 (released 2024-05-21)

- processors: optionally use PyVIPS for image metadata

Version 5.7.0 (released 2024-05-06)

- files-schema: hide `uri` from serialization
- records: added access field to files

Version 5.6.0 (released 2024-04-23)

- services: add support for nested links

Version 5.5.0 (released 2024-04-09)

* records: add calculated system field with indexing; allows calculated system field to cache the value in the index, and
  use the cached value when reading from the index.

Version 5.4.0 (released 2024-03-22)

- installation: upgrade invenio-app, invenio-base, invenio-accounts
  (removes before_first_request_deprecation)

Version 5.3.0 (released 2024-03-20)

- facets: provide new CombinedTermsFacet (facet to use for nested subjects)

Version 5.2.4 (released 2024-02-27)

- processors: updated file metadata extractor to handle multi-sequence images

Version 5.2.3 (released 2024-02-16)

- schema: avoid mutating original data in pre_load

Version 5.2.2 (released 2024-02-09)

- models: restore file record key unique index

Version 5.2.1 (released 2024-02-09)

- models: remove unique constraint for file record key

Version 5.2.0 (released 2024-02-05)

- models: fix record file indices
- models: add index on object_version_id
- tasks: improve exception log grouping

Version 5.1.0 (released 2024-02-02)

- queryparser: add search field value mapping

Version 5.0.0 (released 2024-01-29)

- installation: bump invenio-accounts

Version 4.19.0 (2024-01-18)

- file manager: copy from other bucket to improve performance

Version 4.18.3 (2023-12-13)

- files: limit amount of files in the REST API

Version 4.18.2 (2023-12-08)

- records: allow overriding of permission action for read method

Version 4.18.1 (2023-11-30)

- files: fix unknown extension return value

Version 4.18.0 (2023-11-29)

- custom_fields: fix EDTF datetime field
- files: changed file key type to string
- files archive: handle broken files

Version 4.17.2 (2023-11-21)

- api: add get file extension from key

Version 4.17.1 (2023-11-09)

- api: do not synchronise db session on delete statement

Version 4.17.0 (2023-11-07)

- file manager: add teardown method (optimise performance)
- api: add remove_all to FileRecord (optimise performance)

Version 4.16.3 (2023-10-26)

- files: updated urls for published files
- files: allowing slash in url

Version 4.16.2 (2023-10-25)

- error: improve error wording in `FailedFileUploadException`

Version 4.16.1 (2023-10-25)

- files: abort with 400 on upload failures

Version 4.16.0 (2023-10-23)

- uow: add record delete index op

Version 4.15.0 (2023-10-20)

- base: add possibility to override search options class

Version 4.14.1 (2023-10-19)

- sort: fallback safely to sort_options

Version 4.14.0 (2023-10-19)

- services: custom_fields: date: use parse_edtf from babel-edtf
- params: validate param option against all available options if exist

Version 4.13.0 (2023-10-19)

- resolver: raises `PIDDoesNotExistError` when record is deleted

Version 4.12.0 (2023-10-11)

- setup: upgrade marshmallow-utils

Version 4.11.7 (2023-10-02)

- bump invenio-stats

Version 4.11.6 (2023-10-02)

- components: handle file upload interruption

Version 4.11.5 (2023-09-29)

- service: add `extra_filter` to reindex method

Version 4.11.4 (2023-09-28)

- params: make sort/facets params immutable

Version 4.11.3 (2023-09-19)

- revert fix bool comparison in api

Version 4.11.2 (2023-09-18)

-  api: fix bool comparison

Version 4.11.1 (2023-09-15)

- records: added link template for read_many calls.

Version 4.11.0 (2023-09-14)

- expanded fields: add null checks
- files: set bucket quota
- service: add sort to read_many

Version 4.10.1 (2023-09-12)

- systemfields: revert files dumping
- systemfields: support conditional dumping of files

Version 4.10.0 (2023-09-05)

- uow: run bulk indexing on post commit hook

Version 4.9.1 (2023-09-05)

- files: dump files order and preview only if entries are dumped (revert)

Version 4.9.0 (2023-09-05)

- files: dump files order and preview only if entries are dumped

Version 4.8.0 (2023-08-25)

- services: move reindex latest records to drafts-resources
- processors: make image formats (checked for metadata) configurable (#484)

Version 4.7.0 (2023-08-16)

- Implement file syncing when publishing a record
- Fixes deletion of files to default to soft deletion unless
  the correct flags are being used.

Version 4.6.0 (2023-08-14)

- service: add a method to reindex all record's versions, with the
  latest first.

Version 4.5.0 (2023-07-11)

- relations: reindex by chunk

Version 4.4.0 (2023-07-11)

- make files component file attributes configurable

Version 4.3.0 (2023-06-15)

- upgrade invenio-accounts

Version 4.2.0 (2023-06-02)

- schemas: fix 'size' value not being dumped if it is 0
- expanded fields: add a non-resolvable system record

Version 4.1.0 (2023-05-04)

- add ServiceResultResolver and ServiceResultProxy

Version 4.0.0 (2023-04-24)

- files: add support for files metadata indexing

Version 3.0.0 (2023-04-20)

- query parser: add allow list and fields to fine tune query parsing

Version 2.0.0 (2023-03-24)

- expandable-field: add a new abstractmethod called `ghost_record` that returns the
  unresolvable representation aka "ghost" of the expanding entity.
- global: renames resolvers to entity_resolvers

Version 1.3.1 (2023-03-23)

- custom-fields: control `field_cls` customization

Version 1.3.0 (2023-03-17)

- errors: add FileKeyNotFoundError

Version 1.2.1 (2023-03-14)

- setup: install invenio_stats

Version 1.2.0 (2023-03-13)

- resource: add event emitter for usage statistics calculation

Version 1.1.1 (2023-03-08)

- dependencies: bump flask-resources

Version 1.1.0 (2023-03-02)

- remove deprecated flask-babelex dependency and imports
- upgrade invenio-pidstore, invenio-records-permissions, invenio-i18n, invenio-records

Version 1.0.9 (2023-02-24)

- serialization: remove files URI for local files

Version 1.0.8 (2023-02-13)

- service: add record indexer service mixin

Version 1.0.7 (2023-02-06)

- service utils: add utility to map query parameters to a dictionary based
  on the service config

Version 1.0.6 (2023-01-23)

- resources: add archive download endpoint for record files

Version 1.0.5 (2023-01-10)

- facets: add facet not found exception

Version 1.0.4 (2022-12-19)

- search: added query parse cls to search config

Version 1.0.3 (2022-12-01)

- Breaking change: FieldsResolver.expand() method is changed to require an identity parameter.
- Breaking change: LinksTemplate.expand() method is changed to require an identity parameter.

Version 1.0.2 (2022-11-25)

- Add i18n translations.

Version 1.0.1 (2022-11-15)

- Compute file status based on storage class.
- Use bulk indexing on when rebuilding indices.

Version 1.0.0

- Initial public release.
