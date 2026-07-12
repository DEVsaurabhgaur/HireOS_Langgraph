# Checkpoint and Rollback System

Lightweight state snapshotting for error recovery.

## Checkpoint Save

Saved before an agent executes. Excludes credentials and large logs.

## Rollback Action

Triggered on persistent failures to restore the last safe state.
