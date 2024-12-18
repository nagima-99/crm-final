from app import db, ManageStudent, ManageTeacher, app  # Импортируйте необходимые модули и классы из вашего приложения

def delete_records(model, model_name):
    """
    Удаляет все записи из указанной модели.
    
    :param model: Модель базы данных
    :param model_name: Название модели для отображения в сообщении
    """
    with app.app_context():  # Установить контекст приложения
        try:
            db.session.query(model).delete()  # Удалить все записи
            db.session.commit()  # Применить изменения
            print(f"Все записи удалены из {model_name}")
        except Exception as e:
            db.session.rollback()  # Откат изменений при ошибке
            print(f"Ошибка при удалении записей из {model_name}: {e}")

if __name__ == "__main__":
    delete_records(ManageStudent, "ManageStudent")
    delete_records(ManageTeacher, "ManageTeacher")
