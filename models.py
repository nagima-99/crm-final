from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.now)
    photo = db.Column(db.String(120), nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Administrator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    surname = db.Column(db.String(50), nullable=False)   
    first_name = db.Column(db.String(50), nullable=False) 
    patronymic = db.Column(db.String(50), nullable=True) 
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    office_name = db.Column(db.String(255), nullable=False)
    office_address = db.Column(db.String(255), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    surname = db.Column(db.String(50), nullable=False)   
    first_name = db.Column(db.String(50), nullable=False) 
    patronymic = db.Column(db.String(50), nullable=True)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    client_name = db.Column(db.String(255), nullable=True)
    client_relation = db.Column(db.String(100), nullable=True)
    client_phone = db.Column(db.String(20), nullable=True)
    user = db.relationship('Users', backref='student', uselist=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    surname = db.Column(db.String(50), nullable=False)   
    first_name = db.Column(db.String(50), nullable=False) 
    patronymic = db.Column(db.String(50), nullable=True)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    education = db.Column(db.String(255), nullable=False)
    user = db.relationship('Users', backref='teacher', uselist=False)
    
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    academic_hours = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    students = db.relationship('ManageStudent', back_populates='course')

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)
    students = db.relationship('ManageStudent', back_populates='group')

class ManageStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    student = db.relationship('Student', backref='enrollments')
    course = db.relationship('Course', back_populates='students')
    group = db.relationship('Group', back_populates='students')


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False) 
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)  
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.teacher_id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)  # Дата занятия
    start_time = db.Column(db.Time, nullable=False)  # Время начала
    end_time = db.Column(db.Time, nullable=False)  # Время окончания
    lesson_topic = db.Column(db.String, nullable=True)

    course = db.relationship('Course', backref='schedules')
    group = db.relationship('Group', backref='schedules')
    teacher = db.relationship('Teacher', backref='schedules')
    
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    attended = db.Column(db.Boolean, default=False)

    event = db.relationship('Schedule', backref='attendances')
    student = db.relationship('Student', backref='attendances')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    method = db.Column(db.String(50), nullable=False)  # "Наличные" или "Безналичные"
