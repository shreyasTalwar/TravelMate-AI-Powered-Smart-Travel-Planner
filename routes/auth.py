import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from werkzeug.utils import secure_filename
from extensions import db, limiter
from models import User
from routes.forms import RegisterForm, LoginForm, ProfileForm
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to profile or dashboard
    if 'user_id' in session:
        return redirect(url_for('auth.profile'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip() if form.phone.data else None
        )
        user.set_password(form.password.data)
        
        # Determine if first user registered should be admin (convenient for setup)
        # Otherwise, default role is 'user'
        if User.query.count() == 0:
            user.role = 'admin'
            user.email_verified = True
            
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            current_app.logger.error(f"Registration Error: {str(e)}")
            
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"], error_message="Too many login attempts. Please try again in a minute.")
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.profile'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            session.clear()
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            # Use 'next' parameter if available
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page or url_for('auth.profile'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('explore'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    form = ProfileForm(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data.strip()
        user.phone = form.phone.data.strip() if form.phone.data else None
        
        # Handle profile image upload
        image_file = form.profile_image.data
        if image_file:
            # Ensure upload folder exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Secure and generate unique filename
            ext = secure_filename(image_file.filename).split('.')[-1]
            unique_filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                # Remove old profile picture if exists
                if user.profile_image:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_image)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                image_file.save(filepath)
                user.profile_image = unique_filename
            except Exception as e:
                flash('Failed to save profile image.', 'danger')
                current_app.logger.error(f"Upload Error: {str(e)}")
                
        try:
            db.session.commit()
            session['user_name'] = user.name  # Update session name
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'danger')
            current_app.logger.error(f"Profile Update Error: {str(e)}")
            
    return render_template('profile.html', form=form, user=user)

# Forgotten password reset flow stub
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        flash(f"If an account exists for {email}, a password reset link has been simulated.", "info")
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')

# Email verification stub
@auth_bp.route('/verify-email', methods=['GET'])
@login_required
def verify_email():
    user = User.query.get(session['user_id'])
    if user:
        user.email_verified = True
        db.session.commit()
        flash("Your email has been verified successfully (Simulation)!", "success")
    return redirect(url_for('auth.profile'))
