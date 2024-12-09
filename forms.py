from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField, IntegerField
from wtforms.validators import Optional, DataRequired, Email, EqualTo, Regexp

class AdministratorForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    phone = StringField('Телефон', validators=[Optional()])
    address = StringField('Адрес', validators=[Optional()])
    office_name = StringField('Название офиса', validators=[Optional()])
    office_address = StringField('Адрес офиса', validators=[Optional()])

class RegisterStudentForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    birth_date = DateField('Дата рождения', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[
        DataRequired(),
        Regexp(r'^\+?[0-9\s\-\(\)]*$', message="Некорректный формат телефона")
    ])
    address = StringField('Адрес', validators=[DataRequired()])
    client_name = StringField('Имя клиента', validators=[DataRequired()])
    client_relation = StringField('Связь с клиентом', validators=[DataRequired()])
    client_phone = StringField('Телефон клиента', validators=[
        DataRequired(),
        Regexp(r'^\+?[0-9\s\-\(\)]*$', message="Некорректный формат телефона")
    ])
    client_workplace = StringField('Место работы клиента')
    client_position = StringField('Должность клиента')

class RegisterTeacherForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    birth_date = DateField('Дата рождения', format='%Y-%m-%d', validators=[DataRequired()])
    phone = StringField('Телефон', validators=[
        DataRequired(),
        Regexp(r'^\+?[0-9\s\-\(\)]*$', message="Некорректный формат телефона")
    ])
    address = StringField('Адрес', validators=[DataRequired()])
    education = StringField('Образование', validators=[DataRequired()])


class CourseForm(FlaskForm):
    course_name = StringField('Название курса', validators=[DataRequired()])
    academic_hours = IntegerField('Академические часы:', validators=[DataRequired()])
    price = IntegerField('Абонемент', validators=[DataRequired()])

class GroupForm(FlaskForm):
    group_name = StringField('Название группы', validators=[DataRequired()])
