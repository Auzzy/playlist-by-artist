import itertools

from playlistmanager.services import pandora

_SERVICE_MODULES = (pandora, )
SERVICE_MAP = {name: service for service in _SERVICE_MODULES for name in service.NAMES}


def get_service(service_name):
    service = SERVICE_MAP.get(service_name.lower())
    if service:
        return service

    raise ValueError(f"Unsupported service name: {service_name}")
