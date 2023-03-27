from flask import Flask, request, jsonify, json, session 
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:highspeed12@localhost/postgres'
app.config['SECRET_KEY'] = 'dsdnsldj23j24dfdfvslje'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

    
@app.route('/register', methods=['POST'])
def register_user():
    data = json.loads(request.data)
    username = data['username']
    email = data['email']
    password = data['password']
    hashed_password = generate_password_hash(password)
    if not username or not email or not password:
        return jsonify({'message': 'Username,email and content are required'})
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}) 


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = json.loads(request.data)
        email = data['email']
        password = data['password']
        if not email or not password:
            return jsonify({'error': 'Email or password is missing.'}), 400
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({'error': 'Invalid email or password'}), 401
        session['user_id'] = user.id
        session['email'] = email
        return jsonify({'message': 'Login successful!'}), 200
    
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful!'}), 200

@app.route('/create', methods=['POST'])
def create_blog_post():
    data = json.loads(request.data)
    title = data['title']
    content = data['content']
    user_id = data['user_id']
    blog_post = Post(title=title, content=content, user_id=user_id)
    db.session.add(blog_post)
    db.session.commit()
    return jsonify({'message': 'Blog post created successfully'})

@app.route('/read/<int:post_id>', methods=['GET'])
def get_blog_post(post_id):
    blog_post = Post.query.get_or_404(post_id)
    return jsonify({
        'id': blog_post.id,
        'title': blog_post.title,
        'content': blog_post.content,
        'date_posted': blog_post.date_posted
    })
    
@app.route('/update/<int:post_id>', methods=['PUT'])
def update_blog_post(post_id):
    blog_post = Post.query.get_or_404(post_id)
    data = json.loads(request.data)
    blog_post.title = data['title']
    blog_post.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Blog post updated successfully'})    

@app.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_blog_post(post_id):
    blog_post = Post.query.get(post_id)
    if not blog_post:
        return jsonify({'error': 'Blog post not found'}), 404
    db.session.delete(blog_post)
    db.session.commit()
    return jsonify({'message': 'Blog post deleted successfully'}), 200
      
      
@app.route('/home', methods=['GET'])
def get_blog_posts():
    blog_posts = Post.query.all()
    blog_post_list = []
    for post in blog_posts:
        name = User.query.filter_by(id=post.user_id).first()
        blog_post_list.append({
            'id': post.id,
            'title': post.title,
            'date_posted': post.date_posted,
            'Username': name.username,
        })
    return jsonify(blog_post_list) 

@app.route('/single/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    author = User.query.filter_by(id=post.user_id).first()
    blog_post_dict = {
        'id': post.id,
        'title': post.title,
        'date_posted': post.date_posted,
        'username': author.username,
    }
    return jsonify(blog_post_dict)


@app.route('/pagination', methods=['GET'])
def get_pagination_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    posts = Post.query.paginate(page=page, per_page=per_page)
    blog_posts_list = []
    for post in posts.items:
        author = User.query.filter_by(id=post.user_id).first()
        blog_post_dict = {
            'id': post.id,
            'title': post.title,
            'Username': author.username,
            'date_posted': post.date_posted
        }
        blog_posts_list.append(blog_post_dict)
    pagination_dict = {
        'page': posts.page,
        'per_page': posts.per_page,
        'total_pages': posts.pages,
        'total_posts': posts.total
    }
    return jsonify({
        'blog_posts': blog_posts_list,
        'pagination': pagination_dict
    })    
    
if __name__ == '__main__':
    with app.app_context():
       db.create_all()
       app.run(port=5433,debug=True)    