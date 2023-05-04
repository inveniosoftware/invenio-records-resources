..
    Copyright (C) 2020-2023 CERN.

    Invenio-Records-Resources is free software; you can redistribute it and/or
    modify it under the terms of the MIT License; see LICENSE file for more
    details.

Changes
=======

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
