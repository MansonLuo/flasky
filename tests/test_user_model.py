import unittest
from app.models import User, Permission, AnonymousUser, Role
from flask import current_app
from app import create_app, db

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_password_setter(self):
        u = User(password = 'cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password = 'cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password = 'cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))


    def test_password_salts_are_random(self):
        u = User(password = 'cat')
        u2 = User(password = 'cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_generate_confirmation_token(self):
        u = User()
        token = u.generate_confirmation_token()
        self.assertTrue(token is not None)

    def test_confirm_confirmation_token(self):
        u = User()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))


    def test_user_role(self):
        u = User(email='john@qq.com', password='cat')
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_anomymoust_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_follow_and_unfollow_user_using_is_folling_and_is_followed_byr(self):
        u1 = User()
        u2 = User()

        u1.follow(u2)
        db.session.add_all([u1, u2])
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))

