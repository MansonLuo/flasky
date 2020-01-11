import os
from app import create_app, db
from app.models import User, Role, Permission, Post, Follow, Comment
from flask_migrate import Migrate
from app.fake import users, posts, comments


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

# why i add this block of code, cause i foggote add lazy option  to relationship() method about followers relationship property in the User model
"""     
@app.context_processor
def context_processer():
    def my_len(list):
        res = 0
        for i in list:
            res += 1
        return res
    return {'my_len': my_len}
"""  

if '__main__' == __name__:
    app.run(debug=False, host="0.0.0.0") #ssl_context='adhoc')
