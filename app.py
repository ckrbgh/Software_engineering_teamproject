from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, PhotoUploadForm, MessageForm
from models import db, User, Photo, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # Simulate always logged in user (replace with actual logic as needed)
    return User.query.get(1)  # Assuming user with ID 1 is always "logged in"

@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/user_list")
def user_list():
    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route("/photos")
@login_required
def photos():
    photos = Photo.query.all()
    return render_template('photo_list.html', photos=photos)

@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    form = PhotoUploadForm()
    if form.validate_on_submit():
        photo = Photo(description=form.description.data, keywords=form.keywords.data, image_file='some_image.jpg', user_id=current_user.id)
        db.session.add(photo)
        db.session.commit()
        flash('Your photo has been uploaded!', 'success')
        return redirect(url_for('photos'))
    return render_template('upload.html', title='Upload Photo', form=form)

@app.route("/search")
def search():
    keyword = request.args.get('keyword')
    photos = Photo.query.filter(Photo.keywords.contains(keyword)).all()
    return render_template('photo_list.html', photos=photos)

@app.route("/messages", methods=['GET', 'POST'])
@login_required
def messages():
    messages = Message.query.filter_by(recipient_id=current_user.id).all()
    return render_template('messages.html', messages=messages)

@app.route("/message/<int:photo_id>", methods=['GET', 'POST'])
@login_required
def message(photo_id):
    form = MessageForm()
    photo = Photo.query.get_or_404(photo_id)
    if form.validate_on_submit():
        message = Message(content=form.content.data, sender_id=current_user.id, recipient_id=photo.user_id)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been sent!', 'success')
        return redirect(url_for('photos'))
    return render_template('send_message.html', title='Send Message', form=form, photo=photo)

@app.route("/reply/<int:message_id>", methods=['GET', 'POST'])
@login_required
def reply(message_id):
    form = MessageForm()
    original_message = Message.query.get_or_404(message_id)
    if form.validate_on_submit():
        reply_message = Message(
            content=form.content.data,
            sender_id=current_user.id,
            recipient_id=original_message.sender_id  # Reply to the original sender
        )
        db.session.add(reply_message)
        db.session.commit()
        flash('Your reply has been sent!', 'success')
        return redirect(url_for('messages'))
    return render_template('reply.html', title='Reply Message', form=form, original_message=original_message)

@app.route("/delete_message/<int:message_id>", methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.recipient_id != current_user.id:
        abort(403)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully', 'success')
    return redirect(url_for('messages'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
