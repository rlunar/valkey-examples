# Capsule discovery action

This directory is reserved for the local action that will:

1. validate every `example.yaml`;
2. produce changed-capsule and full-catalog matrices;
3. verify owners and compatibility declarations; and
4. prevent maintained capsules from escaping scheduled runtime CI.

The action must be implemented and blocking before the first runnable capsule
is admitted. Directory-name heuristics must not determine catalog membership.
