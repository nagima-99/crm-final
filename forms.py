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
    submit = SubmitField('Сохранить')

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
    submit = SubmitField('Зарегистрировать')

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
    submit = SubmitField('Зарегистрировать')


class CourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    academic_hours = IntegerField('Academic Hours', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    submit = SubmitField('Submit')

class GroupForm(FlaskForm):
    group_name = StringField('Название группы', validators=[DataRequired()])
    submit = SubmitField('Submit')