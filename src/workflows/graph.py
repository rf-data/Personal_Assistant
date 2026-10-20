"""Deterministic graph validation, no execution or implicit dependency invention."""


def topological(stages):
    items = {s.stage_id: s for s in stages}
    if len(items) != len(stages):
        raise ValueError("Duplicate stage ID")
    for stage in stages:
        if len(set(stage.dependencies)) != len(stage.dependencies) or set(
            stage.dependencies
        ) - set(items):
            raise ValueError("Duplicate or unknown dependency")
    remaining, result = set(items), []
    while remaining:
        ready = sorted(
            k for k in remaining if set(items[k].dependencies) <= set(result)
        )
        if not ready:
            raise ValueError("Dependency cycle")
        result.extend(ready)
        remaining.difference_update(ready)
    return tuple(items[k] for k in result)
