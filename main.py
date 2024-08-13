from typing import Any

from app import create_app, socketio, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Post, Community, Comment, Vacancy, Message, Session

app = create_app()
celery_app = app.extensions["celery"]


@app.shell_context_processor
def make_shell_context() -> dict[str, Any]:
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post, 'Community': Community, 'Comment': Comment,
            'Vacancy': Vacancy, 'Message': Message, 'Session': Session}


def recreate_db() -> None:
    db.drop_all()
    db.create_all()
    db.session.commit()


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
