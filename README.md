# TorrAcePlaylists
Генерация плейлистов в формате m3u, для TorrServer (торрент файлы) и Ace Engine (торрент файлы и тв-передачи) и запуск http сервера для проигрывания плейлистов на других устройствах.

В данной программе использовался код из репозитория [acestream_search](https://github.com/vstavrinov/acestream_search/blob/master/acestream_search/acestream_search.py), для получения iptv плейлистов тв-каналов на основе Ace Engine.

# Install
1. Создайте среду выполнения [venv](https://docs.python.org/3/library/venv.html).
`python -m venv env`
2. Установить зависимости:
`pip install -r requirements.txt`
3. Изменить файл .env, для настройки параметров среды выполнения
```
// Содержимое файла .env
ip = введите свой ip адресс

port_torrserv = 8090 // Порт torrserver
port_ace = 6878 // Порт ace engine

torr_serv_path = E:\MediaTV\TheDarkSmartTVServer\TorrServer.exe // Путь к исполняющему файлу для запуска torrserver'а

fileName = torrserv_list.m3u
txt_torrserv = torrserv.txt
path_dir = .\playlists
max_out_title = 70
```
4. Запустить Server.cmd

