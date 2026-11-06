from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    badge_number = StringField('Badge Number', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Length(max=30)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    station_id = SelectField('Station', coerce=int, validators=[Optional()])
    password = PasswordField('Password (leave empty to keep current)', validators=[Optional(), Length(min=6)])
    submit = SubmitField('Save User')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='New password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='New password and confirmation must match.')
    ])
    submit = SubmitField('Change Password')
