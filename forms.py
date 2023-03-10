from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email


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


class NotesForm(FlaskForm):
    description = StringField('Product', [DataRequired(), Length(max=200)])
    text = TextAreaField('Product', [DataRequired(), Length(max=200)])
    submit = SubmitField('SUBMIT')

