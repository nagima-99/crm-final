from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, IntegerField, FileField, SelectField
from wtforms.validators import Optional, DataRequired, Email, EqualTo, Regexp, ValidationError, Length, NumberRange
from models import db, Users

class AdministratorForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    patronymic = StringField('Отчество')
    birth_date = DateField('Дата рождения', format='%Y-%m-%d', validators=[Optional()])
    phone = StringField('Телефон', validators=[Optional(), Regexp(r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$',
            message="Введите номер телефона Казахстана в формате +7 (XXX) XXX-XX-XX")])
    address = StringField('Адрес', validators=[Optional()])
    photo = FileField('Фото')  # Добавляем поле для загрузки фото
    office_name = StringField('Название офиса', validators=[Optional()])
    office_address = StringField('Адрес офиса', validators=[Optional()])

class UpdateUserForm(FlaskForm):
    def validate_name_format(self, field):
        """Проверка, что поле содержит только буквы на русском языке с заглавной буквы."""
        if not field.data.istitle() or not all(c.isalpha() or c.isspace() for c in field.data):
            raise ValidationError("Поле должно содержать только буквы на русском языке с заглавной буквы.")
    
    def validate_new_password(self, field):
        """Проверка нового пароля (если он введен)."""
        if field.data and len(field.data) < 8:  # Если новый пароль введен
            raise ValidationError("Пароль должен быть не менее 8 символов.")
    
    def validate_confirm_password(self, field):
        """Проверка совпадения пароля (если новый пароль введен)."""
        if self.new_password.data:  # Если новый пароль введен
            if field.data != self.new_password.data:
                raise ValidationError("Пароли должны совпадать.")
        return True

    email = StringField(
        'Email',
        validators=[DataRequired(), Email(message="Введите корректный email.")],
    )
    first_name = StringField(
        'Имя',
        validators=[
            DataRequired(),
            Length(max=50, message="Имя не может быть длиннее 50 символов."),
            validate_name_format,  # Используем метод validate_name_format
        ],
    )
    surname = StringField(
        'Фамилия',
        validators=[
            DataRequired(),
            Length(max=50, message="Фамилия не может быть длиннее 50 символов."),
            validate_name_format,  # Используем метод validate_name_format
        ],
    )
    patronymic = StringField(
        'Отчество',
        validators=[Length(max=50, message="Отчество не может быть длиннее 50 символов.")],
    )
    birth_date = DateField(
        'Дата рождения',
        validators=[Optional()],
        format='%Y-%m-%d',
    )
    phone = StringField(
        'Телефон',
        validators=[DataRequired(), Regexp(r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$', message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX")],
    )
    address = StringField(
        'Адрес',
        validators=[Length(max=100, message="Адрес не может быть длиннее 100 символов.")],
    )
    office_name = StringField(
        'Название офиса',
        validators=[Length(max=100, message="Название офиса не может быть длиннее 100 символов.")],
    )
    office_address = StringField(
        'Адрес офиса',
        validators=[Length(max=100, message="Адрес офиса не может быть длиннее 100 символов.")],
    )

    # Новый пароль не обязателен
    new_password = PasswordField(
        'Новый пароль',
        validators=[validate_new_password]  # Используем метод validate_new_password
    )

    # Подтверждение пароля, но только если новый пароль введен
    confirm_password = PasswordField(
        'Подтверждение пароля',
        validators=[validate_confirm_password]  # Используем метод validate_confirm_password
    )

    current_password = PasswordField(
        'Текущий пароль',
        validators=[DataRequired()],
    )


class RegisterStudentForm(FlaskForm):
    def validate_email(self, field):
        """Проверка на уникальность email."""
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError("Этот email уже зарегистрирован в системе.")
    
    def validate_name_format(form, field):
        """Проверка, что ФИО введено на русском языке с заглавной буквы."""
        if not field.data.istitle() or not all(c.isalpha() or c.isspace() for c in field.data):
            raise ValidationError("Поле должно содержать только буквы на русском языке с заглавной буквы.")

    surname = StringField(
        'Фамилия',
        validators=[
            DataRequired(),
            Length(max=50, message="Фамилия не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    first_name = StringField(
        'Имя',
        validators=[
            DataRequired(),
            Length(max=50, message="Имя не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    patronymic = StringField(
        'Отчество',
        validators=[
            Length(max=50, message="Отчество не может быть длиннее 50 символов."),
        ],
    )
    photo = FileField('Фото')  # Добавляем поле для загрузки фото
    first_name = StringField(
        'Имя',
        validators=[
            DataRequired(),
            Length(max=50, message="Имя не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message="Введите корректный email."),
            validate_email,
        ],
    )
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired(),
            Length(min=8, message="Пароль должен быть не менее 8 символов."),
        ],
    )
    confirm_password = PasswordField(
        'Подтвердите пароль',
        validators=[
            DataRequired(),
            EqualTo('password', message="Пароли должны совпадать."),
        ],
    )
    birth_date = DateField(
        'Дата рождения',
        validators=[DataRequired()],
        format='%Y-%m-%d',
    )
    phone = StringField(
        'Телефон',
        validators=[
            DataRequired(),
            Regexp(
                r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$',
                message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX",
            ),
        ],
    )
    address = StringField(
        'Адрес',
        validators=[
            DataRequired(),
            Length(max=100, message="Адрес не может быть длиннее 100 символов."),
        ],
    )
    client_name = StringField(
        'Имя клиента (ФИО)',
        validators=[
            DataRequired(),
            validate_name_format,
            Length(max=100, message="ФИО клиента не может быть длиннее 100 символов."),
        ],
    )
    client_relation = SelectField(
        'Связь с учеником',
        choices=[
            ('мать', 'Мать'),
            ('отец', 'Отец'),
            ('опекун', 'Опекун'),
        ],
        validators=[DataRequired()],
    )
    client_phone = StringField(
        'Телефон клиента',
        validators=[
            DataRequired(),
            Regexp(
                r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$',
                message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX",
            ),
        ],
    )


class RegisterTeacherForm(FlaskForm):
    def validate_email(self, field):
        """Проверка на уникальность email."""
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError("Этот email уже зарегистрирован в системе.")
    
    def validate_name_format(form, field):
        """Проверка, что ФИО введено на русском языке с заглавной буквы."""
        if not field.data.istitle() or not all(c.isalpha() or c.isspace() for c in field.data):
            raise ValidationError("Поле должно содержать только буквы на русском языке с заглавной буквы.")

    surname = StringField(
        'Фамилия',
        validators=[
            DataRequired(),
            Length(max=50, message="Фамилия не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    photo = FileField('Фото')  # Добавляем поле для загрузки фото
    first_name = StringField(
        'Имя',
        validators=[
            DataRequired(),
            Length(max=50, message="Имя не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    patronymic = StringField(
        'Отчество',
        validators=[
            Length(max=50, message="Отчество не может быть длиннее 50 символов."),
        ],
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message="Введите корректный email."),
            validate_email,
        ],
    )
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired(),
            Length(min=8, message="Пароль должен быть не менее 8 символов."),
        ],
    )
    confirm_password = PasswordField(
        'Подтвердите пароль',
        validators=[
            DataRequired(),
            EqualTo('password', message="Пароли должны совпадать."),
        ],
    )
    birth_date = DateField(
        'Дата рождения',
        validators=[DataRequired()],
        format='%Y-%m-%d',
    )
    phone = StringField(
        'Телефон',
        validators=[
            DataRequired(),
            Regexp(
                r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$',
                message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX",
            ),
        ],
    )
    address = StringField(
        'Адрес',
        validators=[
            DataRequired(),
            Length(max=100, message="Адрес не может быть длиннее 100 символов."),
        ],
    )
    education = StringField(
        'Образование',
        validators=[
            DataRequired(),
            Length(max=100, message="Образование не может быть длиннее 100 символов."),
        ],
    )

class CourseForm(FlaskForm):
    course_name = StringField('Название курса', validators=[DataRequired()])
    academic_hours = IntegerField('Академические часы:', validators=[
        DataRequired(),
        NumberRange(min=0, message="Количество часов не может быть отрицательным")
    ])
    price = IntegerField('Абонемент', validators=[
        DataRequired(),
        NumberRange(min=0, message="Цена не может быть отрицательной")
    ])

class GroupForm(FlaskForm):
    group_name = StringField('Название группы', validators=[DataRequired()])

class UpdateTeacherForm(FlaskForm):
    def validate_name_format(self, field):
        """Проверка, что поле содержит только буквы на русском языке с заглавной буквы."""
        if not field.data.istitle() or not all(c.isalpha() or c.isspace() for c in field.data):
            raise ValidationError("Поле должно содержать только буквы на русском языке с заглавной буквы.")
    
    def validate_new_password(self, field):
        """Проверка нового пароля (если он введен)."""
        if field.data and len(field.data) < 8:  # Если новый пароль введен
            raise ValidationError("Пароль должен быть не менее 8 символов.")
    
    def validate_confirm_password(self, field):
        """Проверка совпадения пароля (если новый пароль введен)."""
        if self.new_password.data and field.data != self.new_password.data:
            raise ValidationError("Пароли должны совпадать.")

    email = StringField(
        'Email',
        validators=[DataRequired(), Email(message="Введите корректный email.")],
    )
    first_name = StringField(
        'Имя',
        validators=[
            DataRequired(),
            Length(max=50, message="Имя не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    surname = StringField(
        'Фамилия',
        validators=[
            DataRequired(),
            Length(max=50, message="Фамилия не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    patronymic = StringField(
        'Отчество',
        validators=[Length(max=50, message="Отчество не может быть длиннее 50 символов.")],
    )
    birth_date = DateField(
        'Дата рождения',
        validators=[DataRequired()],
        format='%Y-%m-%d',
    )
    phone = StringField(
        'Телефон',
        validators=[DataRequired(), Regexp(r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$', message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX")],
    )
    address = StringField(
        'Адрес',
        validators=[Length(max=255, message="Адрес не может быть длиннее 255 символов.")],
    )
    education = StringField(
        'Образование',
        validators=[Length(max=255, message="Образование не может быть длиннее 255 символов.")],
    )

    new_password = PasswordField(
        'Новый пароль',
        validators=[validate_new_password],
    )
    confirm_password = PasswordField(
        'Подтверждение пароля',
        validators=[validate_confirm_password],
    )
    current_password = PasswordField(
        'Текущий пароль',
        validators=[DataRequired()],
    )

class UpdateStudentForm(FlaskForm):
    def validate_name_format(self, field):
        """Проверка, что поле содержит только буквы на русском языке с заглавной буквы."""
        if not field.data.istitle() or not all(c.isalpha() or c.isspace() for c in field.data):
            raise ValidationError("Поле должно содержать только буквы на русском языке с заглавной буквы.")
    
    def validate_new_password(self, field):
        """Проверка нового пароля (если он введен)."""
        if field.data and len(field.data) < 8:  # Если новый пароль введен
            raise ValidationError("Пароль должен быть не менее 8 символов.")
    
    def validate_confirm_password(self, field):
        """Проверка совпадения пароля (если новый пароль введен)."""
        if self.new_password.data and field.data != self.new_password.data:
            raise ValidationError("Пароли должны совпадать.")

    email = StringField(
        'Email',
        validators=[DataRequired(), Email(message="Введите корректный email.")],
    )
    first_name = StringField(
        'Имя',
        validators=[
            DataRequired(),
            Length(max=50, message="Имя не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    surname = StringField(
        'Фамилия',
        validators=[
            DataRequired(),
            Length(max=50, message="Фамилия не может быть длиннее 50 символов."),
            validate_name_format,
        ],
    )
    patronymic = StringField(
        'Отчество',
        validators=[Length(max=50, message="Отчество не может быть длиннее 50 символов.")],
    )
    birth_date = DateField(
        'Дата рождения',
        validators=[DataRequired()],
        format='%Y-%m-%d',
    )
    phone = StringField(
        'Телефон',
        validators=[DataRequired(), Regexp(r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$', message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX")],
    )
    address = StringField(
        'Адрес',
        validators=[Length(max=255, message="Адрес не может быть длиннее 255 символов.")],
    )

    client_name = StringField(
        'Имя родителя/опекуна',
        validators=[Length(max=255, message="Имя родителя не может быть длиннее 255 символов.")],
    )
    client_relation = StringField(
        'Степень родства',
        validators=[Length(max=100, message="Степень родства не может быть длиннее 100 символов.")],
    )
    client_phone = StringField(
        'Телефон родителя/опекуна',
        validators=[Regexp(r'^\+7\s?\(\d{3}\)\s?\d{3}\d{2}\d{2}$', message="Введите номер телефона в формате +7 (XXX) XXX-XX-XX")],
    )

    new_password = PasswordField(
        'Новый пароль',
        validators=[validate_new_password],
    )
    confirm_password = PasswordField(
        'Подтверждение пароля',
        validators=[validate_confirm_password],
    )
    current_password = PasswordField(
        'Текущий пароль',
        validators=[DataRequired()],
    )
