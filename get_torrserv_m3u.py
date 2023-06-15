#!/usr/bin/python
#
# Title: Generate m3u playlists from TorrServer & Ace Player
# Author: AlekPet
# License: MIT
# Version: 2022_06_14


import os
import requests
import json
import re
from urllib.parse import quote
import subprocess
import psutil
from dotenv import dotenv_values
from libs import server
from colorama import init, Back, Fore, Style

# --- colorama init
init(convert=True,autoreset=True)

config = dotenv_values(".env")

formatVideo = ('.avi','.mkv','.mp4')

mState = {
    'answer': Fore.YELLOW+Style.BRIGHT,
    'error': Fore.RED+Style.BRIGHT,
    'normal': Fore.GREEN+Style.BRIGHT,
    'focus': Fore.MAGENTA+Style.BRIGHT,
    'warning': Fore.CYAN+Style.BRIGHT
    }

# --- Variables
formatVideo = ('.avi','.mkv','.mp4')

regEmpty = re.compile('^\s*$', re.I | re.IGNORECASE)

ip = config.get('ip','localhost')
port_torrserv=config.get('port_torrserv','8090')
#serv_pid = None

port_ace = config.get('port_ace','6878')

fileName = config.get('fileName','torrserv_list.m3u')
txt_torrserv = config.get('txt_torrserv','torrserv.txt')
path_dir = config.get('path_dir',os.path.join(os.path.dirname(__file__),'playlists'))
save_path = os.path.join(path_dir,fileName)
max_out_title = int(config.get('max_out_title',70))


mState = {
    'answer': Fore.YELLOW+Style.BRIGHT,
    'error': Fore.RED+Style.BRIGHT,
    'normal': Fore.GREEN+Style.BRIGHT,
    'focus': Fore.MAGENTA+Style.BRIGHT,
    'warning': Fore.CYAN+Style.BRIGHT
    }

### AceStream
defaultAce = [
    {'torrent': f'http://{ip}:{port_ace}/playlist/eW5KVGn.m3u', 'title': 'Ace Playlist', 'group': 'm3u', 'userSet': True},
    ]
# --/ Variables

def procRun(name):
    'Check process is rinning'
    return name in (proc.name() for proc in psutil.process_iter())

def httpTorCheck(tor_link):
    'Check torlink http...'
    if tor_link.find('http')!=-1:
        return True
    return False

def readAceTxt(filetxt='ace.txt' , newline=True, log=True):
    file_txt = os.path.join(path_dir,filetxt)
    list_tor = []
    nonameCount = 1
    
    if os.path.isfile(file_txt):
        print()
        
        if log:
            print(mState['normal']+"Читаю файл: "+filetxt)
            
        with open(file_txt, encoding='utf-8') as file:
            lines = file.readlines()

            if not len(lines):
                print(mState['warning']+f"Файл {filetxt} пустой...")
                return list_tor
            
            for line in lines:
                line_read = line

                if newline:
                    line_read = line.rstrip('\n')

                if bool(regEmpty.search(line_read)):
                    continue
                
                line_read = line.split(sep=',')
                line_read = list(map(str.strip, line_read))
                
                if isinstance(line_read, (list,tuple)):
                    
                    torr = None
                    name = None
                    
                    if len(line_read) ==  2:
                        torr, name = line_read
                        
                        if not httpTorCheck(torr):
                            continue
                        
                        if bool(regEmpty.search(name)):
                            name = f'NoName Torrent {nonameCount}'
                            nonameCount+=1
                             
                    else:
                        if httpTorCheck(line_read[0]):
                            if log:
                                print(mState['warning']+f'Найдена ссылка, но нет названия! В тексте `{line_read[0]}`')
                                
                            torr = line_read[0]
                            name = f'NoName Torrent {nonameCount}'
                            nonameCount+=1
                        else:
                            if log:
                                print(mState['warning']+f'Нет торрента, только текст или пусто! В тексте `{line_read[0]}`\n')
                            continue

                    if torr != None and name != None:
                        tor_dict = {'torrent': torr, 'title': name, 'tor_down': line_read}
                        list_tor.append(tor_dict)
    else:
        print(mState['warning']+f"Файл `{filetxt}` не найден возвращаем только плейлист...\n")

    if filetxt.find('ace')!=-1:
        list_tor.extend(defaultAce)

    len_torr_file = len(list_tor)
    if(len_torr_file):
        print(mState['warning']+f"Найдео торрентов в файле: {len_torr_file}")
        for k,l in enumerate(list_tor):
            print(mState['answer']+f"{k+1}. {l.get('title')} [torrent: {l.get('torrent')}]")
        
    return list_tor

### TorrServ
def removeTorrentTS(hashi):
    #{"action":"rem","hash":"120c6a1e143190b4fd73ef381331c88f972eeb91"}
    if hashi:
        url_save_torrServ =  f'http://{ip}:{port_torrserv}/torrents'
        req = requests.post(url_save_torrServ, json={'action': 'rem', 'hash': hashi})
        
        if req.status_code == 200:
            print(mState['answer']+"Торрент был успешно удален!")
        else:
            print(mState['error']+"Торрент удалить не удалось, неверный хеш или торрент уже был удален!")

def removeFromTxt(file_txt, danie):
    file_txt = os.path.join(path_dir, file_txt)
    
    if os.path.isfile(file_txt):
        line_read_copy = None
        
        try:        
            file_orig = open(file_txt, 'r', encoding='utf-8')
            line_read = file_orig.readlines()
            line_read_copy = line_read[:]
            file_orig.close()

            file_new = open(file_txt, 'w', encoding='utf-8')
            for line in line_read:
                if line.strip('\n') != danie:
                    file_new.write(line)     
            
            file_orig.close()
            print(mState['answer']+f'[Удаление из файла]: Строка > {danie} < была удалена из файла {file_txt} !\n')
        
        except Exception as e:
            print(mState['error']+"Ошибка удаления строки, восстанавливаю файл...")
            with open(file_txt, 'w', encoding='utf-8') as f:
                f.write(line_read_copy)
                  
        

def managerTorrServRemove():
    torrserv_file = readAceTxt(txt_torrserv, True, False)    
    txt_read_add = addTorrent_Torrserv(torrserv_file, '')
    
    rem_input = ''
    
    while rem_input!='e':

        print(mState['warning']+'''Меню удаления:
[Цифра] - цифра, торрент раздачи для удаления
[e] - Отмена
''')
        len_tor, response = getListTorrents()
        rem_input = input("Введите комманду: ")

        if rem_input == 'e':
            break

        if not rem_input.isdigit():
            print(mState['error']+'Неверный ввод данных!')
            continue
            
        rem_sel = int(rem_input)

        if rem_sel < 1 or rem_sel > len_tor:
            print(mState['error']+'Введеная цифра больше или меньше допустимой!')
            continue

        rem_sel = rem_sel -1
        sel_hashi, sel_title = response[rem_sel].get('hash', None), response[rem_sel].get('title', None)

        #print('Dev....')

        _remW = _remT = False

        # remove from web
        # resW = filter(lambda x: x.get('hash') == sel_hash, response)
        # resT = filter(lambda x: x.get('hash') == sel_hash, txt_read_add)
        # removeTorrentTS(resW[0])
        # removeFromTxt(txt_torrserv, resT.get('torrent'))
        
        for webtor in response:
            w_title = webtor.get('title')
            w_hashi = webtor.get('hash', None)

            if not w_hashi:
                print(mState['error']+'[Web] Хеш у {w_title} не найден!')
                continue

            if w_hashi == sel_hashi:
                _remW = True
                #print(f"WEB Удаляю {w_title} hash {w_hashi}")
                removeTorrentTS(w_hashi)

                # renove from txt
                for txt in txt_read_add:
                    txt_title =  txt.get('title')
                    txt_hash =  txt.get('hash')
                    txt_torrent =  txt.get('torrent')

                    if not w_hashi:
                        print(mState['error']+'[Txt] Хеш у {txt_title} не найден!')
                        continue

                    if txt_hash == w_hashi:
                        _remT = True
                        #print(f"TXT Удаляю {txt_title} hash {txt_hash} danie {txt_torrent}")
                        removeFromTxt(txt_torrserv, txt_torrent)


                outp = mState['focus']+f"Торрент {w_title} был удален из "
                if _remW and _remT:
                    outp+=f"TorrServer'a' и файла {txt_torrserv}"
                elif _remW and not _remT:
                    outp+="TorrServer'a'"                        
                elif _remT and not _remW:
                    outp+=f"файла {txt_torrserv}"
                else:
                    out = mState['focus']+"Торрент не был удален из-за отсутствия!"

                print(outp+'!\n')

            

def getData(res):
    data_out = []
    data = res.get('data')
    files = json.loads(data)
    files = files.get('TorrServer').get('Files')
    if len(files):
        for x in files:
            path = x.get('path')

            if path and path.endswith(formatVideo):
                id_file = x.get('id')
                file_name = quote(path[path.rfind('/')+1:])

                data_out.append({'id':id_file, 'file_name':file_name, 'group':'Movies'})
                
    return data_out

def runService(name, path):
    #global serv_pid
    try:


        if not path or not os.path.isfile(path):
            raise FileNotFoundError

        if not procRun(f'{name}.exe'):
            #process = subprocess.Popen(f'{path}',stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=0x08000000)
            #serv_pid = process.pid
            #for line in process.stdout:
            #   print(line)            
            os.chdir(path[:-len(f'{name}.exe')])
            os.startfile(path)
            print(mState['normal']+f'Сервер `{name}` был запущен!\n')
            return True
        else:
            print(mState['answer']+f'Сервер `{name}` уже запущен!\n')
            return True
            
    except FileNotFoundError:
        print(mState['error']+f"""Приложение {name} не найдено по следующему пути '{path}',
или не задано в файле .env !""")
        
    except Exception as e:
        print(e)

def addTorrent_Torrserv(data_dict, action = 'save'):
    try:
        print()

        action_not_save = action == 'save'
        torrents = []
        
        if action_not_save:
            print(mState['normal']+"Добавляю торренты в torrserv... ")

            
        for torr_data in data_dict:
            torrent, _, _ = torr_data.values()
            
            #if title.find("NoName Torrent") == -1:
            #    title =  f"&title={quote(title)}"
            #else:
            #    title = ""

            url_save_torrServ =  f'http://{ip}:{port_torrserv}/stream/fname?link={torrent}&{"save&" if action_not_save else action}stat' # http://127.0.0.1:8090/stream/fname?link=...&save&title=...&poster= | http://127.0.0.1:8090/stream/fname?link=...&stat

            req = requests.get(url_save_torrServ)
            
            if req.status_code != 200:
                print()
                print(mState['error']+f"!!! [${action}] Торрент файл '{torrent}' не удалось скачать, пропускаю и удаляю из файла... !!!")
                removeFromTxt(txt_torrserv, torrent)
                continue

            json_data = req.json()
            json_data.update({'torrent': torrent})
            
            if action_not_save:
                print(mState['focus']+'>> '+json_data.get('title')+' -> [Ok!]')
            else:
                torrents.append(json_data)

        print(mState['normal']+'Данные из текстового файла torrserv прочитаны и добавленны!\n')
        if not action_not_save:
            return torrents
        
    except Exception as e:
        return []

def getListTorrents():
    try:
        response = requests.post(f'http://{ip}:{port_torrserv}/torrents', json={'action': 'list'})
        response = response.json()

        len_res = len(response)

        if len_res>0:
            idx = 1
            for kei, k in enumerate(response):
                title = k.get('title')

                backCol = Back.MAGENTA if kei % 2 else Back.CYAN
                print(backCol+mState['answer']+f'{kei+1}. {title[:max_out_title]+"..." if len(title)>max_out_title else title}')

        print()

        return len_res, response
        
                
    except requests.ConnectionError as e:
        print(mState['error']+'Не удалось подключиться к TorrServer!\n')
        print(mState['answer']+'Запустить TorrServer?\n')
        if input('Введите: ') in ('yes','y', 1, '1', 'да', 'Да'):
            if runService('TorrServer', getEnv('torr_serv_path')):
                updatePLS()
            
        return 0, None

def getEnv(k):
    config = dotenv_values(".env")
    return config.get(k, None)

def updatePLS(save=True):
    try:
        response = requests.post(f'http://{ip}:{port_torrserv}/torrents', json={'action': 'list'})
        response = response.json()

        out = '#EXTM3U\n'
        action = 'play'

        idx = 1
        print(mState['answer']+"Раздачи в TorrServer: ")
        for key, k in enumerate(response):
            title = k.get('title')
            hash = k.get('hash')
            filesNames = getData(k)
            print(mState['warning'] + f"[{key+1}] {title}\n    Файлы с расширением {','.join(formatVideo)} [{len(filesNames)}]:")
            
            for kei, filename in enumerate(filesNames):
                title = filename.get('file_name') if len(filesNames)>1 else title
                file_name = filename.get('file_name')
                id_file = filename.get('id')
                group = filename.get('group', 'Ungroup')

                backCol = Back.MAGENTA if kei % 2 else Back.GREEN
                print(backCol+mState['answer'] + f'    {kei+1}. {title[:max_out_title]+"..." if len(title)>max_out_title else title}')
                
                out+=f'''#EXTINF:-1, {title} group-title="{group}", {title}
http://{ip}:{port_torrserv}/stream/{file_name}?link={hash}&index={id_file}&{action}
'''
            print()#tvg-name=""
                
        if save:
            # AceSream
            ace_stream = readAceTxt()
            for ace in ace_stream:
                group = ace.get('group', 'Ace File')
                torrent = ace.get('torrent')
                title =  ace.get('name')
                
                if not 'userSet' in ace:
                    torrent = f'http://{ip}:{port_ace}/ace/getstream?url={quote(torrent)}'
                                    

                out+=f'''#EXTINF:-1,{title} group-title="{group}", {title}
{torrent}
'''          
            # end - AceSream # tvg-name=""
            
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(out)
                
                print(mState['focus']+f'''Файл `{fileName}` успешно создан!!!
Путь к файлу: `{path_dir}` ...
                ''')        
                
    except requests.ConnectionError as e:
        
        print(mState['error']+'Не удалось подключиться к TorrServer!\n')
        print(mState['answer']+'Запустить TorrServer?\n')
        if input('Введите: ') in ('yes','y', 1, '1', 'да', 'Да'):
            if runService('TorrServer', getEnv('torr_serv_path')):
                updatePLS()


### end - TorrServ


def main(save=True):   
    cin = ''
    
    while cin != 'e':
        print(mState['normal']+'''
*** Работа с плейлистом ***
------- TorrServer -------
u - Обновить плейлист
l - Показать лист в torrserv
lr - Удалить торрент из TorrServer'a
r - Запустить TorrServer
rq - Завершить TorrServer
----------- Server -------
h - запустить htttp сервер
-------------------------
e - Завершить программу
''')
        cin = input('Введите: ').lower()
        
        if cin == 'u':
           torrserv_file = readAceTxt(filetxt=txt_torrserv)
           
           if len(torrserv_file):
               addTorrent_Torrserv(torrserv_file)

           else:
               print(mState['warning']+'Данные в текстовом файле torrserv отсутствуют!\n')                
           
           updatePLS()

        if cin == 'l':
            _, _ = getListTorrents()

        elif cin == 'lr':
            managerTorrServRemove()

        elif cin == 'r':
            if runService('TorrServer', getEnv('torr_serv_path')):

                print(mState['answer']+'Обновить плейлист?')    
                if input('Введите: ').lower() in ['y','1','да']:
                    updatePLS()

        elif cin == 'rq':
            if not procRun('TorrServer.exe'):
               print(mState['warning']+'TorrServer не работает!!\n')
               continue

            url_shutdown_torrServ =  f'http://{ip}:{port_torrserv}/shutdown'

            requests.get(url_shutdown_torrServ)
            print(mState['normal']+'{OK] Заверешен!!!\n')

            

                
        elif cin == 'h':
            server.run(handler_class=server.HttpGetHandler)
        else:
            print('\n'+mState['focus']+'Указана несуществующая комманда...!')
            
    print(mState['normal']+'Программа завершена!')


if __name__ == "__main__":
    main()
