import json
import pathlib
from typing import Optional, Dict, Any, List


class ProFileSystem:
    """
    Простейшая файловая система для учебной ОС:
    - реальные файлы лежат в data/<user>/...
    - метаданные в data/fs_meta.json
    - поддерживает: create, read, update, delete, browse
    """

    def __init__(self, data_dir: str = "data", meta_file: str = "fs_meta.json"):
        self.data_dir = pathlib.Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.meta_path = self.data_dir / meta_file
        # user_files[owner][filename] = {...meta...}
        self.user_files: Dict[str, Dict[str, Any]] = {}

        self.load_metadata()

    # ============ ВНУТРЕННИЕ МЕТОДЫ ============

    def load_metadata(self) -> None:
        """Загрузка метаданных из JSON."""
        if not self.meta_path.exists():
            self.user_files = {}
            return

        try:
            data = self.meta_path.read_text(encoding="utf-8")
            # Если файл пустой
            if not data.strip():
                self.user_files = {}
                return
            self.user_files = json.loads(data)
        except Exception as e:
            print(f"❌ Ошибка загрузки метаданных: {e}")
            self.user_files = {}

    def save_metadata(self) -> None:
        """Сохранение метаданных в JSON."""
        try:
            self.meta_path.write_text(
                json.dumps(self.user_files, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"❌ Ошибка сохранения метаданных: {e}")

    def _get_file_record(self, user: str, filename: str) -> Optional[Dict[str, Any]]:
        """Получить запись о файле из метаданных."""
        return self.user_files.get(user, {}).get(filename)

    def _normalize_filename(self, filename: str) -> str:
        """Простейшая защита: запрет выхода за корень (..)."""
        # Можно усложнить, пока только простая проверка
        if ".." in pathlib.PurePosixPath(filename).parts:
            raise ValueError("Недопустимый путь (содержит '..')")
        return filename

    # ============ ПУБЛИЧНЫЕ ОПЕРАЦИИ ============

    def create(self, filename: str, content: str, owner: str, readonly: bool = False) -> bool:
        """
        Создает реальный файл + метаданные.
        filename может содержать подкаталоги: 'docs/test.txt'
        """
        try:
            filename = self._normalize_filename(filename)
        except ValueError as e:
            print(f"❌ {e}")
            return False

        file_path = self.data_dir / owner / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            file_path.write_text(content, encoding="utf-8")
            stat = file_path.stat()
            self.user_files.setdefault(owner, {})[filename] = {
                "path": str(file_path),
                "size": len(content),
                "created": stat.st_mtime,
                "modified": stat.st_mtime,
                "owner": owner,
                "readonly": readonly,
                # В будущем можно добавить список разрешённых читателей:
                # "allowed_readers": [owner]
            }
            self.save_metadata()
            return True
        except Exception as e:
            print(f"❌ Ошибка создания файла: {e}")
            return False

    def read(self, filename: str, user: str) -> Optional[str]:
        """
        Читает файл с проверкой прав.
        Пока что: читать может только владелец (user == owner).
        """
        # На будущее: можно сделать глобальный поиск по всем владельцам,
        # если файл расшаривается. Сейчас жёстко по владельцу.
        record = self._get_file_record(user, filename)
        if not record:
            return None

        file_path = pathlib.Path(record["path"])
        if not file_path.exists():
            return None

        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return None

    def update(self, filename: str, new_content: str, user: str) -> bool:
        """
        Перезаписывает содержимое файла.
        Разрешено только владельцу и только если файл не readonly.
        """
        record = self._get_file_record(user, filename)
        if not record:
            return False

        if record.get("readonly"):
            print("❌ Файл только для чтения")
            return False

        file_path = pathlib.Path(record["path"])
        if not file_path.exists():
            return False

        try:
            file_path.write_text(new_content, encoding="utf-8")
            stat = file_path.stat()
            record["size"] = len(new_content)
            record["modified"] = stat.st_mtime
            self.save_metadata()
            return True
        except Exception as e:
            print(f"❌ Ошибка обновления файла: {e}")
            return False

    def browse(self, user: str, path: str = ".") -> List[Dict[str, Any]]:
        """
        Обзор файловой системы пользователя.
        path относительно корня пользователя: '.', 'docs', 'docs/subdir'.
        """
        try:
            path = self._normalize_filename(path)
        except ValueError as e:
            print(f"❌ {e}")
            return []

        base_path = self.data_dir / user / path
        if not base_path.exists():
            return []

        items: List[Dict[str, Any]] = []
        try:
            for item in base_path.iterdir():
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime,
                })
        except Exception as e:
            print(f"❌ Ошибка при обзоре каталога: {e}")
            return []

        return items

    def delete(self, filename: str, user: str) -> bool:
        """
        Удаление файла.
        Разрешено только владельцу, readonly не даёт удалить.
        """
        record = self._get_file_record(user, filename)
        if not record:
            return False

        if record.get("readonly"):
            print("❌ Нельзя удалить файл только для чтения")
            return False

        file_path = pathlib.Path(record["path"])
        try:
            if file_path.exists():
                file_path.unlink()

            # Удаляем запись из метаданных
            del self.user_files[user][filename]
            if not self.user_files[user]:
                # Если у пользователя больше нет файлов — убираем ключ
                del self.user_files[user]

            self.save_metadata()
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления файла: {e}")
            return False

    # ===== Дополнительно: проверка существования =====

    def exists(self, filename: str, user: str) -> bool:
        """Проверка, что файл есть и в метаданных, и на диске."""
        record = self._get_file_record(user, filename)
        if not record:
            return False
        return pathlib.Path(record["path"]).exists()
