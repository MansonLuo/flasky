import unittest
from app import create_app, db
from app.models import User, Role
import re
from app.main import main
from flask import url_for

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        with self.app.test_request_context():
            response = self.client.get(url_for('main.index'))
            self.assertEqual(response.status_code, 200)
            self.assertTrue('Stranger' in response.get_data(as_text=True))

    def test_register_and_login(self):
        #register a new account
        response = self.client.post('/auth/register', data={
            'email': '1558911620@qq.com',
            'username': 'ml',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertEqual(response.status_code, 302)


        # log in with the new account
        response = self.client.post('/auth/login', data={
            'email': '1558911620@qq.com', 
            'password': 'cat'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('Hello,ml', response.get_data(as_text=True)))
        self.assertTrue(
                'You have not confirmed your account yet' in response.get_data(as_text=True))


        # send a confirmation token
        user = User.query.filter_by(email='1558911620@qq.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token), follow_redirects=True)

        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
                'You have confirmed your account' in response.get_data(as_text=True))
    

        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been logged out' in response.get_data(as_text=True))

