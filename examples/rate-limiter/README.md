# Rate Limiter

Examples that enforce request quotas, rolling windows, token budgets, and
related admission-control policies belong here.

The primary learning objective must remain Valkey-backed rate limiting.
Authentication, gateway products, and generic web-framework tutorials are out
of scope.

## Examples

- [Sliding-window rate limiter with Python and Flask](sliding-window-python-flask/)
  — compares atomic `WATCH`/`MULTI`/`EXEC` and Lua implementations through one
  HTTP contract.
- [Sliding-window rate limiter with Python and FastAPI](sliding-window-python-fastapi/)
  — same sliding-window implementations using an asynchronous GLIDE client
  managed by FastAPI lifespan, with Uvicorn as the ASGI server.
