from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, DecimalField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp, NumberRange
from models import User

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Invalid email address format."),
        Length(max=120)
    ])
    phone = StringField('Phone Number', validators=[
        Length(max=20, message="Phone number must not exceed 20 characters."),
        Regexp(r'^\+?[0-9\s\-()]*$', message="Invalid phone number format.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Invalid email address format.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    submit = SubmitField('Log In')

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    phone = StringField('Phone Number', validators=[
        Length(max=20, message="Phone number must not exceed 20 characters."),
        Regexp(r'^\+?[0-9\s\-()]*$', message="Invalid phone number format.")
    ])
    profile_image = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only images (jpg, jpeg, png, gif) are allowed.')
    ])
    submit = SubmitField('Save Changes')

class TripForm(FlaskForm):
    destination = StringField('Destination', validators=[
        DataRequired(message="Destination is required."),
        Length(max=255, message="Destination name is too long.")
    ])
    budget = DecimalField('Budget (INR)', validators=[
        DataRequired(message="Budget is required."),
        NumberRange(min=0, message="Budget must be a positive number.")
    ])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[
        DataRequired(message="Start date is required.")
    ])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[
        DataRequired(message="End date is required.")
    ])
    travellers = IntegerField('Number of Travelers', default=1, validators=[
        DataRequired(message="Number of travelers is required."),
        NumberRange(min=1, message="Must have at least 1 traveler.")
    ])
    submit = SubmitField('Save Trip')

    def validate_end_date(self, end_date):
        if self.start_date.data and end_date.data:
            if end_date.data < self.start_date.data:
                raise ValidationError("End date cannot be earlier than start date.")

