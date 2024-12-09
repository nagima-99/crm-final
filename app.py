from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from forms import AdministratorForm, RegisterStudentForm, RegisterTeacherForm, CourseForm, GroupForm
from models import db, Users, Administrator, Teacher, Student, Course, Group
from functools import wraps

# Инициализация приложения
app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем лишние предупреждения
app.config['SECRET_KEY'] = 'your_secret_key'  # Для защиты форм

# Инициализация базы данных
db.init_app(app)

# Инициализация логина
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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
@app.route('/administrator/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def administrator_dashboard(id):
    administrator = Administrator.query.filter_by(admin_id=id).first()
    if not administrator:
        flash('Администратор не найден!')
        return redirect(url_for('login'))

    age = calculate_age(administrator.birth_date)
    form = AdministratorForm(obj=administrator)

    if form.validate_on_submit():
        form.populate_obj(administrator)
        db.session.commit()
        flash('Данные успешно обновлены!')
        return redirect(url_for('administrator_dashboard', id=id))

    return render_template('administrator_dashboard.html', administrator=administrator, age=age, form=form)

# Cписок учеников
@app.route('/students', methods=['GET'])
@login_required
@role_required('Администратор')
def students_list():
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    students = Student.query.all()

    student_ages = {student.id: calculate_age(student.birth_date) for student in students}

    return render_template('students_list.html', students=students, administrator=administrator, student_ages=student_ages)


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

    teacher_ages = {teacher.id: calculate_age(teacher.birth_date) for teacher in teachers}

    return render_template('teachers_list.html', teachers=teachers, administrator=administrator, teacher_ages=teacher_ages)


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

    flash("Преподаватель и пользователь успешно удалены!")
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
                client_workplace=form.client_workplace.data,
                client_position=form.client_position.data
            )
            db.session.add(student)
            db.session.commit()  # Сохраняем данные в таблицу Teacher

            print('Студент успешно зарегистрирован!', 'success')
            return redirect(url_for('students_list', id=current_user.id))
        
        except Exception as e:
            db.session.rollback()  # Откатываем изменения при ошибке
            print(f'Ошибка при добавлении ученика: {e}', 'danger')
    
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
            return redirect(url_for('administrator_dashboard', id=current_user.id))
        
        except Exception as e:
            db.session.rollback()  # Откатываем изменения при ошибке
            return(f'Ошибка при добавлении teacher: {e}', 'danger')
    
    return render_template('register_teacher.html', form=form, administrator=administrator)


# Добавить новый курс
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def add_course():
    form = CourseForm()
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    if form.validate_on_submit():
        # Проверка на уникальность названия курса
        existing_course = Course.query.filter_by(course_name=form.course_name.data).first()
        if existing_course:
            # Если курс с таким именем уже существует, отобразить сообщение об ошибке
            form.course_name.errors.append("Курс с таким названием уже существует. Пожалуйста, выберите другое название.")
        else:
            course = Course(course_name=form.course_name.data, 
                            academic_hours=form.academic_hours.data,
                            price=form.price.data)
            db.session.add(course)
            db.session.commit()
            return redirect(url_for('list_courses'))
    return render_template('add_course.html', form=form, administrator=administrator)

# Редактировать курс
@app.route('/edit_course/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def edit_course(id):
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()
    course = Course.query.get_or_404(id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.course_name = form.course_name.data
        course.academic_hours = form.academic_hours.data
        course.price = form.price.data
        db.session.commit()
        return redirect(url_for('list_courses'))
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
    return render_template('courses.html', courses=courses, administrator=administrator)


# Добавить новую группу
@app.route('/add_group', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def add_group():
    form = GroupForm()  # Пример формы, которую нужно создать
    administrator = Administrator.query.filter_by(admin_id=current_user.id).first()  # Извлекаем объект администратора

    if form.validate_on_submit():
        existing_group = Group.query.filter_by(group_name=form.group_name.data).first()
        if existing_group:
            form.group_name.errors.append("Группа с таким названием уже существует. Пожалуйста, выберите другое название.")
        else:
            group = Group(group_name=form.group_name.data)  # Допустим, у группы есть название
            db.session.add(group)
            db.session.commit()
            return redirect(url_for('list_groups'))
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
        group.group_name = form.group_name.data
        db.session.commit()
        return redirect(url_for('list_groups'))
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
    return render_template('groups.html', groups=groups, administrator=administrator)


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
