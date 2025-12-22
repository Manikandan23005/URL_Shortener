from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, default='user')

    user = db.relationship('URLMapping', backref='owner', lazy=True)

    def __repr__(self):
        return f"<User: {self.username} - Role: {self.role}>"
    
    def get_id(self):
        return str(self.id)
    def is_admin(self):
        return self.role == 'admin'
class URLMapping(db.Model):
    __tablename__ = 'URLMapping'
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    max_clicks = db.Column(db.Integer, nullable=True)
    redirect_type = db.Column(db.Integer, default=302)
    is_private = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<URLMapping: {self.short_code} -> {self.original_url}>"

class Click(db.Model):
    __tablename__ = 'Click'
    id = db.Column(db.Integer, primary_key=True)
    url_mapping_id = db.Column(db.Integer, db.ForeignKey('URLMapping.id'), nullable=False)
    click_time = db.Column(db.DateTime, server_default=db.func.now())
    user_agent = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    referrer = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Click: URLMapping ID {self.url_mapping_id} at {self.click_time}>"

