from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, NewUser, Login, CommentForm
from flask_gravatar import Gravatar
from random import randint
from functools import wraps
import os
import psycopg2

#CREATE FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

#CONNECTING TEXT EDITOR FIELD TO APP
ckeditor = CKEditor(app)

#CONNECTING BOOTSTRAP5 TO FLASK
bootstrap = Bootstrap5(app)

#CONNECTING AND CONFIGURING GRAVATAR
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

#CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///blog.db").replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#CONFIGURE TABLES
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)

    # FOREIGN KEY COLUMN
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # A User OBJECT - DEFINING RELATIONSHIP TO USERS - THE COMMENTS IS THE "CHILD (MANY)"
    comment_author = relationship("User", back_populates="comments")

    # FOREIGN KEY COLUMN
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    # A BlogBost OBJECT - DEFINING RELATIONSHIP TO POSTS - THE COMMENTS IS THE "CHILD (MANY)"
    post = relationship("BlogPost", back_populates="comments")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    ## FOREIGN KEY COLUMN
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    ## A User OBJECT - DEFINING RELATIONSHIP TO USERS - THE POSTS IS THE "CHILD (MANY)"
    author = relationship("User", back_populates="posts")

    ## A LIST OF Comment OBJECTS - DEFINING RELATIONSHIP TO COMMENTS, POSTS IT THE - "PARENT (ONE)"
    comments = relationship("Comment", back_populates="post")


    def __repr__(self):
        return f"User id - {self.id}"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    ## A LIST OF BlogPost OBJECTS -  DEFINING RELATIONSHIP TO POSTS, USERS IS THE - "PARENT (ONE)"
    posts = relationship("BlogPost", back_populates="author")

    ## A LIST OF Comment OBJECTS - DEFINING RELATIONSHIP TO COMMENTS, USERS IS THE - "PARENT (ONE)"
    comments = relationship("Comment", back_populates="comment_author")

db.create_all()


#ESTABLISH USER SESSIONS MANAGMENT
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#Security gateway function that allows only admin (id=0) to enter defined routs
def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_active and int(current_user.get_id()) == 1:
            return func(*args, **kwargs)
        print("abort 403")
        return abort(403)

    return decorated_function


#CONFIGURE WEBSITE ROUTES

@app.route('/')
def get_all_posts():
    # test = BlogPost.query.get(1)
    # print(test.author.name)
    # print(type(current_user))
    # print(current_user.get_id())
    print(current_user.is_active)
    posts = BlogPost.query.all()

    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = NewUser()

    if form.validate_on_submit():
        detected_user = User.query.filter_by(email=form.email.data).first()
        hash = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=randint(8,16))

        if detected_user == None:
            user = User(
                email= form.email.data,
                password=hash,
                name= form.name.data,
            )
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for("get_all_posts"))

        flash("This email is already registered. Try logging in instead.")
        flash("second message")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = Login()

    if form.validate_on_submit():
        detected_user = User.query.filter_by(email=form.email.data).first()
        try:
            check_pass = check_password_hash(detected_user.password, form.password.data)
        except:
            pass

        if detected_user == None or check_pass == False:
            flash("Your Email or password is incorrect. Please try again.")
            return redirect(url_for("login"))

        login_user(detected_user)
        return redirect(url_for("get_all_posts"))

    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    form = CommentForm()

    if form.validate_on_submit():
        if current_user.is_active:
            new_comment = Comment(
                body=form.body.data,
                author_id =current_user.get_id(),
                post_id=post_id
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("show_post", post_id=post_id))
        else:
            flash("You must login to comment")
            return redirect(url_for("login"))

    return render_template("post.html", post=requested_post, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.get_id(),
            # author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
@login_required
def edit_post(post_id):
    is_edit = True
    post = BlogPost.query.get(post_id)

    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
    )

    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=is_edit)


@app.route("/delete/<int:post_id>")
@admin_only
@login_required
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
