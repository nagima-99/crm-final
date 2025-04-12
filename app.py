from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from forms import AdministratorForm, UpdateUserForm, RegisterStudentForm, RegisterTeacherForm, CourseForm, GroupForm, UpdateTeacherForm, UpdateStudentForm
from models import db, Users, Administrator, Teacher, Student, Course, Group, ManageStudent, Schedule, Attendance, Payment, Message, Salary
from functools import wraps
import logging
import pusher
from sqlalchemy import func


# Инициализация приложения
app = Flask(__name__)

# Инициализация Pusher
pusher_client = pusher.Pusher(
    app_id="1942827",
    key="625c8111a341758cd1e0",
    secret="7d1fb0e8b5fcbcb0acd1",
    cluster="eu",
    ssl=True
)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем лишние предупреждения
app.config['SECRET_KEY'] = '7d1fb0e8b5fcbcb0acd1'  # Для защиты форм
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


# Инициализация базы данных
db.init_app(app)

# Инициализация логина
login_manager = LoginManager(app)
login_manager.login_view = 'login'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Миграции
from flask_migrate import Migrate
migrate = Migrate(app, db)

# Загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Вспомогательная функция для вычисления возраста
def calculate_age(birth_date):
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

# Декоратор для проверки роли
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Недостаточно прав доступа', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Главная страница
@app.route('/')
def index():
    return redirect(url_for('login'))

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Добро пожаловать!', 'success')
            if user.role == 'Администратор':
                return redirect(url_for('administrator_dashboard', id=user.id))
            elif user.role == 'Учитель':
                return redirect(url_for('teacher_dashboard', id=user.id))
            elif user.role == 'Студент':
                return redirect(url_for('student_dashboard', id=user.id))
        else:
            flash('Неправильное имя пользователя или пароль', 'danger')

    return render_template('login.html')

# Страница администрирования
@app.route('/administrator/<int:id>', methods=['GET'])
@login_required
@role_required('Администратор')
def administrator_dashboard(id):
    form = AdministratorForm()  # Создаем экземпляр формы

    # Получение данных администратора
    administrator = Administrator.query.filter_by(admin_id=id).first()
    if not administrator:
        flash('Администратор не найден!', 'danger')
        return redirect(url_for('login'))

    # Получение данных пользователя
    user = Users.query.get_or_404(administrator.admin_id)

    # Вычисление возраста
    age = calculate_age(administrator.birth_date)
    # Обработка фото
    if form.photo.data:
        photo = form.photo.data
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        user.photo = filename
    else:
        # Если фото не было загружено, оставить дефолтное
        if not user.photo:
            user.photo = 'default.png'
    # Рендеринг страницы профиля
    return render_template(
        'administrator_dashboard.html',
        administrator=administrator,
        user=user,
        age=age,
        form=form
    )

@app.route('/student/<int:id>', methods=['GET'])
@login_required
@role_required('Студент')
def student_dashboard(id):
    print(f"ID из URL: {id}")
    form = RegisterStudentForm()

    # Получение данных студента
    student = Student.query.filter_by(student_id=id).first()
    courses = Course.query.join(ManageStudent).filter(ManageStudent.student_id == id).distinct().all()
    

    if not student:
        print(f"ID из URL: {id}, ID студента: {student}")

        flash('Студент не найден!', 'danger')
        return redirect(url_for('login')) 

    # Получение данных пользователя
    user = Users.query.get_or_404(student.student_id)

    # Вычисление возраста
    age = calculate_age(student.birth_date)

    # Обработка фото
    if form.photo.data:
        photo = form.photo.data
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        user.photo = filename
    else:
        # Если фото не было загружено, оставить дефолтное
        if not user.photo:
            user.photo = 'default.png'
    print(f"Передача student в шаблон: {student}")

    # Рендеринг страницы профиля студента
    return render_template(
        'student_dashboard.html',
        student=student,
        user=user,
        age=age,
        courses=courses,
        form=form
    )


@app.route('/teacher/<int:id>', methods=['GET'])
@login_required
@role_required('Учитель')
def teacher_dashboard(id):
    print(f"ID из URL: {id}")
    form = RegisterTeacherForm()

    # Получение данных учителя
    teacher = Teacher.query.filter_by(teacher_id=id).first()
    courses = Course.query.join(Schedule).filter(Schedule.teacher_id == id).distinct().all()
    if not teacher:
        print(f"ID из URL: {id}, ID учителя: {teacher}")

        flash('Учитель не найден!', 'danger')
        return redirect(url_for('login')) 

    # Получение данных пользователя
    user = Users.query.get_or_404(teacher.teacher_id)

    # Вычисление возраста
    age = calculate_age(teacher.birth_date)

    # Обработка фото
    if form.photo.data:
        photo = form.photo.data
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        user.photo = filename
    else:
        # Если фото не было загружено, оставить дефолтное
        if not user.photo:
            user.photo = 'default.png'

    # Рендеринг страницы профиля учителя
    return render_template(
        'teacher_dashboard.html',
        teacher=teacher,
        user=user,
        age=age,
        courses=courses,
        form=form
    )


@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def update_user(id):
    administrator = Administrator.query.get_or_404(id)  # Получаем администратора по ID
    user = Users.query.get_or_404(administrator.admin_id)  # Получаем пользователя
    form = UpdateUserForm()  # Создаем экземпляр формы

    # Преобразуем дату в datetime перед передачей в форму (если дата существует)
    if administrator.birth_date:
        form.birth_date.data = administrator.birth_date

    if form.validate_on_submit():
        try:
            # Проверка текущего пароля
            if not user.check_password(form.current_password.data):
                flash('Неправильный текущий пароль', 'danger')
                return redirect(url_for('update_user', id=user.id))
            
            # Обновляем данные пользователя
            user.email = form.email.data
            administrator.first_name = form.first_name.data
            administrator.surname = form.surname.data
            administrator.patronymic = form.patronymic.data
            
            # Преобразуем строку в объект date
            # Преобразуем строку в объект date
            if form.birth_date.data:
                print(f"Полученная дата из формы: {form.birth_date.data}")  # Отладка

                if isinstance(form.birth_date.data, str):  # Преобразуем строку в дату
                    administrator.birth_date = datetime.strptime(form.birth_date.data, "%Y-%m-%d").date()
                else:
                    administrator.birth_date = form.birth_date.data

                print(f"Полученная дата из формы: {form.birth_date.data} (тип: {type(form.birth_date.data)})")
                print(f"Дата перед коммитом: {administrator.birth_date} (тип: {type(administrator.birth_date)})")
  # Проверка перед сохранением
            else:
                print("Дата рождения не передана!")
            

            administrator.phone = form.phone.data
            administrator.address = form.address.data
            administrator.office_name = form.office_name.data
            administrator.office_address = form.office_address.data

            # Обновляем пароль, если он был изменен
            if form.new_password.data:
                user.set_password(form.new_password.data)

            db.session.commit()
            flash('Данные успешно обновлены!', 'success')
            return redirect(url_for('administrator_dashboard', id=administrator.admin_id))
        
        except Exception as e:
            db.session.rollback()  # Откатываем изменения при ошибке
            logger.error(f'Ошибка при обновлении данных пользователя: {e}')
            flash('Произошла ошибка при обновлении данных. Повторите попытку.', 'danger')
    
    # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    
    # Заполняем форму текущими данными
    form.email.data = user.email
    form.first_name.data = administrator.first_name
    form.surname.data = administrator.surname
    form.patronymic.data = administrator.patronymic
    form.birth_date.data = administrator.birth_date
    form.phone.data = administrator.phone
    form.address.data = administrator.address
    form.office_name.data = administrator.office_name
    form.office_address.data = administrator.office_address
    print(f"Дата, переданная в шаблон: {administrator.birth_date}")
    return render_template('update_user.html', form=form, administrator=administrator, user=user)

@app.route('/update_student/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Студент')
def update_student(id):
    user = Users.query.get_or_404(id)  # Получаем пользователя по ID
    student = Student.query.filter_by(student_id=user.id).first_or_404()  # Получаем данные студента
    form = UpdateStudentForm()

    # Заполняем форму текущими значениями, если студент уже есть
    if student.birth_date:
        form.birth_date.data = student.birth_date

    if form.validate_on_submit():
        try:
            # Проверка текущего пароля
            if not user.check_password(form.current_password.data):
                flash('Неправильный текущий пароль', 'danger')
                return redirect(url_for('update_student', id=user.id))

            # Обновляем данные пользователя
            user.email = form.email.data
            student.first_name = form.first_name.data
            student.surname = form.surname.data
            student.patronymic = form.patronymic.data

            # Преобразуем строку в объект date
            if form.birth_date.data:
                student.birth_date = form.birth_date.data  

            student.phone = form.phone.data
            student.address = form.address.data
            student.client_name = form.client_name.data
            student.client_relation = form.client_relation.data
            student.client_phone = form.client_phone.data

            # Обновляем пароль, если он был изменен
            if form.new_password.data:
                user.set_password(form.new_password.data)
            db.session.commit()
            flash('Данные успешно обновлены!', 'success')
            return redirect(url_for('student_dashboard', id=user.id))  # Редирект на профиль студента

        except Exception as e:
            db.session.rollback()
            logger.error(f'Ошибка при обновлении данных студента: {e}')
            flash('Произошла ошибка при обновлении данных. Повторите попытку.', 'danger')

    # Обработка ошибок формы
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")

    # Заполняем форму текущими значениями
    form.email.data = user.email
    form.first_name.data = student.first_name
    form.surname.data = student.surname
    form.patronymic.data = student.patronymic
    form.birth_date.data = student.birth_date
    form.phone.data = student.phone
    form.address.data = student.address
    form.client_name.data = student.client_name
    form.client_relation.data = student.client_relation
    form.client_phone.data = student.client_phone

    return render_template('update_student.html', form=form, student=student, user=user)


@app.route('/update_teacher/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Учитель')
def update_teacher(id):
    user = Users.query.get_or_404(id)  # Получаем пользователя по ID
    teacher = Teacher.query.filter_by(teacher_id=user.id).first_or_404()  # Находим учителя
    form = UpdateTeacherForm()

    # Преобразуем дату в datetime перед передачей в форму (если дата существует)
    if teacher.birth_date:
        form.birth_date.data = teacher.birth_date

    if form.validate_on_submit():
        try:
            # Проверка текущего пароля
            if not user.check_password(form.current_password.data):
                flash('Неправильный текущий пароль', 'danger')
                return redirect(url_for('update_teacher', id=user.id))  # Исправленный редирект

            # Обновляем данные пользователя
            user.email = form.email.data
            teacher.first_name = form.first_name.data
            teacher.surname = form.surname.data
            teacher.patronymic = form.patronymic.data

            # Преобразуем строку в объект date
            if form.birth_date.data:
                teacher.birth_date = form.birth_date.data  

            teacher.phone = form.phone.data
            teacher.address = form.address.data
            teacher.education = form.education.data

            # Обновляем пароль, если он был изменен
            if form.new_password.data:
                user.set_password(form.new_password.data)

            db.session.commit()
            flash('Данные успешно обновлены!', 'success')
            return redirect(url_for('teacher_dashboard', id=user.id))  # Редирект по user.id

        except Exception as e:
            db.session.rollback()
            logger.error(f'Ошибка при обновлении данных учителя: {e}')
            flash('Произошла ошибка при обновлении данных. Повторите попытку.', 'danger')

    # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")

    # Заполняем форму текущими данными
    form.email.data = user.email
    form.first_name.data = teacher.first_name
    form.surname.data = teacher.surname
    form.patronymic.data = teacher.patronymic
    form.birth_date.data = teacher.birth_date
    form.phone.data = teacher.phone
    form.address.data = teacher.address
    form.education.data = teacher.education

    return render_template('update_teacher.html', form=form, teacher=teacher, user=user)


@app.route('/upload_photo/<int:id>', methods=['POST'])
@login_required
def upload_photo(id):
    user = Users.query.get_or_404(id)  # Получаем пользователя

    if 'photo' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(request.referrer)

    file = request.files['photo']
    if file.filename == '':
        flash('Нет выбранного файла', 'danger')
        return redirect(request.referrer)

    if file:
        # Проверяем, если старое фото существует, то удаляем его
        old_photo = user.photo
        if old_photo and old_photo != 'default.png':  # Не удаляем default.png
            try:
                old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_photo)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)  # Удаляем старое фото
            except Exception as e:
                print(f"Ошибка при удалении старого фото: {e}")

        # Сохраняем новое фото
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Обновляем поле photo в базе данных
        user.photo = filename
        db.session.commit()

        flash('Фото успешно загружено', 'success')
        return redirect(request.referrer)  # Перенаправляем на страницу, с которой был отправлен запрос


@app.route('/delete_photo/<int:id>', methods=['POST'])
@login_required
@role_required('Администратор', 'Учитель', 'Студент')
def delete_photo(id):
    user = Users.query.get_or_404(id)

    if user.photo:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], user.photo))
            user.photo = None
            db.session.commit()
            flash('Фото успешно удалено!', 'success')
        except Exception as e:
            flash(f'Ошибка при удалении фотографии: {e}', 'danger')
    # Перенаправляем пользователя на его панель
    if user.role == 'Администратор':
        return redirect(url_for('administrator_dashboard', id=id))
    elif user.role == 'Учитель':
        return redirect(url_for('teacher_dashboard', id=id))
    elif user.role == 'Студент':
        return redirect(url_for('student_dashboard', id=id))

    # Если роль неизвестна, отправляем на главную
    return redirect(url_for('login'))


# Cписок учеников
@app.route('/students', methods=['GET'])
@login_required
@role_required('Администратор')
def students_list():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    students = Student.query.all()

    # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 8  # Количество учеников на одной странице

    # Пагинация
    pagination = Student.query.paginate(page=page, per_page=per_page)
    students = pagination.items  # Ученики текущей страницы

    student_ages = {student.id: calculate_age(student.birth_date) for student in students}

    return render_template('students_list.html', students=students, administrator=administrator, student_ages=student_ages, pagination=pagination)


@app.route('/delete_student/<int:id>', methods=['GET'])
@login_required
@role_required('Администратор')
def delete_student(id):
    # Ищем студента по ID
    student = Student.query.get(id)
    if not student:
        flash("Студент не найден!", 'danger')
        return redirect(url_for('students_list'))

    # Удаляем связанного пользователя
    user = student.user  # Получаем связанного пользователя
    if user:
        db.session.delete(user)  # Удаляем пользователя из таблицы Users
    
    db.session.delete(student)  # Удаляем студента из таблицы Student
    db.session.commit()  # Подтверждаем изменения в базе данных

    flash("Студент и пользователь успешно удалены!", 'success')
    return redirect(url_for('students_list'))


# Cписок учителей
@app.route('/teachers', methods=['GET'])
@login_required
@role_required('Администратор')
def teachers_list():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    teachers = Teacher.query.all()

    # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Количество учеников на одной странице

    # Пагинация
    pagination = Teacher.query.paginate(page=page, per_page=per_page)
    teachers = pagination.items  # Ученики текущей страницы

    teacher_ages = {teacher.id: calculate_age(teacher.birth_date) for teacher in teachers}

    return render_template('teachers_list.html', teachers=teachers, administrator=administrator, teacher_ages=teacher_ages, pagination=pagination)


@app.route('/delete_teacher/<int:id>', methods=['GET'])
@login_required
@role_required('Администратор')
def delete_teacher(id):
    teacher = Teacher.query.get(id)
    if not teacher:
        flash("Преподаватель не найден!", 'danger')
        return redirect(url_for('teachers_list'))

    user = teacher.user  # Связанный пользователь
    if user:
        db.session.delete(user)

    db.session.delete(teacher)
    db.session.commit()

    flash("Преподаватель успешно удалены!", 'success')
    return redirect(url_for('teachers_list'))



# Регистрация ученика
@app.route('/register_student', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def register_student():
    form = RegisterStudentForm()
    
    # Получаем текущего администратора
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    if not administrator:
        flash('Администратор не найден!', 'danger')
        return redirect(url_for('login'))
    
    if form.validate_on_submit():
        try:
            # Создаем пользователя в таблице Users
            user = Users(
                email=form.email.data,
                role='Студент'
            )
            user.set_password(form.password.data)  # Хэшируем пароль
            db.session.add(user)
            db.session.commit()  # Сохраняем пользователя, чтобы получить user.id
            # Сохраняем данные в базу
            student = Student(
                student_id=user.id,
                surname=form.surname.data,
                first_name=form.first_name.data,
                patronymic=form.patronymic.data,
                birth_date=form.birth_date.data,
                phone=form.phone.data,
                address=form.address.data,
                client_name=form.client_name.data,
                client_relation=form.client_relation.data,
                client_phone=form.client_phone.data,
            )
            db.session.add(student)
            db.session.commit()  # Сохраняем данные в таблицу Teacher

            flash("Ученик успешно зарегистрирован!", "success")
            return redirect(url_for('students_list', id=current_user.id))
        
        except Exception as e:
            db.session.rollback()  # Откатываем изменения при ошибке
            logger.error(f'Ошибка при добавлении ученика: {e}')
            flash("Произошла ошибка при добавлении ученика. Повторите попытку.", "danger")
    # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    
    return render_template('register_student.html', form=form, administrator=administrator)

@app.route('/register_teacher', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def register_teacher():
    form = RegisterTeacherForm()
    
    # Получаем текущего администратора (текущий пользователь)
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    if not administrator:
        flash('Администратор не найден!', 'danger')
        return redirect(url_for('login'))
    
    if form.validate_on_submit():
        try:
            # Создаем пользователя в таблице Users
            user = Users(
                email=form.email.data,
                role='Учитель'
            )
            user.set_password(form.password.data)  # Хэшируем пароль
            db.session.add(user)
            db.session.commit()  # Сохраняем пользователя, чтобы получить user.id
            # Создаем запись в таблице Teacher
            teacher = Teacher(
                teacher_id=user.id,  # Используем ID только что созданного пользователя
                surname=form.surname.data,
                first_name=form.first_name.data,
                patronymic=form.patronymic.data,
                birth_date=form.birth_date.data,
                phone=form.phone.data,
                address=form.address.data,
                education=form.education.data
            )

            db.session.add(teacher)
            db.session.commit()  # Сохраняем данные в таблицу Teacher

            flash('Преподаватель успешно зарегистрирован!', 'success')
            return redirect(url_for('teachers_list', id=current_user.id))
        
        except Exception as e:
            db.session.rollback()  # Откатываем изменения при ошибке
            logger.error(f'Ошибка при добавлении учителя: {e}')
            flash("Произошла ошибка при добавлении учителя. Повторите попытку.", "danger")
    # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    
    return render_template('register_teacher.html', form=form, administrator=administrator)


@app.route('/add_course', methods=['POST'])
def add_course():
    data = request.get_json()
    course_name = data.get('course_name')
    academic_hours = data.get('academic_hours')
    price = data.get('price')

    # Проверка на отрицательные значения
    if academic_hours is not None and int(academic_hours) < 0:
        return jsonify({"success": False, "message": "Академические часы не могут быть отрицательными"})
    if price is not None and int(price) < 0:
        return jsonify({"success": False, "message": "Цена не может быть отрицательной"}) 

    # Пример проверки на существование курса
    existing_course = Course.query.filter_by(course_name=course_name).first()
    if existing_course:
        return jsonify({"success": False, "message": "Курс уже существует"})
    
    # Если курс не существует, сохраняем его
    new_course = Course(course_name=course_name, academic_hours=data['academic_hours'], price=data['price'])
    db.session.add(new_course)
    db.session.commit()

    flash("Курс успешно добавлен!", "success")
    return jsonify({"success": True, "message": "Курс успешно добавлен"})

# Редактировать курс
@app.route('/edit_course/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def edit_course(id):
    # Получаем администратора, связанного с текущим пользователем
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    # Получаем курс из базы данных
    course = Course.query.get_or_404(id)
    # Заполняем форму данными из курса 
    form = CourseForm(obj=course)

    if form.validate_on_submit():
        try:
            # Проверка на уникальность названия курса
            existing_course = Course.query.filter_by(course_name=form.course_name.data).first()
            
            # Если курс с таким названием уже существует, но это не тот же курс
            if existing_course and existing_course.id != course.id:
                flash("Курс с таким названием уже существует. Пожалуйста, выберите другое название.", "danger")
            else:
                # Обновляем данные курса
                course.course_name = form.course_name.data
                course.academic_hours = form.academic_hours.data
                course.price = form.price.data
                db.session.commit()  # Сохраняем изменения в базе данных
                
                # Отправляем сообщение об успешном изменении
                flash("Курс успешно обновлен!", "success")
                return redirect(url_for('list_courses'))
        except Exception as e:
            db.session.rollback()  # Откатываем изменения в случае ошибки
            flash("Произошла ошибка при изменении курса. Повторите попытку.", "danger")
        # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    # Отображаем шаблон с формой и курсом
    return render_template('edit_course.html', form=form, course=course, administrator=administrator)

@app.route('/delete_course/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def delete_course(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('list_courses'))


# Просмотр всех курсов
@app.route('/courses', methods=['GET'])
@login_required
@role_required('Администратор')
def list_courses():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    courses = Course.query.all()
    # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 8  # Количество учеников на одной странице

    # Пагинация
    pagination = Course.query.paginate(page=page, per_page=per_page)
    courses = pagination.items  # Ученики текущей страницы
    return render_template('courses.html', courses=courses, administrator=administrator, pagination=pagination)


# Добавить новую группу
@app.route('/add_group', methods=['POST'])
@login_required
@role_required('Администратор')
def add_group():
    form = GroupForm()  # Пример формы, которую нужно создать
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()

    if form.validate_on_submit():
        try:
            existing_group = Group.query.filter_by(group_name=form.group_name.data).first()
            if existing_group:
                return jsonify({"success": False, "message": "Группа уже существует"})
            else:
                group = Group(group_name=form.group_name.data)  
                db.session.add(group)
                db.session.commit()
                flash("Группа успешно добавлена!", "success")
                return jsonify({"success": True, "message": "Группа успешно добавлена"})
        except Exception as e:
            db.session.rollback()
            flash("Произошла ошибка при добавлении группы. Повторите попытку.", "danger")
            return jsonify({"success": False, "message": "Произошла ошибка"})
    # Обработка ошибок формы (если есть)
    return jsonify({"success": False, "message": "Ошибка валидации формы"})


# Редактировать группу
@app.route('/edit_group/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def edit_group(id):
    group = Group.query.get_or_404(id)
    form = GroupForm(obj=group)
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()  # Извлекаем объект администратора

    if form.validate_on_submit():
        try:
            existing_group = Group.query.filter_by(group_name=form.group_name.data).first()
            if existing_group and existing_group.id != group.id:
                flash("Группа с таким названием уже существует. Пожалуйста, выберите другое название.", "danger")
            else:
                group.group_name = form.group_name.data
                db.session.commit()
                flash("Группа успешно обновлена!", "success")
                return redirect(url_for('list_groups'))
        except Exception as e:
            db.session.rollback()  # Откатываем изменения в случае ошибки
            flash("Произошла ошибка при изменении группы. Повторите попытку.", "danger")
        # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    # Отображаем шаблон с формой и курсом
    return render_template('edit_group.html', form=form, group=group, administrator=administrator)

@app.route('/delete_group/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def delete_group(id):
    group = Group.query.get_or_404(id)
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('list_groups'))

# Просмотр всех групп
@app.route('/groups', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def list_groups():
    form = GroupForm()  # Пример формы, которую нужно создать

    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    groups = Group.query.all()

    if form.validate_on_submit():
        # Если форма отправлена и прошла валидацию, добавляем новую группу
        group_name = form.group_name.data
        existing_group = Group.query.filter_by(group_name=group_name).first()

        if existing_group:
            flash("Группа с таким названием уже существует!", "danger")
        else:
            new_group = Group(group_name=group_name)
            db.session.add(new_group)
            db.session.commit()
            flash("Группа успешно добавлена!", "success")

        return redirect(url_for('list_groups'))

    # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 8 

    # Пагинация
    pagination = Group.query.paginate(page=page, per_page=per_page)
    groups = pagination.items 

    return render_template('groups.html', form=form, groups=groups, administrator=administrator, pagination=pagination)

@app.route('/management', methods=['GET'])
@login_required
@role_required('Администратор', 'Студент')
def management():
    user = current_user
    courses = Course.query.all()
    groups = Group.query.all()
    student_info = []

    if user.role == 'Студент':
        base_template = "base_student.html"
        student = Student.query.filter_by(student_id=user.id).first()
        if student:
            payments = Payment.query.filter_by(student_id=student.student_id).order_by(Payment.payment_date.desc()).all()

            manage_student_entry = ManageStudent.query.filter_by(student_id=student.student_id).first()
            course = Course.query.get(manage_student_entry.course_id) if manage_student_entry else None
            group = Group.query.get(manage_student_entry.group_id) if manage_student_entry else None

            total_paid = db.session.query(db.func.sum(Payment.amount)).filter_by(student_id=student.student_id).scalar() or 0
            total_attended = Attendance.query.filter_by(student_id=student.student_id, attended=True).count()

            price_per_lesson = (course.price / course.academic_hours) if course else 0
            balance = total_paid - (total_attended * price_per_lesson)
            payment_status = "Оплачено" if balance > 0 else "Не оплачено"
            # Пагинация платежей для студента
            page = request.args.get('page', 1, type=int)
            per_page = 5  # Сколько платежей на страницу
            payments_paginated = Payment.query.filter_by(student_id=student.student_id)\
                                            .order_by(Payment.payment_date.desc())\
                                            .paginate(page=page, per_page=per_page)

            student_info.append({
                'student': student,
                'course': course,
                'group': group,
                'balance': balance,
                'payment_status': payment_status,
                'payments': payments,
            })

        return render_template(
            'management.html',
            student_info=student_info,
            courses=courses,
            groups=groups,
            base_template=base_template,
            payments_paginated=payments_paginated,
            student=student
        )

    # Админская часть
    base_template = "base_administrator.html"
    administrator = Administrator.query.filter_by(admin_id=user.id).first()
    page = request.args.get('page', 1, type=int)
    per_page = 6
    student_pagination = Student.query.paginate(page=page, per_page=per_page)
    students = student_pagination.items

    for student in students:
        manage_student_entry = ManageStudent.query.filter_by(student_id=student.student_id).first()
        course = Course.query.get(manage_student_entry.course_id) if manage_student_entry else None
        group = Group.query.get(manage_student_entry.group_id) if manage_student_entry else None

        total_paid = db.session.query(db.func.sum(Payment.amount)).filter_by(student_id=student.student_id).scalar() or 0
        total_attended = Attendance.query.filter_by(student_id=student.student_id, attended=True).count()

        price_per_lesson = (course.price / course.academic_hours) if course else 0
        balance = total_paid - (total_attended * price_per_lesson)
        payment_status = "Оплачено" if balance > 0 else "Не оплачено"

        student_info.append({
            'student': student,
            'course': course,
            'group': group,
            'balance': balance,
            'payment_status': payment_status
        })

    return render_template(
        'management.html',
        administrator=administrator,
        student_info=student_info,
        courses=courses,
        groups=groups,
        student_pagination=student_pagination,
        base_template=base_template
    )



@app.route('/edit_management/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def edit_management(id):
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    student = Student.query.filter_by(student_id=id).first_or_404()
    courses = Course.query.all()
    groups = Group.query.all()

    # Получаем существующие данные о студенте
    manage_student = ManageStudent.query.filter_by(student_id=student.student_id).first()
    current_course_id = manage_student.course_id if manage_student else None
    current_group_id = manage_student.group_id if manage_student else None
    course_prices = {course.id: course.price for course in courses}

    # Получаем курс ученика
    course = Course.query.get(current_course_id) if current_course_id else None
    price_per_lesson = (course.price / course.academic_hours) if course else 0

    # Считаем баланс
    total_paid = db.session.query(db.func.sum(Payment.amount)).filter_by(student_id=student.student_id).scalar() or 0
    total_attended = Attendance.query.filter_by(student_id=student.student_id, attended=True).count()

    balance = total_paid - (total_attended * price_per_lesson)

    if request.method == 'POST':
        course_id = int(request.form.get('course_id'))
        group_id = int(request.form.get('group_id'))
        payment_method = request.form.get('payment_method')
        amount = request.form.get('amount')

        # Создаем или обновляем запись о студенте
        if not manage_student:
            manage_student = ManageStudent(student_id=student.student_id)
        manage_student.course_id = course_id
        manage_student.group_id = group_id
        db.session.add(manage_student)

        if amount:
            new_payment = Payment(student_id=student.student_id, amount=float(amount), method=payment_method)
            db.session.add(new_payment)
        
        db.session.commit()  # Сохраняем все изменения в базе данных
        flash('Изменения сохранены!', 'success')
        return redirect(url_for('management'))

    return render_template(
        'edit_management.html',
        administrator=administrator,
        student=student,
        courses=courses,
        groups=groups,
        current_course_id=current_course_id,
        current_group_id=current_group_id,
        balance=balance,
        course_prices=course_prices
    )


@app.route('/schedule_management')
@login_required
@role_required('Администратор', 'Учитель', 'Студент') 
def schedule_management():
    user = current_user

    administrator = None
    teacher = None
    student = None
    courses = []
    groups = []
    teachers = []
    full_name = ''
    if user.role == 'Администратор':
        base_template = "base_administrator.html"
        administrator = Administrator.query.filter_by(admin_id=user.id).first()  # Извлекаем объект администратора
        courses = Course.query.all()  # Получаем все курсы
        groups = Group.query.all()  # Получаем все группы
        teachers = Teacher.query.all()  # Получаем всех преподавателей

    elif user.role == 'Учитель':  # Если преподаватель
        base_template = "base_teacher.html"
        teacher = Teacher.query.filter_by(teacher_id=user.id).first()  # Получаем объект преподавателя
        if teacher:
            courses = Course.query.join(Schedule).filter(Schedule.teacher_id == teacher.teacher_id).all()  
            groups = Group.query.join(Schedule).filter(Schedule.teacher_id == teacher.teacher_id).all()  
            teachers = [teacher]
            print(f"Курсы для учителя: {[course.course_name for course in courses]}")
            print(f"Группы для учителя: {[group.group_name for group in groups]}")
    
    elif user.role == 'Студент':  # Если ученик
        base_template = "base_student.html"
        student = Student.query.filter_by(student_id=user.id).first()  # Получаем объект студента
        if student:
            full_name = f"{student.surname} {student.first_name}"

            # Получаем группу студента через таблицу ManageStudent
            groups = Group.query.join(ManageStudent).filter(ManageStudent.student_id == student.student_id).all()
            
            # Получаем курсы, к которым относится студент
            courses = Course.query.join(ManageStudent).filter(ManageStudent.student_id == student.student_id).all()


    return render_template('schedule_management.html', user=user, base_template=base_template, 
                    administrator=administrator, 
                    courses=courses, 
                    groups=groups, 
                    teachers=teachers,
                    teacher=teacher,
                    student=student,         
                    student_full_name=full_name 
)

@app.route('/get_events', methods=['GET'])
@login_required
@role_required('Администратор', 'Учитель', 'Студент') 
def get_events():
    user = current_user
    events = []
    
    if user.role == 'Администратор':  # Если админ, загружаем все события
        events = Schedule.query.all()
    elif user.role == 'Учитель':  # Если учитель, загружаем только его занятия
        teacher = Teacher.query.filter_by(teacher_id=user.id).first()
        if teacher:
            events = Schedule.query.filter_by(teacher_id=teacher.teacher_id).all()
    elif user.role == 'Студент':  # Для студента загружаем только его события
        student = Student.query.filter_by(student_id=user.id).first()
        if student:
            # Получаем группы студента через ManageStudent
            student_groups = db.session.query(ManageStudent.group_id).filter_by(student_id=student.student_id).subquery()

            # Фильтруем расписание по группам, в которых учится студент
            events = Schedule.query.filter(Schedule.group_id.in_(student_groups.select())).all()

            print(events)
    events_list = []

    for event in events:
        attendance_records = Attendance.query.filter_by(event_id=event.id).all()
        
        print(f"Event ID: {event.id}, Attendance Records: {attendance_records}")

        attendance_list = [record.student_id for record in attendance_records]

        event_data = {
            'id': event.id,
            'title': event.course.course_name if event.course else "Не указано",
            'start': f"{event.date}T{event.start_time}",
            'end': f"{event.date}T{event.end_time}" if event.end_time else None,
            'extendedProps': {
                'group_id': event.group.id if event.group else None,
                'group_name': event.group.group_name if event.group else "Не указано",
                'teacher_name': f"{event.teacher.first_name} {event.teacher.surname}" if event.teacher else "Не указано",
                'lesson_topic': event.lesson_topic or "",
                'attendance': attendance_list  
            }
        }
        events_list.append(event_data)

    return jsonify(events_list)


@app.route('/add_schedule', methods=['POST'])
@login_required
@role_required('Администратор')
def add_schedule():
    try:
        data = request.get_json()
        print("Полученные данные:", data)  # Лог

        start_datetime = datetime.fromisoformat(data['start_time'])
        end_datetime = datetime.fromisoformat(data['end_time'])

        date = start_datetime.date()
        start_time = start_datetime.time()
        end_time = end_datetime.time()

        group_id = int(data['group_id'])
        course_id = int(data['course_id'])
        teacher_id = int(data['teacher_id'])

        new_schedule = Schedule(
            date=date,
            start_time=start_time,
            end_time=end_time,
            group_id=group_id,
            course_id=course_id,
            teacher_id=teacher_id
        )

        db.session.add(new_schedule)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        print("Ошибка при добавлении расписания:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/delete_event', methods=['POST'])
@login_required
@role_required('Администратор')
def delete_event():
    data = request.get_json()
    event_id = data.get('event_id')

    event = Schedule.query.get(event_id)
    if not event:
        return jsonify({'success': False, 'error': 'Событие не найдено'})

    teacher_id = event.teacher_id
    course_id = event.course_id
    group_id = event.group_id
    duration_hours = (datetime.combine(event.date, event.end_time) - datetime.combine(event.date, event.start_time)).seconds / 3600

    try:
        db.session.delete(event)
        db.session.commit()

        # Вычитаем часы из зарплаты
        update_teacher_salary(teacher_id, -duration_hours, course_id, group_id)

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_students', methods=['GET'])
@login_required
@role_required('Администратор', 'Учитель', 'Ученик')
def get_students():
    print("DEBUG: role_required прошли")
    group_id = request.args.get('group_id')
    print(f"Получен запрос с group_id: {group_id}")
    if not group_id:
        return jsonify({"error": "group_id is required"}), 400

    user = current_user

    # Если учитель, проверяем, ведет ли он в этой группе
    if user.role == 'Учитель':
        print(f"DEBUG: user.id = {user.id}")  

        teacher = Teacher.query.filter_by(teacher_id=user.id).first()
        print(f"DEBUG: teacher найден: {teacher}")

        if not teacher:
            return jsonify({"error": "Преподаватель не найден"}), 403

        is_teaching = Schedule.query.filter_by(group_id=group_id, teacher_id=teacher.teacher_id).first()
        print(f"DEBUG: Учитель {teacher.teacher_id}, group_id {group_id}, is_teaching: {is_teaching}")

        if not is_teaching:
            return jsonify({"error": "Доступ запрещен"}), 403


        # Учителю можно увидеть весь список студентов группы
        students = db.session.query(Student).join(ManageStudent).filter(ManageStudent.group_id == group_id).all()
        students_list = [
            {"id": student.student_id, "full_name": f"{student.surname} {student.first_name}"}
            for student in students
        ]
        return jsonify(students_list)

    # Если админ — выводим всех
    if user.role == 'Администратор':
        students = db.session.query(Student).join(ManageStudent).filter(ManageStudent.group_id == group_id).all()
        students_list = [
            {"id": student.student_id, "full_name": f"{student.surname} {student.first_name}"}
            for student in students
        ]
        return jsonify(students_list)

    # Если ученик — возвращаем только его ФИО
    if user.role == 'Ученик':
        student = Student.query.get(user.id)
        if not student:
            return jsonify({"error": "Ученик не найден"}), 403

        in_group = ManageStudent.query.filter_by(student_id=student.student_id, group_id=group_id).first()
        if not in_group:
            return jsonify({"error": "Доступ запрещен"}), 403

        # Возвращаем только данные ученика
        student_info = {"id": student.student_id, "full_name": f"{student.surname} {student.first_name}"}
        return jsonify([student_info])

@app.route('/update_lesson_topic', methods=['POST'])
@login_required
@role_required('Администратор', 'Учитель')
def update_lesson_topic():
    data = request.json
    event_id = data.get('event_id')
    lesson_topic = data.get('lesson_topic')
    attendance_list = set(data.get('attendance', []))  # Уникальные ID студентов, которые присутствовали

    if not event_id or not lesson_topic:
        return jsonify({"error": "event_id и lesson_topic обязательны"}), 400

    # Находим событие
    schedule = Schedule.query.get(event_id)
    if not schedule:
        return jsonify({"error": "Событие не найдено"}), 404

    schedule.lesson_topic = lesson_topic

    # Получаем текущие записи посещаемости
    existing_attendance = {record.student_id: record for record in Attendance.query.filter_by(event_id=event_id)}

    # Добавляем новых студентов в базу
    new_students = attendance_list - existing_attendance.keys()
    for student_id in new_students:
        new_attendance = Attendance(event_id=event_id, student_id=student_id, attended=True)
        db.session.add(new_attendance)

    # Удаляем студентов, которых больше нет в списке
    students_to_remove = existing_attendance.keys() - attendance_list
    for student_id in students_to_remove:
        db.session.delete(existing_attendance[student_id])

    # Начисление зарплаты (только при первом сохранении посещаемости)
    if not existing_attendance and attendance_list:
        duration_hours = (datetime.combine(schedule.date, schedule.end_time) - datetime.combine(schedule.date, schedule.start_time)).total_seconds() / 3600

        salary_entry = Salary.query.filter_by(
            teacher_id=schedule.teacher_id,
            course_id=schedule.course_id,
            group_id=schedule.group_id
        ).first()

        if salary_entry:
            salary_entry.total_hours += duration_hours
            salary_entry.update_salary()
        else:
            new_salary_entry = Salary(
                teacher_id=schedule.teacher_id,
                course_id=schedule.course_id,
                group_id=schedule.group_id,
                month=schedule.date.strftime("%Y-%m"), 
                total_hours=duration_hours
            )
            db.session.add(new_salary_entry)

    db.session.commit()
    return jsonify({"success": True})



def get_chat_partners():
    print(f"Текущий пользователь: {current_user.id}, роль: {current_user.role}")

    if current_user.role == 'Администратор':
        users = Users.query.filter(Users.role.in_(['Учитель', 'Студент'])).all()
    elif current_user.role == 'Учитель':
        users = Users.query.filter(Users.role.in_(['Студент', 'Администратор'])).all() 
    elif current_user.role == 'Студент':
        users = Users.query.filter(Users.role.in_(['Учитель', 'Администратор'])).all()
    else:
        users = []

    print(f"Найдено пользователей: {len(users)}")
    return users

def get_full_name(user):
    if user.role == 'Администратор':
        admin = Administrator.query.filter_by(admin_id=user.id).first()
        return f"{admin.surname} {admin.first_name}" if admin else "Администратор"

    elif user.role == 'Учитель':
        teacher = Teacher.query.filter_by(teacher_id=user.id).first()
        return f"{teacher.surname} {teacher.first_name}" if teacher else "Учитель"

    elif user.role == 'Студент':
        student = Student.query.filter_by(student_id=user.id).first()
        return f"{student.surname} {student.first_name}" if student else "Студент"

    return "Неизвестный пользователь"


@app.route('/chat')
@login_required
@role_required('Администратор', 'Учитель', 'Студент')
def chat():
    user = current_user
    base_template = (
        "base_administrator.html" if user.role == "Администратор"
        else "base_teacher.html" if user.role == "Учитель"
        else "base_student.html"
    )

    teacher = None
    student = None
    administrator = None

    if user.role == 'Учитель':
        teacher = Teacher.query.filter_by(teacher_id=user.id).first()
    if user.role == 'Студент':
        student = Student.query.filter_by(student_id=user.id).first()
    if user.role == 'Администратор':
        administrator = Administrator.query.filter_by(admin_id=user.id).first()

    # Выбор собеседников в зависимости от роли
    if user.role == 'Студент':
        # Берем курсы и группы, в которых он учится
        student_courses = [enroll.course_id for enroll in student.enrollments]
        student_groups = [enroll.group_id for enroll in student.enrollments]

        # Находим учителей, которые ведут эти курсы или группы через расписание
        teachers = Teacher.query.join(Schedule).filter(
            (Schedule.course_id.in_(student_courses)) | 
            (Schedule.group_id.in_(student_groups))
        ).distinct().all()
        teacher_users = [Users.query.filter_by(id=t.teacher_id).first() for t in teachers]

        # Добавляем всех администраторов
        admins = Users.query.filter_by(role='Администратор').all()
        chat_partners = admins + teacher_users

    elif user.role == 'Учитель':
        # Берем курсы и группы, которые ведет учитель
        teacher_schedules = Schedule.query.filter_by(teacher_id=teacher.teacher_id).all()
        course_ids = list({s.course_id for s in teacher_schedules})
        group_ids = list({s.group_id for s in teacher_schedules})

        # Находим студентов из этих курсов и групп
        students = Student.query.join(ManageStudent).filter(
            (ManageStudent.course_id.in_(course_ids)) | 
            (ManageStudent.group_id.in_(group_ids))
        ).distinct().all()

        student_users = [Users.query.filter_by(id=s.student_id).first() for s in students]
        admins = Users.query.filter_by(role='Администратор').all()
        chat_partners = admins + student_users

    else:
        # Администратор видит всех кроме себя
        chat_partners = Users.query.filter(Users.id != user.id).all()

    print(f"Найдено пользователей: {len(chat_partners)}")
    for u in chat_partners:
        print(f"ID: {u.id}, Email: {u.email}, Role: {u.role}") 

    users = [
        {
            "id": u.id,
            "full_name": get_full_name(u), 
            "photo": url_for('static', filename='uploads/' + u.photo) if u.photo else url_for('static', filename='uploads/default.png'),
            "role": u.role 
        }
        for u in chat_partners if u  # добавил проверку на None на случай косяков с выборкой
    ]

    return render_template('chat.html', users=users, base_template=base_template, teacher=teacher, administrator=administrator, student=student)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.json
        recipient_id = data.get('recipient_id')
        message_text = data.get('message')
        
        if not recipient_id or not message_text:
            return jsonify({'error': 'Неверные данные'}), 400

        # Сохраняем сообщение в базе данных
        message = Message(sender_id=current_user.id, recipient_id=recipient_id, message=message_text)
        db.session.add(message)
        db.session.commit()
        
        # Отправляем пуш-уведомление с новым сообщением
        pusher_client.trigger(f'chat_{recipient_id}', 'new_message', {
            'sender': current_user.username,
            'message': message_text
        })
        
        return jsonify({'status': 'Message sent'})
    
    except Exception as e:
        # Логирование ошибки
        print(f"Ошибка при отправке сообщения: {e}")
        return jsonify({'error': 'Произошла ошибка при отправке сообщения.'}), 500


@app.route('/get_messages/<int:recipient_id>', methods=['GET'])
@login_required
def get_messages(recipient_id):
    try:
        # Получаем все сообщения между текущим пользователем и получателем
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient_id)) |
            ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.timestamp.asc()).all()
        
        # Получаем пользователей для сообщений заранее, чтобы избежать повторных запросов к базе данных
        users_dict = {user.id: get_full_name(user) for user in Users.query.all()}
        
        # Формируем ответ с данными сообщений
        return jsonify([{
            'sender': users_dict[msg.sender_id],  # Получаем имя отправителя из заранее подготовленного словаря
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages])

    except Exception as e:
        # Логирование ошибки
        print(f"Ошибка при загрузке сообщений: {e}")
        return jsonify({'error': 'Произошла ошибка при загрузке сообщений.'}), 500

# Функция для обновления или создания записи о зарплате учителя
def update_teacher_salary(teacher_id, hours, course_id, group_id):
    current_month = datetime.now().strftime('%Y-%m')

    print(f"Обновление зарплаты: Teacher ID: {teacher_id}, Course ID: {course_id}, Group ID: {group_id}, Hours: {hours}")

    salary = Salary.query.filter_by(
        teacher_id=teacher_id,
        course_id=course_id,
        group_id=group_id,
        month=current_month,
        status='Ожидает оплаты'
    ).first()

    if salary:
        salary.total_hours += hours
        if salary.total_hours <= 0:
            db.session.delete(salary)  # Удаляем запись, если часов не осталось
        else:
            salary.total_salary = salary.total_hours * salary.hourly_rate  # Пересчет суммы
    else:
        if hours > 0:  # Добавляем новую запись, только если есть положительные часы
            last_salary = Salary.query.filter_by(teacher_id=teacher_id).order_by(Salary.month.desc()).first()
            last_hourly_rate = last_salary.hourly_rate if last_salary else 1500

            salary = Salary(
                teacher_id=teacher_id,
                course_id=course_id,
                group_id=group_id,
                month=current_month,
                total_hours=hours,
                hourly_rate=last_hourly_rate,
                total_salary=hours * last_hourly_rate,
                status='Ожидает оплаты'
            )
            db.session.add(salary)

    db.session.commit()



# Функция для обработки выплаты зарплаты
def pay_teacher_salary(salary_id):
    salary = Salary.query.get(salary_id)
    if salary and salary.status == 'Ожидает оплаты':
        salary.status = 'Оплачено'
        salary.payment_date = datetime.now().date()
        db.session.commit()

# Пример вызова при добавлении записи в расписание
def on_schedule_added(teacher_id, course_id, group_id, date, start_time, end_time):
    # Подсчет часов
    print(f"Добавление занятия: {teacher_id}, {course_id}, {group_id}, {date}, {start_time}, {end_time}")

    duration = (datetime.combine(date, end_time) - datetime.combine(date, start_time)).seconds / 3600
    
    # Проверяем, есть ли уже такая запись
    existing_schedule = Schedule.query.filter_by(teacher_id=teacher_id, course_id=course_id, group_id=group_id, date=date, start_time=start_time, end_time=end_time).first()
    print(existing_schedule)
    if not existing_schedule:
        # Создаем запись в расписании, если ее нет
        new_schedule = Schedule(
            teacher_id=teacher_id,
            course_id=course_id,
            group_id=group_id,
            date=date,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(new_schedule)
        db.session.commit()
    
    # Обновляем зарплату учителя
    update_teacher_salary(teacher_id, duration)


# Обновление ставки за час
@app.route('/update_hourly_rate', methods=['POST'])
def update_hourly_rate():
    data = request.json
    salary_id = data.get('salary_id')
    new_rate = data.get('new_rate')
    print(f"Получен запрос: salary_id={salary_id}, new_rate={new_rate}")

    salary = Salary.query.get(salary_id)
    if salary:
        print(f"Зарплата ID: {salary.id}, Часы: {salary.total_hours}, Ставка: {salary.hourly_rate}")
        salary.hourly_rate = float(new_rate)
        salary.update_salary()  # Пересчет зарплаты
        db.session.commit()
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Запись не найдена"}), 404


@app.route('/pay_salary', methods=['POST'])
def pay_salary():
    data = request.json
    salary_id = data.get('salary_id')
    print(f"Полученный salary_id: {salary_id}")  # Логируем ID

    salary = Salary.query.get(salary_id)
    if salary:
        print(f"Найдена зарплата {salary.id}, статус: {salary.status}")  # Лог

    if salary and salary.status == 'Ожидает оплаты':
        salary.status = 'Оплачено'
        salary.payment_date = datetime.now().date()
        db.session.commit()
        print(f"Зарплата {salary.id} обновлена: {salary.status}, {salary.payment_date}")  # Лог
        return jsonify({"success": True})

    print("Ошибка оплаты!")  # Лог ошибки
    return jsonify({"success": False, "error": "Не удалось оплатить"}), 400

# Словарь для перевода месяцев на русский
MONTHS_RU = {
    "January": "Январь", "February": "Февраль", "March": "Март",
    "April": "Апрель", "May": "Май", "June": "Июнь",
    "July": "Июль", "August": "Август", "September": "Сентябрь",
    "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"
}

@app.route('/salary_management')
@login_required
@role_required('Администратор', 'Учитель')
def salary_management():
    user = current_user
    base_template = "base_administrator.html" if user.role == 'Администратор' else "base_teacher.html"
    teacher = None
    if user.role == 'Учитель':
        teacher = Teacher.query.filter_by(teacher_id=user.id).first()
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    
    # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 3

    # Запрос данных
    query = (
        db.session.query(
            Salary.id,
            Teacher.teacher_id.label("teacher_id"),
            Teacher.surname,
            Teacher.first_name,
            Teacher.patronymic,
            func.group_concat(Course.course_name, ', ').label("courses"),
            func.group_concat(Group.group_name, ', ').label("groups"),
            func.sum(Salary.total_hours).label("total_hours"),
            func.sum(Salary.total_salary).label("total_salary"),
            func.max(Salary.hourly_rate).label("hourly_rate"),
            Salary.month,
            Salary.status,
            Salary.payment_date
        )
        .join(Salary, Salary.teacher_id == Teacher.teacher_id)
        .outerjoin(Course, Salary.course_id == Course.id)  
        .outerjoin(Group, Salary.group_id == Group.id)  
        .group_by(Teacher.id, Salary.month, Salary.status, Salary.payment_date)  
    )
    if user.role == 'Учитель' and teacher:
        query = query.filter(Teacher.teacher_id == teacher.teacher_id)

    # Группировка и пагинация
    salaries_pagination = query.group_by(Teacher.id, Salary.month, Salary.status, Salary.payment_date) \
                                .order_by(Salary.status.asc(), Salary.payment_date.desc()) \
                                .paginate(page=page, per_page=per_page)
    def format_month(date_str):
        if date_str:
            dt = datetime.strptime(date_str, "%Y-%m")
            month_en = dt.strftime("%B")  # Получаем месяц на английском
            month_ru = MONTHS_RU.get(month_en, month_en)  # Переводим на русский
            return f"{month_ru} {dt.year}"
        return "Не указан"

    # Создаем новый список словарей (чтобы можно было редактировать)
    salaries = []
    for salary in salaries_pagination.items:

        salaries.append({
            "id": salary.id,
            "teacher_id": salary.teacher_id,
            "surname": salary.surname,
            "first_name": salary.first_name,
            "patronymic": salary.patronymic,
            "courses": ", ".join(set(salary.courses.split(", "))) if salary.courses else "Не указано",
            "groups": ", ".join(set(salary.groups.split(", "))) if salary.groups else "Не указано",
            "total_hours": salary.total_hours,
            "total_salary": salary.total_salary,
            "hourly_rate": salary.hourly_rate,
            "month": format_month(salary.month),
            "status": salary.status,
            "payment_date": salary.payment_date
        })

    return render_template(
        'salary_management.html', 
        salaries=salaries,  
        administrator=administrator, 
        pagination=salaries_pagination,
        base_template=base_template,
        teacher=teacher,
        is_teacher=user.role == 'Учитель',
    )


# Страница выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Инициализация базы данных и запуск приложения
if __name__ == "__main__":
    app.run(debug=True)

