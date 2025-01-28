from flask import Blueprint
from .auth_routes import auth
from .home_routes import home
# from .reunion_routes import reunion  # Original import

# Updated import with renamed Blueprint
from .reunion_routes import reunion
from .director_routes import director_bp


__all__ = ['auth', 'home', 'reunion', 'director_bp']