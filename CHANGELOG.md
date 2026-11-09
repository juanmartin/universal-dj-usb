# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-11-05

### Features

- **gui:** add a compact About dialog linked from the version label
- add playlist file copy core and path handling ([9680e29](https://github.com/juanmartin/universal-dj-usb/commit/9680e296b762229eee61c67856058bac064c5e03))
- add playlist audio copy workflows to CLI and GUI ([ddb14da](https://github.com/juanmartin/universal-dj-usb/commit/ddb14daa7437b88fdbe09a5e27f09608510b5811))
- **gui:** open output folder after export ([367cdf9](https://github.com/juanmartin/universal-dj-usb/commit/367cdf985ebd1ab9e8de8218c6082a05f6d43df7))
- **gui:** improve export workflow and format folders ([539393b](https://github.com/juanmartin/universal-dj-usb/commit/539393bd722af3d68fbede87a96c20f445c31ed5))

### Bug Fixes

- **nml:** use volume-relative paths ([0e894bd](https://github.com/juanmartin/universal-dj-usb/commit/0e894bd5e5639646b68471539c5d0d5f238598e2))
- **windows:** keep the output folder in copied NML paths
- **gui:** clarify M3U extended-format tooltip ([ae27de7](https://github.com/juanmartin/universal-dj-usb/commit/ae27de731340396d628d6f217826db42014ad5a1))
- **paths:** re-anchor missing Contents paths ([d64541e](https://github.com/juanmartin/universal-dj-usb/commit/d64541ee1846070b6481e9c8c357818f1492ed61))

### Documentation

- add the canonical agent guide, topic docs, and ADR log ([d4418ae](https://github.com/juanmartin/universal-dj-usb/commit/d4418ae41985ccf99948f87a6f2f1fcbc11e4129))
- plan playlist file copying and OneLibrary support ([dad3684](https://github.com/juanmartin/universal-dj-usb/commit/dad368489c32e3bfe7b560b54987decb4e244ec8), [d7e7f16](https://github.com/juanmartin/universal-dj-usb/commit/d7e7f1696a021dcce487c77b56a0b8b42f325581))
- prepare the v0.3.0 release plan ([f95fe3a](https://github.com/juanmartin/universal-dj-usb/commit/f95fe3af053bb89a2cc7e56e15decc8d1e1888ca))

### Build and CI

- only run the Release workflow for tag-driven builds ([97e3f8d](https://github.com/juanmartin/universal-dj-usb/commit/97e3f8d18b37f3093ebcf5febb6bdf0801bd8453))
- bump the app version to 0.3.0 and read it from `pyproject.toml` ([c6306f6](https://github.com/juanmartin/universal-dj-usb/commit/c6306f6ff3f9cf5a8c20403895d38f66459ec1ac))
- update macOS runners and test Windows before packaging ([8a3dfa1](https://github.com/juanmartin/universal-dj-usb/commit/8a3dfa19418466a0edb19a9e20297b7d94859d80))
- name Windows release executables with version/architecture and add `jaunmatrin`
  publisher metadata
