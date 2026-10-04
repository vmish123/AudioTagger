import os
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.id3 import TIT2, TPE1, TALB, TDRC, APIC
from mutagen.flac import Picture


class AudioTagEditor:
    """Управление метаданными аудиофайлов. Чтение и запись тегов."""

    # Извлечение метаданных (тегов и обложки) из аудиофайла
    def read_tags(self, file_path: str) -> dict:
        # Проверка существования файла на диске
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден.")

        # Инициализация словаря для хранения извлеченных данных
        tags_data = {
            'title': '',
            'artist': '',
            'album': '',
            'year': 0,
            'cover_data': None
        }

        try:
            # Определение формата аудиофайла
            audio = mutagen.File(file_path)
            if audio is None:
                return tags_data

            # Обработка формата MP3
            if isinstance(audio, MP3) and audio.tags:
                # Извлечение полей
                if 'TIT2' in audio.tags:
                    tags_data['title'] = str(audio.tags['TIT2'].text[0])
                if 'TPE1' in audio.tags:
                    tags_data['artist'] = str(audio.tags['TPE1'].text[0])
                if 'TALB' in audio.tags:
                    tags_data['album'] = str(audio.tags['TALB'].text[0])

                # Извлечение года (с учетом разных версий ID3)
                if 'TDRC' in audio.tags:
                    tags_data['year'] = int(str(audio.tags['TDRC'].text[0])[:4])
                elif 'TYER' in audio.tags:
                    tags_data['year'] = int(str(audio.tags['TYER'].text[0]))

                # Поиск и извлечение обложки альбома
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        tags_data['cover_data'] = getattr(tag, 'data', None)
                        break

            # Обработка формата FLAC
            elif isinstance(audio, FLAC) and audio.tags:
                # Извлечение полей
                tags_data['title'] = audio.tags.get('title', [''])[0]
                tags_data['artist'] = audio.tags.get('artist', [''])[0]
                tags_data['album'] = audio.tags.get('album', [''])[0]

                # Извлечение года
                date_str = audio.tags.get('date', [''])[0]
                if date_str:
                    tags_data['year'] = int(date_str[:4])

                # Извлечение обложки альбома
                if audio.pictures:
                    tags_data['cover_data'] = audio.pictures[0].data

        # Перехват и логирование ошибок чтения
        except Exception as exception:
            print(f"Ошибка при чтении тегов {file_path}: {exception}")

        return tags_data

    # Сохранение измененных метаданных (тегов и обложки) в аудиофайл
    def write_tags(self, file_path: str, new_tags: dict) -> bool:
        try:
            # Определение формата аудиофайла
            audio = mutagen.File(file_path)
            if audio is None:
                return False

            # Запись тегов для формата MP3
            if isinstance(audio, MP3):
                # Создание пустой структуры тегов при ее отсутствии
                if audio.tags is None:
                    audio.add_tags()

                # Обновление полей
                if 'title' in new_tags:
                    audio.tags.add(TIT2(encoding=3, text=new_tags['title']))
                if 'artist' in new_tags:
                    audio.tags.add(TPE1(encoding=3, text=new_tags['artist']))
                if 'album' in new_tags:
                    audio.tags.add(TALB(encoding=3, text=new_tags['album']))
                if 'year' in new_tags:
                    audio.tags.add(TDRC(encoding=3, text=str(new_tags['year'])))

                # Сохранение новой обложки
                if 'cover_data' in new_tags and new_tags['cover_data']:
                    # Определение MIME-типа изображения
                    mime = 'image/png' if new_tags['cover_data'].startswith(b'\x89PNG') else 'image/jpeg'

                    # Удаление старых обложек
                    audio.tags.delall('APIC')

                    # Добавление нового изображения
                    audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=new_tags['cover_data']))

            # Запись тегов для формата FLAC
            elif isinstance(audio, FLAC):
                # Создание пустой структуры тегов при ее отсутствии
                if audio.tags is None:
                    audio.add_tags()

                # Обновление полей
                if 'title' in new_tags:
                    audio.tags['title'] = new_tags['title']
                if 'artist' in new_tags:
                    audio.tags['artist'] = new_tags['artist']
                if 'album' in new_tags:
                    audio.tags['album'] = new_tags['album']
                if 'year' in new_tags:
                    audio.tags['date'] = str(new_tags['year'])

                # Сохранение новой обложки
                if 'cover_data' in new_tags and new_tags['cover_data']:
                    # Определение MIME-типа изображения
                    mime = 'image/png' if new_tags['cover_data'].startswith(b'\x89PNG') else 'image/jpeg'

                    # Формирование объекта изображения
                    pic = Picture()
                    pic.type = 3
                    pic.mime = mime
                    pic.desc = "Front Cover"
                    pic.data = new_tags['cover_data']

                    # Удаление старых изображений и добавление нового
                    audio.clear_pictures()
                    audio.add_picture(pic)

            # Физическое сохранение изменений в файл
            if isinstance(audio, MP3):
                audio.save(v2_version=3)
            else:
                audio.save()

            return True

        except PermissionError:
            # Перехват ошибки системной блокировки файла
            print(f"Файл {file_path} заблокирован другим процессом.")
            return False

        except Exception as exception:
            # Перехват прочих ошибок сохранения
            print(f"Ошибка при сохранении тегов в {file_path}: {exception}")

            return False

    # Получение длительности аудиофайла в миллисекундах
    def get_audio_duration(self, file_path: str) -> int:
        try:
            # Извлечение информации о файле и вычисление длительности
            audio = mutagen.File(file_path)
            if audio and hasattr(audio.info, 'length'):
                return int(audio.info.length * 1000)
            return 0
        except Exception:
            return 0
