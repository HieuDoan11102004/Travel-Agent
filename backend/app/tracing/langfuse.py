"""Langfuse tracing setup for the travel planner agent."""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any


def observe_generation(
    name: str,
    model: str | None = None,
    tags: list[str] | None = None,
):
    """Decorator to trace a function as a generation (LLM call)."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            from langfuse import Langfuse

            from app.config import settings

            langfuse = None
            if settings.langfuse_public_key and settings.langfuse_secret_key:
                langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_base_url,
                )

            if langfuse is None:
                return await func(*args, **kwargs)

            with langfuse.generation(
                name=name,
                model=model or settings.openai_model,
                tags=tags or [],
            ) as generation:
                try:
                    result = await func(*args, **kwargs)
                    generation.output = str(result)[:1000]
                    return result
                except Exception as e:
                    generation.level = "ERROR"
                    generation.metadata = {"error": str(e)}
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            from langfuse import Langfuse

            from app.config import settings

            langfuse = None
            if settings.langfuse_public_key and settings.langfuse_secret_key:
                langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_base_url,
                )

            if langfuse is None:
                return func(*args, **kwargs)

            with langfuse.generation(
                name=name,
                model=model or settings.openai_model,
                tags=tags or [],
            ) as generation:
                try:
                    result = func(*args, **kwargs)
                    generation.output = str(result)[:1000]
                    return result
                except Exception as e:
                    generation.level = "ERROR"
                    generation.metadata = {"error": str(e)}
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def observe_span(
    name: str,
    tags: list[str] | None = None,
):
    """Decorator to trace a function as a span (non-LLM operation)."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            from langfuse import Langfuse

            from app.config import settings

            langfuse = None
            if settings.langfuse_public_key and settings.langfuse_secret_key:
                langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_base_url,
                )

            if langfuse is None:
                return await func(*args, **kwargs)

            with langfuse.span(name=name, tags=tags or []) as span:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.level = "ERROR"
                    span.metadata = {"error": str(e)}
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            from langfuse import Langfuse

            from app.config import settings

            langfuse = None
            if settings.langfuse_public_key and settings.langfuse_secret_key:
                langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_base_url,
                )

            if langfuse is None:
                return func(*args, **kwargs)

            with langfuse.span(name=name, tags=tags or []) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.level = "ERROR"
                    span.metadata = {"error": str(e)}
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def trace_event(name: str, metadata: dict[str, Any] | None = None):
    """Log an event to the current trace."""
    from langfuse import Langfuse

    from app.config import settings

    if settings.langfuse_public_key and settings.langfuse_secret_key:
        langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_base_url,
        )
        langfuse.event(name=name, metadata=metadata or {})
