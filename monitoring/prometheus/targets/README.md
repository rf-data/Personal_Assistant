# Explicit target activation

No active `*.json` files are shipped. Copy the matching reviewed example from
`../target-examples/` into a **new** filename here after enabling its Compose
profile. Runtime targets are ignored by Git. Remove discovery files before
turning off a profile to avoid expected-target-down alerts.

`host.json.example` pairs with `host`; `containers.json.example` with `containers`.
Pipeline targets require a real controller/exporter. None exists in this change;
`pipeline.json.example` is only a contract illustration, not an active target.
