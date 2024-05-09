from app import app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post}


if __name__ == '__main__':
    app.run(debug=True)
