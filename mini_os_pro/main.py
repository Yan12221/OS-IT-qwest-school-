import sys
import json
import pathlib
import shutil
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QAbstractItemView

from filesystem import ProFileSystem


# База пользователей (data/users.json)
USERS_FILE = "data/users.json"

def load_users():
    try:
        if pathlib.Path(USERS_FILE).exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"user1": "1234", "user2": "5678", "admin": "admin"}

def save_users(users):
    pathlib.Path(USERS_FILE).parent.mkdir(exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


class LoginDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProOS – Вход")
        self.setFixedSize(350, 220)

        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("Файловая система ProOS")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        form_layout = QtWidgets.QFormLayout()

        self.login_edit = QtWidgets.QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        form_layout.addRow("Логин:", self.login_edit)

        self.pass_edit = QtWidgets.QLineEdit()
        self.pass_edit.setPlaceholderText("Пароль")
        self.pass_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form_layout.addRow("Пароль:", self.pass_edit)

        layout.addLayout(form_layout)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_login = QtWidgets.QPushButton("Войти")
        self.btn_login.clicked.connect(self.accept)
        self.btn_guest = QtWidgets.QPushButton("Гость")
        self.btn_guest.clicked.connect(self.login_guest)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guest)
        btn_layout.addWidget(self.btn_login)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background-color: #121212; color: #ffffff; }
        QLineEdit { 
            background-color: #1E1E1E; border: 1px solid #333333; 
            border-radius: 4px; padding: 8px; 
        }
        QLineEdit:focus { border-color: #4CAF50; }
        QPushButton { 
            background-color: #2D2D2D; border: 1px solid #3A3A3A; 
            border-radius: 6px; padding: 10px 20px; 
        }
        QPushButton:hover { background-color: #4CAF50; color: white; }
        """)

    def login_guest(self):
        self.login_edit.setText("guest")
        self.pass_edit.setText("")
        self.accept()

    def get_credentials(self) -> tuple[str, str]:
        return self.login_edit.text().strip(), self.pass_edit.text().strip()


class AdminPanel(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.fs = ProFileSystem()
        self.current_admin_user = None
        self.setWindowTitle("ProOS – Админ-панель")
        self.resize(900, 700)
        self._setup_ui()

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Заголовок
        title = QtWidgets.QLabel("🔧 Администраторская панель")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # Список пользователей
        layout.addWidget(QtWidgets.QLabel("👥 Пользователи системы:"))
        self.user_list = QtWidgets.QListWidget()
        self.user_list.itemClicked.connect(self.on_user_selected)
        layout.addWidget(self.user_list, 1)

        # Кнопки управления пользователями
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_add_user = QtWidgets.QPushButton("➕ Добавить пользователя")
        self.btn_del_user = QtWidgets.QPushButton("🗑️ Удалить пользователя")
        self.btn_refresh_users = QtWidgets.QPushButton("🔄 Обновить")
        btn_layout.addWidget(self.btn_add_user)
        btn_layout.addWidget(self.btn_del_user)
        btn_layout.addWidget(self.btn_refresh_users)
        layout.addLayout(btn_layout)

        # Инфо о выбранном пользователе
        self.user_info = QtWidgets.QLabel("Выберите пользователя для просмотра файлов")
        self.user_info.setStyleSheet("padding: 10px; background-color: #1E1E1E; border-radius: 4px;")
        layout.addWidget(self.user_info)

        # Список файлов выбранного пользователя
        layout.addWidget(QtWidgets.QLabel("📁 Файлы пользователя:"))
        self.admin_file_list = QtWidgets.QListWidget()
        self.admin_file_list.itemDoubleClicked.connect(self.on_admin_file_selected)
        layout.addWidget(self.admin_file_list, 2)

        # Сигналы
        self.btn_add_user.clicked.connect(self.add_user)
        self.btn_del_user.clicked.connect(self.delete_user)
        self.btn_refresh_users.clicked.connect(self.refresh_users)

        self.refresh_users()
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
        QMainWindow { background-color: #121212; color: #ffffff; }
        QListWidget { 
            background-color: #1E1E1E; border: 1px solid #333333; border-radius: 4px;
        }
        QPushButton { 
            background-color: #2D2D2D; border: 1px solid #3A3A3A; 
            border-radius: 6px; padding: 8px 16px; font-weight: bold;
        }
        QPushButton:hover { background-color: #4CAF50; color: white; }
        QPushButton:pressed { background-color: #45a049; }
        QLabel { padding: 5px; }
        """)

    def refresh_users(self):
        self.user_list.clear()
        global USERS_DB
        USERS_DB = load_users()
        for user in USERS_DB:
            item = QtWidgets.QListWidgetItem(f"👤 {user}")
            self.user_list.addItem(item)

    def on_user_selected(self, item):
        username = item.text()[2:]  # убираем "👤 "
        self.current_admin_user = username
        file_count = len(self.fs.user_files.get(username, {}))
        self.user_info.setText(f"👤 {username} | Файлов: {file_count} | Размер: {sum(f.get('size', 0) for f in self.fs.user_files.get(username, {}).values())} байт")

        # Загружаем файлы пользователя
        self.admin_file_list.clear()
        files = self.fs.user_files.get(username, {})
        for filename in sorted(files.keys()):
            item = QtWidgets.QListWidgetItem(filename)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, filename)
            self.admin_file_list.addItem(item)

    def on_admin_file_selected(self, item):
        if not self.current_admin_user:
            return
        filename = item.data(QtCore.Qt.ItemDataRole.UserRole)
        content = self.fs.read(filename, self.current_admin_user)
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Просмотр: {filename}")
        dialog.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(dialog)
        text_edit = QtWidgets.QPlainTextEdit()
        text_edit.setPlainText(content or "Пустой файл")
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        dialog.exec()

    def add_user(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("➕ Добавить пользователя")
        dialog.setFixedSize(350, 180)
        layout = QtWidgets.QVBoxLayout(dialog)

        form = QtWidgets.QFormLayout()
        login_edit = QtWidgets.QLineEdit()
        pass_edit = QtWidgets.QLineEdit()
        pass_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        form.addRow("Логин:", login_edit)
        form.addRow("Пароль:", pass_edit)
        layout.addLayout(form)

        btn_ok = QtWidgets.QPushButton("Создать")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            login = login_edit.text().strip()
            password = pass_edit.text().strip()
            if login and password and login not in USERS_DB:
                global USERS_DB
                USERS_DB[login] = password
                save_users(USERS_DB)
                self.refresh_users()
                QtWidgets.QMessageBox.information(self, "✅ Успех", f"Пользователь '{login}' создан!")
            else:
                QtWidgets.QMessageBox.warning(self, "❌ Ошибка", "Логин занят или поля пустые!")

    def delete_user(self):
        item = self.user_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "❌ Ошибка", "Выберите пользователя!")
            return

        username = item.text()[2:]
        if username == "admin":
            QtWidgets.QMessageBox.warning(self, "❌ Ошибка", "Нельзя удалить администратора!")
            return

        res = QtWidgets.QMessageBox.question(self, "⚠️ Подтверждение", 
                                           f"Удалить пользователя '{username}' и ВСЕ его файлы?")
        if res == QtWidgets.QMessageBox.StandardButton.Yes:
            # Удаляем из БД пользователей
            global USERS_DB
            del USERS_DB[username]
            save_users(USERS_DB)
            
            # Удаляем папку пользователя
            user_path = self.fs.data_dir / username
            if user_path.exists():
                shutil.rmtree(user_path)
            
            # Удаляем из метаданных
            if username in self.fs.user_files:
                del self.fs.user_files[username]
            self.fs.save_metadata()
            
            self.refresh_users()
            self.admin_file_list.clear()
            self.user_info.setText("Пользователь удалён")
            QtWidgets.QMessageBox.information(self, "✅ Успех", f"Пользователь '{username}' удалён!")


class FileSystemWindow(QtWidgets.QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.fs = ProFileSystem()
        self.current_user = username
        self.current_path = "."
        self.setWindowTitle(f"ProOS – файловый менеджер ({username})")
        self.resize(1000, 600)
        self._setup_ui()
        self._setup_animations()
        self.load_files()

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # Верхняя панель
        top_bar = QtWidgets.QHBoxLayout()
        user_label = QtWidgets.QLabel(f"👤 {self.current_user}")
        user_label.setStyleSheet("font-weight: bold; padding: 8px; font-size: 14px;")
        top_bar.addWidget(user_label)
        top_bar.addStretch()

        self.btn_create = QtWidgets.QPushButton("➕ Создать")
        self.btn_edit = QtWidgets.QPushButton("✏️ Редактировать")
        self.btn_delete = QtWidgets.QPushButton("🗑️ Удалить")
        self.btn_refresh = QtWidgets.QPushButton("🔄 Обновить")
        self.btn_back = QtWidgets.QPushButton("⬅️ Назад")

        top_bar.addWidget(self.btn_back)
        top_bar.addWidget(self.btn_create)
        top_bar.addWidget(self.btn_edit)
        top_bar.addWidget(self.btn_delete)
        top_bar.addWidget(self.btn_refresh)

        main_layout.addLayout(top_bar)

        # Сплиттер
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Левая панель (файлы)
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        self.path_label = QtWidgets.QLabel(f"📁 Путь: {self.current_path}")
        self.path_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.file_list = QtWidgets.QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        left_layout.addWidget(self.path_label)
        left_layout.addWidget(self.file_list, 1)
        splitter.addWidget(left_panel)

        # Правая панель (содержимое)
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        self.content_title = QtWidgets.QLabel("📄 Содержимое файла")
        self.content_title.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        right_layout.addWidget(self.content_title)
        right_layout.addWidget(self.text_edit, 1)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])

        # Сигналы
        self.file_list.itemClicked.connect(self.on_file_selected)
        self.btn_create.clicked.connect(self.on_create_clicked)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_refresh.clicked.connect(self.load_files)
        self.btn_back.clicked.connect(self.go_back)

        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
        QMainWindow { background-color: #121212; color: #ffffff; }
        QListWidget { 
            background-color: #1E1E1E; border: 1px solid #333333; border-radius: 6px;
            font-family: 'Consolas', monospace;
        }
        QPlainTextEdit { 
            background-color: #1E1E1E; border: 1px solid #333333; border-radius: 6px;
            font-family: 'Consolas', monospace;
        }
        QPushButton { 
            background-color: #2D2D2D; border: 1px solid #3A3A3A; 
            border-radius: 6px; padding: 8px 16px; font-weight: bold;
        }
        QPushButton:hover { background-color: #4CAF50; color: white; }
        QPushButton:pressed { background-color: #45a049; }
        """)

    def _setup_animations(self):
        self.fade_anim = QtCore.QPropertyAnimation(self.text_edit, b"windowOpacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)

    def animate_content(self):
        self.text_edit.setWindowOpacity(0.0)
        self.fade_anim.start()

    def go_back(self):
        if self.current_path == ".":
            return
        parts = self.current_path.split("/")
        parts.pop()
        self.current_path = "/".join(parts) if parts else "."
        self.path_label.setText(f"📁 Путь: {self.current_path}")
        self.load_files()

    def load_files(self):
        self.file_list.clear()
        items = self.fs.browse(self.current_user, self.current_path)
        for it in items:
            name = it["name"] + "/" if it["is_dir"] else it["name"]
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, it)
            self.file_list.addItem(item)

    def on_file_selected(self, item):
        info = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if info["is_dir"]:
            self.current_path = info["name"] if self.current_path == "." else f"{self.current_path}/{info['name']}"
            self.path_label.setText(f"📁 Путь: {self.current_path}")
            self.load_files()
            self.text_edit.clear()
            return

        filename = info["name"] if self.current_path == "." else f"{self.current_path}/{info['name']}"
        data = self.fs.read(filename, self.current_user)
        if data is None:
            self.text_edit.setPlainText("❌ Нет доступа к файлу")
        else:
            self.text_edit.setPlainText(data)
            self.animate_content()

    def on_create_clicked(self):
        filename, ok = QtWidgets.QInputDialog.getText(self, "➕ Создать файл", "Имя файла:")
        if not ok or not filename.strip():
            return
        filename = filename.strip()

        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "➕ Создать файл", "Содержимое:", "")
        if not ok:
            return

        full_name = filename if self.current_path == "." else f"{self.current_path}/{filename}"
        if self.fs.create(full_name, text, self.current_user):
            self.load_files()
        else:
            QtWidgets.QMessageBox.warning(self, "❌ Ошибка", "Не удалось создать файл!")

    def on_edit_clicked(self):
        item = self.file_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(self, "ℹ️", "Выберите файл!")
            return

        info = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if info["is_dir"]:
            QtWidgets.QMessageBox.information(self, "ℹ️", "Нельзя редактировать папку!")
            return

        filename = info["name"] if self.current_path == "." else f"{self.current_path}/{info['name']}"
        old_data = self.fs.read(filename, self.current_user) or ""

        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "✏️ Редактировать", f"Файл: {filename}", old_data)
        if ok and self.fs.update(filename, text, self.current_user):
            self.text_edit.setPlainText(text)
            self.animate_content()
        else:
            QtWidgets.QMessageBox.warning(self, "❌ Ошибка", "Не удалось сохранить!")

    def on_delete_clicked(self):
        item = self.file_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.information(self, "ℹ️", "Выберите файл!")
            return

        info = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if info["is_dir"]:
            QtWidgets.QMessageBox.information(self, "ℹ️", "Удаление папок пока не поддерживается!")
            return

        filename = info["name"] if self.current_path == "." else f"{self.current_path}/{info['name']}"
        res = QtWidgets.QMessageBox.question(self, "⚠️ Удалить?", f"Удалить файл '{filename}'?")
        if res == QtWidgets.QMessageBox.StandardButton.Yes:
            if self.fs.delete(filename, self.current_user):
                self.load_files()
                self.text_edit.clear()
            else:
                QtWidgets.QMessageBox.warning(self, "❌ Ошибка", "Не удалось удалить файл!")


def main():
    global USERS_DB
    USERS_DB = load_users()
    
    app = QtWidgets.QApplication(sys.argv)

    while True:
        login_dialog = LoginDialog()
        if login_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            sys.exit(0)

        login, password = login_dialog.get_credentials()

        if login == "guest":
            win = FileSystemWindow("guest")
            win.show()
            sys.exit(app.exec())
        elif login in USERS_DB and USERS_DB[login] == password:
            if login == "admin":
                win = AdminPanel()
            else:
                win = FileSystemWindow(login)
            win.show()
            sys.exit(app.exec())
        else:
            QtWidgets.QMessageBox.warning(None, "❌ Ошибка", "Неверный логин или пароль!")

if __name__ == "__main__":
    main()
