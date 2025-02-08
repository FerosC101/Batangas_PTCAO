from .auth import init_auth_routes
from .business import init_business_routes
from .services import init_services_routes
from .main import init_main_routes

__all__ = ['init_auth_routes', 'init_business_routes', 'init_services_routes', 'init_main_routes']