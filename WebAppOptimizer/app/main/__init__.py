from flask import Blueprint

bp = Blueprint('main', __name__)

from WebAppOptimizer.app.main import routes
