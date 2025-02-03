from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from forms import AdministratorForm, UpdateUserForm, RegisterStudentForm, RegisterTeacherForm, CourseForm, GroupForm
from models import db, Users, Administrator, Teacher, Student, Course, Group, ManageStudent, ManageTeacher, Schedule
from functools import wraps
import logging

# Инициализация приложения
app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем лишние предупреждения
app.config['SECRET_KEY'] = 'your_secret_key'  # Для защиты форм
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
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Недостаточно прав доступа')
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
            if user.role == 'Администратор':
                return redirect(url_for('administrator_dashboard', id=user.id))
            elif user.role == 'Учитель':
                return redirect(url_for('teacher_dashboard'))
            elif user.role == 'Студент':
                return redirect(url_for('student_dashboard'))
        else:
            flash('Неправильное имя пользователя или пароль')

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
        flash('Администратор не найден!')
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
                administrator.birth_date = form.birth_date.data 

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

    return render_template('update_user.html', form=form, administrator=administrator, user=user)


@app.route('/upload_photo/<int:id>', methods=['POST'])
@login_required
def upload_photo(id):
    user = Users.query.get_or_404(id)  # Получаем пользователя

    if 'photo' not in request.files:
        flash('Файл не выбран')
        return redirect(request.referrer)

    file = request.files['photo']
    if file.filename == '':
        flash('Нет выбранного файла')
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

        flash('Фото успешно загружено')
        return redirect(request.referrer)  # Перенаправляем на страницу, с которой был отправлен запрос


@app.route('/delete_photo/<int:id>', methods=['POST'])
@login_required
@role_required('Администратор')
def delete_photo(id):
    user = Users.query.get_or_404(id)

    if user.photo:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], user.photo))
            user.photo = None
            db.session.commit()
            flash('Фото успешно удалено!')
        except Exception as e:
            flash(f'Ошибка при удалении фотографии: {e}')
    
    return redirect(url_for('administrator_dashboard', id=id))


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
        flash("Студент не найден!")
        return redirect(url_for('students_list'))

    # Удаляем связанного пользователя
    user = student.user  # Получаем связанного пользователя
    if user:
        db.session.delete(user)  # Удаляем пользователя из таблицы Users
    
    db.session.delete(student)  # Удаляем студента из таблицы Student
    db.session.commit()  # Подтверждаем изменения в базе данных

    flash("Студент и пользователь успешно удалены!")
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
        flash("Преподаватель не найден!")
        return redirect(url_for('teachers_list'))

    user = teacher.user  # Связанный пользователь
    if user:
        db.session.delete(user)

    db.session.delete(teacher)
    db.session.commit()

    flash("Преподаватель успешно удалены!")
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
        flash('Администратор не найден!')
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
        flash('Администратор не найден!')
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


# Добавить новый курс
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def add_course():
    form = CourseForm()
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    if form.validate_on_submit():
        try:
            # Проверка на уникальность названия курса
            existing_course = Course.query.filter_by(course_name=form.course_name.data).first()
            if existing_course:
                # Если курс с таким именем уже существует, отобразить сообщение об ошибке
                flash("Курс с таким названием уже существует. Пожалуйста, выберите другое название.", "danger")
            else:
                course = Course(course_name=form.course_name.data, 
                                academic_hours=form.academic_hours.data,
                                price=form.price.data)
                db.session.add(course)
                db.session.commit()
                flash("Курс успешно добавлен!", "success")
                return redirect(url_for('list_courses'))
        except Exception as e:
            db.session.rollback()
            flash("Произошла ошибка при добавлении курса. Повторите попытку.", "danger")
        # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    return render_template('add_course.html', form=form, administrator=administrator)

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
@app.route('/add_group', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def add_group():
    form = GroupForm()  # Пример формы, которую нужно создать
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()

    if form.validate_on_submit():
        try:
            existing_group = Group.query.filter_by(group_name=form.group_name.data).first()
            if existing_group:
                flash("Группа с таким названием уже существует. Пожалуйста, выберите другое название.", "danger")
            else:
                group = Group(group_name=form.group_name.data)  
                db.session.add(group)
                db.session.commit()
                flash("Группа успешно добавлена!", "success")
                return redirect(url_for('list_groups'))
        except Exception as e:
            db.session.rollback()
            flash("Произошла ошибка при добавлении группы. Повторите попытку.", "danger")
        # Обработка ошибок формы (если есть)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", "danger")
    return render_template('add_group.html', form=form, administrator=administrator)

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
@app.route('/groups', methods=['GET'])
@login_required
@role_required('Администратор')
def list_groups():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    groups = Group.query.all()
    # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 8 

    # Пагинация
    pagination = Group.query.paginate(page=page, per_page=per_page)
    groups = pagination.items 
    return render_template('groups.html', groups=groups, administrator=administrator, pagination=pagination)

@app.route('/management', methods=['GET'])
@login_required
@role_required('Администратор')
def management():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
        # Получаем текущую страницу из запроса, по умолчанию 1
    page = request.args.get('page', 1, type=int)
    per_page = 9 # Количество учеников на одной странице

    
    # Пагинация
    student_pagination = Student.query.paginate(page=page, per_page=per_page)
    students = student_pagination.items  # Ученики текущей страницы

    courses = Course.query.all()
    groups = Group.query.all()
    teachers = Teacher.query.all()
    

    student_info = []

    for student in students:
        manage_student_entry = ManageStudent.query.filter_by(student_id=student.student_id).first()
        course = None
        group = None
        teacher = None

        if manage_student_entry:
            # Получаем курс и группу
            course = Course.query.get(manage_student_entry.course_id)
            group = Group.query.get(manage_student_entry.group_id)

            # Получаем преподавателя
            manage_teacher = ManageTeacher.query.filter_by(
                group_id=manage_student_entry.group_id,
                course_id=manage_student_entry.course_id
            ).first()

            if manage_teacher:
                teacher = Teacher.query.get(manage_teacher.teacher_id)

        student_info.append({
            'student': student,
            'course': course,
            'group': group,
            'teacher': teacher
        })

    return render_template(
        'management.html',
        administrator=administrator,
        student_info=student_info,
        courses=courses,
        groups=groups,
        teachers=teachers,
        student_pagination=student_pagination
    )

@app.route('/edit_management/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def edit_management(id):
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    student = Student.query.filter_by(student_id=id).first_or_404()
    courses = Course.query.all()
    groups = Group.query.all()
    teachers = Teacher.query.all()

    # Получаем существующие данные о студенте
    manage_student = ManageStudent.query.filter_by(student_id=student.student_id).first()
    current_course_id = manage_student.course_id if manage_student else None
    current_group_id = manage_student.group_id if manage_student else None

    # Находим преподавателя для этого студента
    manage_teacher = None
    current_teacher_id = None
    if manage_student:
        manage_teacher = ManageTeacher.query.filter_by(
            group_id=manage_student.group_id,
            course_id=manage_student.course_id
        ).first()
        current_teacher_id = manage_teacher.teacher_id if manage_teacher else None

    if request.method == 'POST':
        course_id = int(request.form.get('course_id'))
        group_id = int(request.form.get('group_id'))
        teacher_id = int(request.form.get('teacher_id'))  # Получаем teacher_id из формы
        start_date = request.form.get('start_date')  # Получаем дату начала
        end_date = request.form.get('end_date')  # Получаем дату окончания

        # Преобразуем строки в datetime объекты (если формат даты правильный)
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M')

        # Создаем или обновляем запись о студенте
        if not manage_student:
            manage_student = ManageStudent(student_id=student.student_id)
        manage_student.course_id = course_id
        manage_student.group_id = group_id
        db.session.add(manage_student)

        # Создаем или обновляем запись о преподавателе
        if not manage_teacher:
            manage_teacher = ManageTeacher(
                teacher_id=teacher_id,  
                group_id=group_id,
                course_id=course_id
            )
        else:
            manage_teacher.course_id = course_id
            manage_teacher.group_id = group_id
            manage_teacher.teacher_id = teacher_id

        db.session.add(manage_teacher)

        # Добавляем или обновляем запись о расписании
        schedule = Schedule.query.filter_by(
            course_id=course_id, group_id=group_id, teacher_id=teacher_id).first()

        if not schedule:
            # Создание нового расписания
            schedule = Schedule(
                course_id=course_id,
                group_id=group_id,
                teacher_id=teacher_id,
                start_time=start_datetime,  # Сохраняем время начала
                end_time=end_datetime,      # Сохраняем время окончания
            )
            db.session.add(schedule)
        else:
            # Обновление существующего расписания
            schedule.start_time = start_datetime
            schedule.end_time = end_datetime

        db.session.commit()  # Сохраняем все изменения в базе данных
        flash('Изменения сохранены!')
        return redirect(url_for('management'))

    return render_template(
        'edit_management.html',
        administrator=administrator,
        student=student,
        courses=courses,
        groups=groups,
        teachers=teachers,
        current_course_id=current_course_id,
        current_group_id=current_group_id,
        current_teacher_id=current_teacher_id  # Передаем ID текущего преподавателя
    )


@app.route('/schedule_management')
def schedule_management():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()  # Извлекаем объект администратора
    courses = Course.query.all()  # Получаем все курсы
    groups = Group.query.all()  # Получаем все группы
    teachers = Teacher.query.all()  # Получаем всех преподавателей

    return render_template('schedule_management.html', administrator=administrator, courses=courses, groups=groups, teachers=teachers)

@app.route('/get_events', methods=['GET'])
def get_events():
    events = Schedule.query.all()  # Извлекаем все события из базы
    events_list = [
        {
            'id': event.id,
            'title': f'Курс {event.course.course_name}',  # Укажите как хотите отображать название
            'start': event.start_time.isoformat(),  # Преобразуем дату в строку ISO
            'end': event.end_time.isoformat() if event.end_time else None,
        }
        for event in events
    ]
    return jsonify(events_list)

@app.route('/update_event', methods=['POST'])
def update_event():
    data = request.get_json()
    event_id = data['id']
    start_time = data['start']
    end_time = data['end']

    # Найти событие по ID
    event = Schedule.query.get(event_id)
    if event:
        event.start_time = datetime.fromisoformat(start_time)
        event.end_time = datetime.fromisoformat(end_time) if end_time else None
        db.session.commit()
        return jsonify({
            'id': event.id,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat() if event.end_time else None,
        })
    
    return jsonify({'error': 'Event not found'}), 404


# Страница выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Инициализация базы данных и запуск приложения
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True, threaded=True)
