from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    address = TextAreaField('Address', validators=[DataRequired()])
    
    bank_name = StringField('Bank Name')
    account_holder_name = StringField('Account Holder Name')
    account_number = StringField('Account Number')
    ifsc_code = StringField('IFSC Code')
    
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[('electronics', 'Electronics'), ('vehicles', 'Vehicles'), ('tools', 'Tools'), ('party', 'Party Supplies'), ('other', 'Other')], validators=[DataRequired()])
    rental_price = FloatField('Rental Price (per day)', validators=[DataRequired()])
    image = FileField('Item Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    is_available = BooleanField('Available for Rent', default=True)
    submit = SubmitField('Post Item')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class EditBankDetailsForm(FlaskForm):
    bank_name = StringField('Bank Name')
    account_holder_name = StringField('Account Holder Name')
    account_number = StringField('Account Number')
    ifsc_code = StringField('IFSC Code')
    submit = SubmitField('Update Bank Details')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[('5', '5 Stars'), ('4', '4 Stars'), ('3', '3 Stars'), ('2', '2 Stars'), ('1', '1 Star')], validators=[DataRequired()])
    comment = TextAreaField('Review Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Review')
