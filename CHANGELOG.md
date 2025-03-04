# CHANGELOG


## v0.2.3 (2024-12-13)

### Bug Fixes

- Partial payload patch ([#9](https://github.com/NextGenContributions/django-ninja-crudl/pull/9),
  [`ba5bda5`](https://github.com/NextGenContributions/django-ninja-crudl/commit/ba5bda5be54e50ebe5eaa0ea482517e9d43db5c7))

* fix: Partial payload patch

* chore: Optimize import

* fix: Patch schema did not have original field's metadata and validations


## v0.2.2 (2024-12-09)

### Bug Fixes

- Missing pre_patch hook
  ([`7c9596d`](https://github.com/NextGenContributions/django-ninja-crudl/commit/7c9596d43beff13c2819483a5704a81229e82dde))


## v0.2.1 (2024-12-09)

### Bug Fixes

- Missing return and incorrect return schema
  ([`35547c4`](https://github.com/NextGenContributions/django-ninja-crudl/commit/35547c440d0515ff6ce3c96fffb8ffe4498e2784))


## v0.2.0 (2024-11-29)

### Documentation

- Added ref to @api_controller + styling
  ([`8fc5eb2`](https://github.com/NextGenContributions/django-ninja-crudl/commit/8fc5eb2f89f01a91b56601335455c229825adf22))

- Update some styling
  ([`17d0adc`](https://github.com/NextGenContributions/django-ninja-crudl/commit/17d0adcdb06a6c059ff453bd3674245c9abda1a1))

### Features

- Support property decorated method fields in the list endpoint
  ([`65fe9fc`](https://github.com/NextGenContributions/django-ninja-crudl/commit/65fe9fced4db786bf0effdf58907164b9ad9763f))


## v0.1.1 (2024-11-22)

### Bug Fixes

- Allow overriding Crudl class methods
  ([`24bc2eb`](https://github.com/NextGenContributions/django-ninja-crudl/commit/24bc2eb60d16ebf6a0b13af2fc590f75e2b606f0))

### Documentation

- Updating docs + added project communication channels
  ([`99192dc`](https://github.com/NextGenContributions/django-ninja-crudl/commit/99192dc48e0654ab8c042067de5f4312bdedb4d8))


## v0.1.0 (2024-11-22)


## v0.0.5 (2024-11-21)

### Bug Fixes

- Project depends on django2pydantic
  ([`bc3c97c`](https://github.com/NextGenContributions/django-ninja-crudl/commit/bc3c97cac187e931df15fc6e26d9164afc421ddb))

- Semantic release version_variables for uv.lock
  ([`988ed43`](https://github.com/NextGenContributions/django-ninja-crudl/commit/988ed432509a7bfa4477e11dfcdddd5534e3e29f))


## v0.0.4 (2024-11-19)

### Features

- Control whether each operation is exposed
  ([`493ac8d`](https://github.com/NextGenContributions/django-ninja-crudl/commit/493ac8d626c158ce9a7dc252be22a67328fb9abd))

- `delete_allowed` boolean to control whether DELETE method is enabled. - `create_fields`,
  `update_fields`, `get_one_fields` or `list_fields` can be set to `None` or undefined which means
  the operation endpoint will not be enabled

Other updates: - Bubbling up some key django2pydantic elements via the public package interface -
  Updated tutorial - Deleted an unneccesary file


## v0.0.3 (2024-11-19)

### Bug Fixes

- Funding link
  ([`afe76f4`](https://github.com/NextGenContributions/django-ninja-crudl/commit/afe76f4a0644c2620bf3729c0e852ba586667db1))


## v0.0.2 (2024-11-19)

### Bug Fixes

- Update README.md and bump version to test deployment
  ([`3388b91`](https://github.com/NextGenContributions/django-ninja-crudl/commit/3388b914b793f4db167bce90a9a63567edd121f3))

Signed-off-by: Jukka Hassinen <jukka.hassinen@gmail.com>

- Authors for build
  ([`6b39b29`](https://github.com/NextGenContributions/django-ninja-crudl/commit/6b39b2966e5ef1693a6a52e6a1de7c553610cbbd))


## v0.0.1 (2024-11-19)

### Bug Fixes

- Publish pipeline + doc updates
  ([`24aa79a`](https://github.com/NextGenContributions/django-ninja-crudl/commit/24aa79abe91c0ebb7353ca2539e0ab4cdbebee77))
