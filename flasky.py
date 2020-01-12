from app import create_app, db
from app.models import User, Role, Permission, Post, Follow, Comment
from flask_migrate import Migrate
from app.fake import users, posts, comments
import os
import sys
import click

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Permission=Permission, Post=Post, users=users, posts=posts, Follow=Follow, Comment=Comment, comments=comments)

@app.cli.command()
def test():
    """Run the unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False, help='Run tests under code coverage')
def test(coverage):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML vesion: file://%s/index.html' % covdir)

        COV.erase()

if '__main__' == __name__:
    app.run(debug=False, host="0.0.0.0") #ssl_context='adhoc')
