from playlistmanager.services import pandora, youtubemusic

_SERVICE_MODULES = (pandora, youtubemusic)
SERVICE_MAP = {name: service for service in _SERVICE_MODULES for name in service.NAMES}


def get_service(service_name):
    service = SERVICE_MAP.get(service_name.lower())
    if service:
        return service

    raise ValueError(f"Unsupported service name: {service_name}")

def supported_services_info():
    def service_to_info(service):
        return {
            "display": service.DISPLAY_NAME,
            "names": service.NAMES,
            "package": service
        }

    return [service_to_info(service) for service in _SERVICE_MODULES]
