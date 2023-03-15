from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from wtforms_sqlalchemy.fields import QuerySelectField
from app import Category


class RegistrationForm(FlaskForm):
    user = StringField('User', [DataRequired(), Length(max=50)])
    email = StringField('Email', [DataRequired(), Email(), Length(max=50)])
    password = PasswordField('Password', [DataRequired(), Length(max=50)])
    confirmed_password = PasswordField("Confirm Password", [EqualTo(
        'password', "Password must be the same!"), Length(max=50)])
    i_am_human = BooleanField('I Am Human', [DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', [DataRequired(), Email(), Length(max=50)])
    password = PasswordField('Password', [DataRequired(), Length(max=50)])
    remember_me = BooleanField("Remember me")
    submit = SubmitField('Login')


class CategoryForm(FlaskForm):
    description = StringField('Description', [DataRequired(), Length(max=100)])
    submit = SubmitField('SUBMIT')

class UpdatePhoto(FlaskForm):
    photo = FileField('Add photo', validators=[DataRequired(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('SUBMIT')


# class NoteForm(FlaskForm):
#     description = StringField('Description', [DataRequired(), Length(max=200)])
#     text = TextAreaField('Text', [DataRequired(), Length(max=500)])
#     photo = FileField('Add photo', validators=[DataRequired(), FileAllowed(['jpg', 'png'])])
#     cat = QuerySelectField('Category', query_factory=Category.query.all)
#     submit = SubmitField('SUBMIT')

