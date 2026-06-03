# Overview

Sony Projector Protocol provides async Python helpers for local Sony projector discovery and control.

The package is designed for applications such as Home Assistant integrations. It handles Sony protocol framing, parsing, timeouts, identity reads, and protocol-specific errors while leaving protocol selection, entity creation, and user overrides to the upstream application.

## Protocols

- **SDAP** reports discovery metadata such as IP address, product name, serial number, power status, installation location, and SDCP community when the projector advertises it.
- **SDCP / PJ Talk** is a control protocol used by many Sony projectors. SDCP commands include a 4-character community value. The default community is `SONY`.
- **ADCP** is another Sony control protocol. Some projectors require password authentication before ADCP commands can be used.

Discovery does not decide which control protocol to use. An upstream application should choose `protocol="sdcp"` or `protocol="adcp"` from user configuration, a model database, or its own integration logic.

## Start Here

- Use the project README for installation and quick-start examples.
- Use the Home Assistant examples for integration policy and select-entity option lookup.
- Use the command matrix to see which methods are protocol-neutral, ADCP-only, or SDCP-only.
- Use the developer guide when adding command mappings, capability data, or captured-session fixtures.
