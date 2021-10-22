"""Module for providing a dependency container."""
from dependency_injector import containers, providers
from dependency_injector.providers import Configuration
from xknx.core import ConnectionManager


class DependencyContainer(containers.DeclarativeContainer):  # type: ignore
    """Dependency container."""

    config: Configuration = providers.Configuration()

    connection_manager: ConnectionManager = providers.Singleton(ConnectionManager)
