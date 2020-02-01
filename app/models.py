from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for
from . import db
from datetime import datetime
from markdown import markdown
import bleach
from bs4 import BeautifulSoup
import os
from app.exceptions import ValidationError

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role')
    
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE], 
            'Moderator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE], 
            'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE, Permission.ADMIN],
        }

        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permission -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r >' % self.name

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    new_email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar = db.Column(db.Text())
    posts = db.relationship('Post', backref="author", lazy="dynamic")
    followed = db.relationship('Follow', 
            foreign_keys=[Follow.follower_id], 
            backref=db.backref('follower', lazy='joined'),
            lazy='dynamic',
            cascade='all, delete-orphan')
    followers = db.relationship('Follow', 
            foreign_keys=[Follow.followed_id],
            backref=db.backref('followed', lazy='joined'),
            lazy='dynamic', 
            cascade='all, delete-orphan')

    comments = db.relationship('Comment', backref="author", lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if (self.email == current_app.config['FLASKY_ADMIN']):
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

        if self.avatar is None:
            self.avatar = self.gravatar()

        self.follow(self)

    @staticmethod
    def update_model():
        for u in User.query.all():
            if u.avatar is None:
                u.avatar = u.gravatar()
                db.session.add(u)
        db.session.commit()

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            user.follow(user)
            db.session.add(user)
            db.session.commit()


    #user account configuration
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Post.author_id == Follow.followed_id).filter(Follow.follower_id == self.id)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)

        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        if self.new_email:
            if self.email != self.new_email:
                self.email = self.new_email
        db.session.add(self)

        return True
    # end of user account configuration

    # permission check
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def gravatar(self, size=100):
        url = 'http://q1.qlogo.cn/g?b=qq&nk={qq}&s={size}'
        return url.format(qq=self.email, size=size)


    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
    
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, other_user):
        if other_user.id is None:
            return False
        return self.followed.filter_by(followed_id=other_user.id).first() is not None

    def is_followed_by(self, _user):
        if _user.id is None:
            return False
        return self.followers.filter_by(follower_id=_user.id).first() is not None
    
    def check_or_create_path(self, path):
            path = os.path.join(current_app.config['APP_DIR'], path[1:])
            if not os.path.isdir(path):
                os.makedirs(path)
        
    def get_personal_path(self, username, subdir, _filename):
        abs_path = url_for('static', filename='uploads/' + username + '/' + subdir + '/' + _filename)
        basedir = os.path.dirname(abs_path)
        self.check_or_create_path(basedir)

        return abs_path

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts', id=self.id),
            'post_count': self.posts.count()
        }

        return json_user

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],                expires_in=expiration)

        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %r >' % self.username

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    slug = db.Column(db.Text, default="void")
    comments = db.relationship('Comment', backref="post", lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags=allowed_tags, strip=True
        ))

        #inital or change post.slug automatally
        target.slug = target.get_slug()

    def get_slug(self):
        soup = BeautifulSoup(self.body_html, "html.parser")
        
        if soup.h1:
            return soup.h1.text
        else:
            return soup.p.text.split('.')[0]


    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comment_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }

        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format="html"), 
            tags=allowed_tags, strip=True))

    
    def to_json(self):
        json_comment = {
                'url': url_for('api.get_comment', id=self.id),
                'post_url': url_for('api.get_post', id=self.post_id),
                'body': self.body,
                'body_html': self.body_html,
                'timestamp': self.timestamp,
                'author_url': url_for('api.get_user', id=self.author_id),
        }

        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')

        return Comment(body=body)




db.event.listen(Comment.body, 'set', Comment.on_changed_body)
db.event.listen(Post.body, 'set', Post.on_changed_body)
