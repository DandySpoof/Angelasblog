from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField
from flask_login import UserMixin

##WTForm
class CreatePostForm(FlaskForm):
	title = StringField("Blog Post Title", validators=[DataRequired("Please enter title")])
	subtitle = StringField("Subtitle", validators=[DataRequired("Please enter subtitle")])
	img_url = StringField("Blog Image URL", validators=[DataRequired("Please enter url"), URL("Please enter a valid url")])
	body = CKEditorField("Blog Content", validators=[DataRequired("Please write somthing")])
	submit = SubmitField("Submit Post")


class NewUser(UserMixin, FlaskForm):
	name = StringField("Name:", validators=[DataRequired("Please enter your name")])
	email = EmailField("Email:", validators=[DataRequired("Please enter your email"),
	                                         Email("Please enter a valid email address")])
	password = PasswordField("Password:", validators=[DataRequired("Please enter your password")])
	submit = SubmitField("Register")


class Login(FlaskForm):
	email = EmailField("Email:", validators=[DataRequired("Please enter your email"),
	                                         Email("Please enter a valid email address")])
	password = PasswordField("Password:", validators=[DataRequired("Please enter your password")])
	submit = SubmitField("Register")

class CommentForm(FlaskForm):
	body = CKEditorField("Comment", validators=[DataRequired("Please write somthing")])
	submit = SubmitField("Submit Comment")
