import os
import json
import forms
from datetime import datetime
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, logout_user, login_user, login_required
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from enum import Enum
from sqlalchemy.orm import backref
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect

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
    description = db.Column("description", db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")


class Notes(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column("description", db.String, nullable=False)
    text = db.Column("text", db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=True, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", lazy=True)

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
        return render_template("index.html", user=current_user.user)
    else:
        return render_template("index.html")


# ******************************** Category LIST *********************************

@app.route("/categories")
def categories():
    db.create_all()
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        categories = Category.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=8)
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
        form = forms.CategoryForm()
        category = Category.query.get(id)
        if form.validate_on_submit():
            category.description = form.description.data
            db.session.commit()
            return redirect(url_for('categories'))
        return render_template("edit_category.html", form=form, category=category)
    else:
        return render_template("index.html")


@app.route("/delete_category/<int:id>")
def delete_category(id):
    if current_user.is_authenticated:
        category = Category.query.get(id)
        db.session.delete(category)
        db.session.commit()
        return redirect(url_for('categories'))
    else:
        return render_template("index.html")

# ******************************** Uzrasai LIST *********************************


@app.route("/notes")
def notes():
    db.create_all()
    if current_user.is_authenticated:
        notes = Notes.query.filter_by(user_id=current_user.id).all()
        return render_template("notes.html", notes=notes, user=current_user.user)
    else:
        return render_template("index.html")


@app.route("/add_notes", methods=["GET", "POST"])
def add_note():
    db.create_all()
    if current_user.is_authenticated:
        form = forms.NotesForm()
        if form.validate_on_submit():
            new_note = Notes(description=form.description.data, text=form.text.data,
                             user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            return redirect(url_for('notes'))
        return render_template("add_note.html", form=form)
    else:
        return render_template("index.html")

# @app.route("/products/edit/<int:id>", methods=['GET', 'POST'])
# @login_required
# def update_product(id):
#     form = forms.ProductForm()
#     product = Product.query.get(id)
#     if form.validate_on_submit():
#         product.description = form.description.data
#         product.price = form.price.data
#         product.quantity = form.quantity.data
#         product.unit = form.unit.data
#         db.session.commit()
#         return redirect(url_for('shopping_records'))
#     return render_template("update_product.html", form=form, product=product)


# @app.route("/product_status/<int:id>", methods=['GET', 'POST'])
# @login_required
# def product_status(id):
#     form = forms.StatusProductForm()
#     product = Product.query.get(id)
#     if form.validate_on_submit():
#         product.status = form.status.data
#         db.session.commit()
#         return redirect(url_for('shopping_records'))
#     return render_template("products.html", form=form, product=product)


# @app.route("/products/delete/<int:id>")
# @login_required
# def delete_product(id):
#     product_event = Product.query.get(id)
#     db.session.delete(product_event)
#     db.session.commit()
#     return redirect(url_for('shopping_records'))


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
