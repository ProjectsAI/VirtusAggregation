from WebAppOptimizer.app import create_app, db, cli
from WebAppOptimizer.app.models import User, Post, Configuration

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Configuration': Configuration} #'Post': Post