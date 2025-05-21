# CHANGELOG


## v0.5.0 (2025-05-21)

### Features

- **#69**: Support serializing pydantic.networks.AnyUrl
  ([#70](https://github.com/NextGenContributions/django-ninja-crudl/pull/70),
  [`9c1b382`](https://github.com/NextGenContributions/django-ninja-crudl/commit/9c1b3825319ef271ca9664baf56fa4c2012d98dd))

* feat(#69): Support serializing pydantic.networks.AnyUrl

* style: format code with Ruff Formatter

This commit fixes the style issues introduced in 3b1bf08 according to the output from Ruff
  Formatter.

Details: https://github.com/NextGenContributions/django-ninja-crudl/pull/70

* chore: Fix renderers __all__

* chore: Consolidate type handling branches

Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

Signed-off-by: Phuong Nguyen <7949163+phuongfi91@users.noreply.github.com>

* chore: Missing docstrings

This commit fixes the style issues introduced in 6dc42a8 according to the output from Ruff
  Formatter.

---------

Co-authored-by: deepsource-autofix[bot] <62050782+deepsource-autofix[bot]@users.noreply.github.com>


## v0.4.0 (2025-05-15)

### Features

- **#63**: Unify error responses by using schemas defined by django-ninja-crudl
  ([#64](https://github.com/NextGenContributions/django-ninja-crudl/pull/64),
  [`888ff50`](https://github.com/NextGenContributions/django-ninja-crudl/commit/888ff506b7698faed0ae7b5466a678ac147f396e))

* feat(#63): Unify error responses by using schemas defined by django-ninja-crudl

* style: format code with Ruff Formatter

This commit fixes the style issues introduced in f85633c according to the output from Ruff
  Formatter.

Details: https://github.com/NextGenContributions/django-ninja-crudl/pull/64

---------

Co-authored-by: deepsource-autofix[bot] <62050782+deepsource-autofix[bot]@users.noreply.github.com>


## v0.3.0 (2025-05-05)

### Bug Fixes

- Trunk permission to create/update label
  ([#52](https://github.com/NextGenContributions/django-ninja-crudl/pull/52),
  [`20ae156`](https://github.com/NextGenContributions/django-ninja-crudl/commit/20ae15645ebf3e293c46fec919a0cf93183f216b))

- **#48**: Openapi schemas
  ([#47](https://github.com/NextGenContributions/django-ninja-crudl/pull/47),
  [`fbe4719`](https://github.com/NextGenContributions/django-ninja-crudl/commit/fbe471931bbbaea10011b5ca7923437fda679b92))

* fix: OpenAPI schemas

* style: format code with Ruff Formatter

This commit fixes the style issues introduced in 413a026 according to the output from Ruff
  Formatter.

Details: https://github.com/NextGenContributions/django-ninja-crudl/pull/47

* chore: Fix tests

---------

Co-authored-by: deepsource-autofix[bot] <62050782+deepsource-autofix[bot]@users.noreply.github.com>

- **#49**: Openapi specs examples
  ([#50](https://github.com/NextGenContributions/django-ninja-crudl/pull/50),
  [`08d0161`](https://github.com/NextGenContributions/django-ninja-crudl/commit/08d0161a8dfce2fba978faa7034c5e1e785a47a3))

### Features

- Add nitpick and configs
  ([#15](https://github.com/NextGenContributions/django-ninja-crudl/pull/15),
  [`f02a945`](https://github.com/NextGenContributions/django-ninja-crudl/commit/f02a94534177336e4129c683718cf7638b941af3))

- Support different type of Django relationships
  ([#29](https://github.com/NextGenContributions/django-ninja-crudl/pull/29),
  [`13c93f2`](https://github.com/NextGenContributions/django-ninja-crudl/commit/13c93f23de9a3c2e21b911b0528b52538eeb2133))

* cicd: Implement same workflows as django2pydantic

* cicd: Implement same noxfile as django2pydantic

* fix: Broken tests and pre-2024-christmas refactor WIP

* chore: Fix formatting

* chore: Update nitpick and missing pyrightconfig.json

* chore: Add pylint as dev deps

* chore: Move some configs outside of .trunk and add .vale.ini

* chore: WIP fixes

* style: format code with Ruff Formatter

This commit fixes the style issues introduced in 38752ea according to the output from Ruff
  Formatter.

Details: https://github.com/NextGenContributions/django-ninja-crudl/pull/20

* chore: Restore openapi_extra for create endpoint

This commit fixes the style issues introduced in 580a3ad according to the output from Ruff
  Formatter.

This commit fixes the style issues introduced in fd0908e according to the output from Ruff
  Formatter.

* chore: Restore crudl.py and minor permission fix

* feat: Support m2m relationship update for PUT/PATCH

* chore: Add tests and more WIP

This commit fixes the style issues introduced in cda5e9f according to the output from Ruff
  Formatter.

Details: https://github.com/NextGenContributions/django-ninja-crudl/pull/29

* chore: Undo changes to crudl.py

* chore: Clean up/refactor and fix typings WIP

* chore: More typing changes

* chore: More typing fixes and PatchDict to make beartype happy

* chore: Fix issue with beartype patch_dict being annotated Body

This commit fixes the style issues introduced in 6f11481 according to the output from Ruff
  Formatter.

* chore: Add tests for more forward/reverse relation tests

* chore: Update tests, refactor and fix relation handling logic

This commit fixes the style issues introduced in 93cde0a according to the output from Ruff
  Formatter.

* chore: Fix tests

---------

Co-authored-by: deepsource-autofix[bot] <62050782+deepsource-autofix[bot]@users.noreply.github.com>

- Support reverse urls and permissions
  ([#43](https://github.com/NextGenContributions/django-ninja-crudl/pull/43),
  [`2e30296`](https://github.com/NextGenContributions/django-ninja-crudl/commit/2e3029654eeb6ab44191256c9ccc7f482c95ab2e))

* feat: Support reverse urls and permissions

* chore: Fix tests

* feat: Overhaul permission handlings and tests

* chore: Update uv.lock to reflect latest django2pydantic

* style: format code with Ruff Formatter

This commit fixes the style issues introduced in b20a287 according to the output from Ruff
  Formatter.

Details: https://github.com/NextGenContributions/django-ninja-crudl/pull/43

* chore: Update to nox@2025.2.9 hoping to fix python nox issue

* chore: Explicitly mark uv as nox venv backend

* chore: Update pytest config for coverage report

* chore: Fix none queryset in get_filter_for_list test setup

* feat: Another permission handling overhaul to handle simple relations

This commit fixes the style issues introduced in 3e5d2d8 according to the output from Ruff
  Formatter.

---------

Co-authored-by: deepsource-autofix[bot] <62050782+deepsource-autofix[bot]@users.noreply.github.com>


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

- Authors for build
  ([`6b39b29`](https://github.com/NextGenContributions/django-ninja-crudl/commit/6b39b2966e5ef1693a6a52e6a1de7c553610cbbd))

- Update README.md and bump version to test deployment
  ([`3388b91`](https://github.com/NextGenContributions/django-ninja-crudl/commit/3388b914b793f4db167bce90a9a63567edd121f3))

Signed-off-by: Jukka Hassinen <jukka.hassinen@gmail.com>


## v0.0.1 (2024-11-19)

### Bug Fixes

- Publish pipeline + doc updates
  ([`24aa79a`](https://github.com/NextGenContributions/django-ninja-crudl/commit/24aa79abe91c0ebb7353ca2539e0ab4cdbebee77))
