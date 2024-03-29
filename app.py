import os
import json
import forms
from datetime import datetime
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, logout_user, login_user
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import backref
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect
import secrets
from PIL import Image
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from wtforms_sqlalchemy.fields import QuerySelectField


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.app_context().push()
CORS(app)
ma = Marshmallow(app)
csrf = CSRFProtect(app)


# app.config.from_prefixed_env()
app.config['SECRET_KEY'] = "Your_secret_string"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'Login'
login_manager.login_message_category = 'info'
login_manager.login_message = "You need to Login!"


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column("user", db.String(50), nullable=False)
    email = db.Column("email", db.String(50), unique=True, nullable=False)
    password = db.Column("password", db.String(50), nullable=False)


class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column("description", db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")


class Notes(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column("description", db.String, nullable=False)
    text = db.Column("text", db.String(500), nullable=False)
    photo = db.Column(db.String(20), nullable=False)
    category = db.Column("category", db.String(
        20), nullable=False, default="Other")
    date = db.Column(db.DateTime, nullable=True, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")


# ************************************* USER REGISTRATION / LOGIN ********************


@app.route("/register", methods=['GET', 'POST'])
def register():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        crypted_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(user=form.user.data, email=form.email.data,
                    password=crypted_password)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Email already registered. Please choose another.', 'danger')
            return redirect(url_for('register'))
        flash('Success! Now you can login', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Something wrong. Please check email and password!', 'danger')
    return render_template('login.html', title='login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(user_id):
    db.create_all()
    return User.query.get(int(user_id))


@app.route("/")
def index():
    if current_user.is_authenticated:
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template("index.html", categories=categories, user=current_user.user)
    else:
        return render_template("index.html")


# ******************************** Category LIST *********************************

@app.route("/categories")
def categories():
    db.create_all()
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        categories = Category.query.filter_by(
            user_id=current_user.id).paginate(page=page, per_page=8)
        return render_template("categories.html", categories=categories, user=current_user.user)
    else:
        return render_template("index.html")


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    db.create_all()
    if current_user.is_authenticated:
        form = forms.CategoryForm()
        if form.validate_on_submit():
            new_category = Category(
                description=form.description.data, user_id=current_user.id)
            db.session.add(new_category)
            db.session.commit()
            flash(f"Category added!", 'success')
            return redirect(url_for('categories'))
        return render_template("add_category.html", form=form)
    else:
        return render_template("index.html")


@app.route("/edit_category/<int:id>", methods=['GET', 'POST'])
def edit_category(id):
    if current_user.is_authenticated:
        try:
            get_category_user_id = Category.query.filter_by(id=id).first()
            if current_user.id != get_category_user_id.user_id:
                return render_template("401.html")
            form = forms.CategoryForm()
            category = Category.query.get(id)
            if form.validate_on_submit():
                category.description = form.description.data
                db.session.commit()
                return redirect(url_for('categories'))
            return render_template("edit_category.html", form=form, category=category)
        except AttributeError:
            return render_template("404.html")
    else:
        return render_template("index.html")


@app.route("/delete_category/<int:id>")
def delete_category(id):
    if current_user.is_authenticated:
        try:
            get_category_user_id = Category.query.filter_by(id=id).first()
            if current_user.id != get_category_user_id.user_id:
                return render_template("401.html")
            category = Category.query.get(id)
            db.session.delete(category)
            db.session.commit()
            return redirect(url_for('categories'))
        except AttributeError:
            return render_template("404.html")
    else:
        return render_template("index.html")

# ******************************** SAVE PICTURE *********************************


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path + '/static/images', picture_fn)
    print(app.root_path)
    print(picture_path)
    output_size = (160, 160)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

# ******************************** FORM CLASSES *********************************


class NoteForm(FlaskForm):
    description = StringField('Description', [DataRequired(), Length(max=200)])
    text = StringField('Text', [DataRequired(), Length(max=500)])
    photo = FileField('Add photo', validators=[
                      DataRequired(), FileAllowed(['jpg', 'png'])])
    category = QuerySelectField('Select category', query_factory=lambda: Category.query.filter_by(
        user_id=current_user.id).all(), get_label='description')
    submit = SubmitField('SUBMIT')


class FilterNotesByCategory(FlaskForm):
    category = QuerySelectField('Select category', query_factory=lambda: Category.query.filter_by(
        user_id=current_user.id).all(), get_label='description')


class FilterNotesByName(FlaskForm):
    description = StringField('Enter name', [Length(max=100)])


# ******************************** Notes LIST *********************************


@app.route("/notes", methods=["GET", "POST"])
def notes():
    db.create_all()
    form = FilterNotesByCategory()
    form_name = FilterNotesByName()
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        categories = Category.query.filter_by(
            user_id=current_user.id).all()
        if form_name.description.data:
            description = form_name.description.data
            searching_name = Notes.query.filter_by(user_id=current_user.id).filter(
                Notes.description.like('%' + description + '%')).all()
        else:
            searching_name = 0

        if form.category.data:
            category = form.category.data
            notes = Notes.query.filter_by(
                user_id=current_user.id, category=category.description).paginate(page=page, per_page=3)
        else:
            notes = Notes.query.filter_by(
                user_id=current_user.id).paginate(page=page, per_page=3)
        return render_template("notes.html", form_name=form_name, form=form, searching_name=searching_name, notes=notes, categories=categories, user=current_user.user)
    else:
        return render_template("index.html")


@app.route("/add_notes", methods=["GET", "POST"])
def add_note():
    db.create_all()
    if current_user.is_authenticated:
        form = NoteForm()
        if request.method == 'POST' and form.validate_on_submit():
            if form.photo.data:
                photo = save_picture(form.photo.data)
            if form.category.data:
                category = form.category.data
            new_note = Notes(description=form.description.data, text=form.text.data, photo=photo, category=category.description,
                             user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            return redirect(url_for('notes'))
        picture = url_for('static', filename='/images/' + Notes.photo)
        return render_template("add_note.html", form=form, picture=picture)
    else:
        return render_template("index.html")


@app.route("/edit_note/<int:id>", methods=['GET', 'POST'])
def edit_note(id):
    if current_user.is_authenticated:
        try:
            get_category_user_id = Notes.query.filter_by(id=id).first()
            if current_user.id != get_category_user_id.user_id:
                return render_template("401.html")
            form = NoteForm()
            notes = Notes.query.get(id)
            if form.validate_on_submit():
                notes.photo = save_picture(form.photo.data)
                notes.description = form.description.data
                notes.text = form.text.data
                category = form.category.data
                notes.category = category.description
                db.session.commit()
                return redirect(url_for('notes'))
            return render_template("edit_note.html", form=form, notes=notes)
        except AttributeError:
            return render_template("404.html")
    else:
        return render_template("index.html")


@app.route("/delete_note/<int:id>")
def delete_note(id):
    if current_user.is_authenticated:
        try:
            get_note_user_id = Notes.query.filter_by(id=id).first()
            if current_user.id != get_note_user_id.user_id:
                return render_template("401.html")
            note = Notes.query.get(id)
            db.session.delete(note)
            db.session.commit()
            return redirect(url_for('notes'))
        except AttributeError:
            return render_template("404.html")
    else:
        return render_template("index.html")


# ********************************** ERRORS ***********************

@app.errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


# ******************************** RUN APP **********************

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    db.create_all()
