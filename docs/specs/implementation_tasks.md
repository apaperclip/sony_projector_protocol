# Sony Projector Protocol Implementation Tasks

This backlog tracks the gaps and risks found while reviewing the current implementation against the product spec.

## MVP Completion

### 1. Align SDAP Discovery Timeout With Spec

Status: Done

Priority: High

The product spec says discovery should listen for 60 seconds.

Acceptance criteria:

- Set `discover()` to default to 60 seconds.
- Update README and product spec examples to rely on the default discovery window.
- Add or update a unit test that locks the intended default timeout behavior without waiting in real time.

### 2. Remove Automatic ADCP Versus SDCP Detection

Status: Done

Priority: High

Upstream applications must choose whether a projector should use ADCP or SDCP. This library should not infer protocol from SDAP advertisements or probe network ports to decide which client to use.

Acceptance criteria:

- Remove `Protocol.AUTO` from the public protocol enum, or deprecate it with a clear validation error before release.
- Require `Projector(..., protocol="adcp")` or `Projector(..., protocol="sdcp")`.
- Remove `_probe_client()` and any fallback connection attempts across protocols.
- Keep SDAP discovery focused on reporting discovered device metadata only.
- Update README, product spec, and tests so no examples or assertions rely on automatic protocol detection.

### 3. Remove Runtime Capability Reporting

Status: Done

Priority: High

Capability persistence belongs in upstream applications such as Home Assistant. The library should raise clear `UnsupportedCommandError` exceptions and avoid keeping runtime capability state.

Acceptance criteria:

- Remove `projector.capabilities`.
- Remove the facade capability helper.
- Keep `UnsupportedCommandError` behavior for protocol-specific or device-unsupported calls, with subclasses that distinguish package/protocol rejection from projector rejection and expose projector responses for debugging.
- Update docs to recommend disabled-by-default upstream entities for optional commands.

### 4. Clarify Protocol-Neutral Versus Protocol-Specific API

Status: Done

Priority: Medium

The public facade mixes protocol-neutral methods with ADCP-only and SDCP-only controls. That may be acceptable, but the public contract should be intentional before release.

Acceptance criteria:

- Classify current public methods as protocol-neutral, ADCP-only, or SDCP-only.
- Document the method support model in README or API docs.
- Ensure protocol-specific methods fail with `PackageUnsupportedCommandError`.
- Consider naming or grouping helpers if the method list becomes confusing for Home Assistant integration authors.

### 5. Complete Identity Support Expectations

Status: Done

Priority: Medium

The spec calls for model name and serial number where supported. ADCP and SDCP identity reads are implemented.

Acceptance criteria:

- Verify whether SDCP/PJ Talk exposes model and serial fields for supported Sony projectors.
- If supported, implement SDCP identity reads.
- If not supported, document that SDCP identity must come from SDAP discovery or configuration.
- Add tests for the selected behavior.

### 6. Clean Packaging Metadata For Release

Status: Done

Priority: Medium

`pyproject.toml` has valid package metadata, but still contains template-era extras and broad lint/tooling settings that do not match this package.

Acceptance criteria:

- Remove unrelated optional extras such as `spark` unless there is a real package need.
- Review project URLs, classifiers, test extras, and coverage settings for PyPI readiness.
- Ensure `python -m build` or the chosen packaging command produces a clean distribution.
- Add a short release checklist for TestPyPI/PyPI publication.

### 7. Make Loopback Auth Test Sandbox-Friendly Or Document It

Status: Done

Priority: Low

The test suite passes when allowed to bind `127.0.0.1`, but the ADCP authentication test fails in restricted sandbox environments.

Acceptance criteria:

- Either refactor the auth test to use a fake stream object instead of a real local TCP server, or mark/document it as requiring loopback bind permission.
- Keep authentication coverage for challenge/digest/command flow.
- Confirm `pytest` passes in the default development environment.

## Version 0.2 Follow-Up

### 8. Add Home Assistant Integration Reference Examples

Status: Done

Priority: Medium

The spec lists Home Assistant reference examples for Version 0.2, and the package API is now far enough along to show intended usage.

Acceptance criteria:

- Add examples for discovery, manual host configuration, polling power/input, setting power/input, and handling exceptions.
- Include unsupported-command handling examples.
- Keep examples package-level, not a full custom component.

### 9. Validate Advanced Command Coverage Against Sony References

Status: In progress

Priority: Medium

The implementation already includes many controls beyond MVP. These should be checked against Sony command references and model support expectations before promising them publicly.

Acceptance criteria:

- Create a command support matrix for implemented ADCP and SDCP methods. Done.
- Mark commands as MVP, Version 0.2, or experimental. Done.
- Confirm command names, item numbers, and value mappings against source references or captured sessions.
- Add tests for any corrected mappings.
- Do not maintain a model capability matrix; projector-level unsupported responses should raise `ProjectorUnsupportedCommandError` with response metadata.

### 10. Add Captured-Session Replay Tests

Status: Done

Priority: Low

Later-stage integration tests against captured projector sessions are called out in the spec and reduce protocol regression risk.

Acceptance criteria:

- Define a captured-session fixture format that avoids storing secrets or personal network details.
- Add at least one ADCP and one SDCP captured response fixture.
- Add parser/client tests that replay captured responses through fake transports.

## Future Release

### 11. Add ADCP Image Adjustment Controls

Status: Future

Priority: Medium

These controls are called out as useful for ADCP-capable models, but they are not implemented in the current package surface and should not block the current release.

Missing controls:

- Contrast.
- Brightness.
- Sharpness.
- Light output.

Acceptance criteria:

- Confirm ADCP command names and value ranges against Sony references or captured sessions.
- Add `get_*` and `set_*` methods for each supported control.
- Add facade methods on `Projector`.
- Add fake-transport tests for command formatting, response parsing, and unsupported responses.
- Update README and command matrix once implemented.
