# Circuit Breaker Pattern

HireOS implements a custom 3-state circuit breaker per agent node.

## CLOSED State

Normal operation. Failures are monitored.

## OPEN State

Calls are immediately blocked. Enforces timeout before transitioning.

## HALF_OPEN State

Allows a single probe call to test remote server status.
