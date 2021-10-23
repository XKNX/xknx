"""Module for providing a dependency container."""
from dependency_injector import containers, providers
from dependency_injector.providers import Configuration, Singleton
from xknx.core import ConnectionManager


class DependencyContainer(containers.DeclarativeContainer):
    """Dependency container."""

    config: Configuration = providers.Configuration()

    connection_manager: Singleton[ConnectionManager] = providers.Singleton(
        ConnectionManager
    )
