..
    Copyright (C) 2020-2023 CERN.

    Invenio-Records-Resources is free software; you can redistribute it and/or
    modify it under the terms of the MIT License; see LICENSE file for more
    details.

Changes
=======

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
