# CHANGELOG


## v0.6.0 (2025-07-10)

### Features

- Python 3.12-3.13 & django 5.1-5.2 support + doc updates (#110)
  ([#110](https://github.com/NextGenContributions/django-ninja-crudl/pull/110),
  [`652aa09`](https://github.com/NextGenContributions/django-ninja-crudl/commit/652aa09e83b18a4820e6f381bf1970a78208071e))


## v0.5.4 (2025-06-09)

### Bug Fixes

- Full_clean() not getting called on update (#91)
  ([#91](https://github.com/NextGenContributions/django-ninja-crudl/pull/91),
  [`090fb8e`](https://github.com/NextGenContributions/django-ninja-crudl/commit/090fb8ecf2ffb77ba0217f23554f7856ebed2156))


## v0.5.3 (2025-05-28)

### Bug Fixes

- Add missing base filter for delete (#79)
  ([#79](https://github.com/NextGenContributions/django-ninja-crudl/pull/79),
  [`5eba170`](https://github.com/NextGenContributions/django-ninja-crudl/commit/5eba17072bf330002a8ae10ad6a41ac92e898ef7))


## v0.5.2 (2025-05-27)

### Bug Fixes

- Incorrect handling of relation updates (#76)
  ([#76](https://github.com/NextGenContributions/django-ninja-crudl/pull/76),
  [`c61ab05`](https://github.com/NextGenContributions/django-ninja-crudl/commit/c61ab05109059e10239bb6e9147d58e68c3dc8fc))


## v0.5.1 (2025-05-21)

### Bug Fixes

- List endpoint support for model's property and related fields (#71)
  ([#71](https://github.com/NextGenContributions/django-ninja-crudl/pull/71),
  [`5eee317`](https://github.com/NextGenContributions/django-ninja-crudl/commit/5eee3170ac63e51fb38743e53a65071bdc7524d9))


## v0.5.0 (2025-05-21)

### Features

- **#69**: Support serializing pydantic.networks.AnyUrl (#70)
  ([#70](https://github.com/NextGenContributions/django-ninja-crudl/pull/70),
  [`9c1b382`](https://github.com/NextGenContributions/django-ninja-crudl/commit/9c1b3825319ef271ca9664baf56fa4c2012d98dd))


## v0.4.0 (2025-05-15)

### Features

- **#63**: Unify error responses by using schemas defined by django-ninja-crudl (#64)
  ([#64](https://github.com/NextGenContributions/django-ninja-crudl/pull/64),
  [`888ff50`](https://github.com/NextGenContributions/django-ninja-crudl/commit/888ff506b7698faed0ae7b5466a678ac147f396e))


## v0.3.0 (2025-05-05)

### Bug Fixes

- Trunk permission to create/update label (#52)
  ([#52](https://github.com/NextGenContributions/django-ninja-crudl/pull/52),
  [`20ae156`](https://github.com/NextGenContributions/django-ninja-crudl/commit/20ae15645ebf3e293c46fec919a0cf93183f216b))

- **#48**: OpenAPI schemas (#47)
  ([#47](https://github.com/NextGenContributions/django-ninja-crudl/pull/47),
  [`fbe4719`](https://github.com/NextGenContributions/django-ninja-crudl/commit/fbe471931bbbaea10011b5ca7923437fda679b92))

- **#49**: OpenAPI specs examples (#50)
  ([#50](https://github.com/NextGenContributions/django-ninja-crudl/pull/50),
  [`08d0161`](https://github.com/NextGenContributions/django-ninja-crudl/commit/08d0161a8dfce2fba978faa7034c5e1e785a47a3))

### Features

- Add nitpick and configs (#15)
  ([#15](https://github.com/NextGenContributions/django-ninja-crudl/pull/15),
  [`f02a945`](https://github.com/NextGenContributions/django-ninja-crudl/commit/f02a94534177336e4129c683718cf7638b941af3))

- Support different type of Django relationships (#29)
  ([#29](https://github.com/NextGenContributions/django-ninja-crudl/pull/29),
  [`13c93f2`](https://github.com/NextGenContributions/django-ninja-crudl/commit/13c93f23de9a3c2e21b911b0528b52538eeb2133))

- Support reverse urls and permissions (#43)
  ([#43](https://github.com/NextGenContributions/django-ninja-crudl/pull/43),
  [`2e30296`](https://github.com/NextGenContributions/django-ninja-crudl/commit/2e3029654eeb6ab44191256c9ccc7f482c95ab2e))


## v0.2.3 (2024-12-13)

### Bug Fixes

- Partial payload patch (#9)
  ([#9](https://github.com/NextGenContributions/django-ninja-crudl/pull/9),
  [`ba5bda5`](https://github.com/NextGenContributions/django-ninja-crudl/commit/ba5bda5be54e50ebe5eaa0ea482517e9d43db5c7))


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


## v0.0.1 (2024-11-19)

### Bug Fixes

- Publish pipeline + doc updates
  ([`24aa79a`](https://github.com/NextGenContributions/django-ninja-crudl/commit/24aa79abe91c0ebb7353ca2539e0ab4cdbebee77))
