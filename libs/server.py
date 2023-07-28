import os 
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.parse import unquote


if __name__ == "__main__":
    from acestream_search import main, get_options, sav    
    config = {}
else:
    from dotenv import dotenv_values
    from libs.acestream_search import main, get_options, sav  
    config = dotenv_values(".env")
    
from socketserver import ThreadingMixIn


m3u_dir = config.get('path_dir', os.path.join(os.path.dirname(__file__).replace('\\'.join(os.path.dirname(__file__).split('\\')[len(os.path.dirname(__file__).split('\\'))-1:]),''),'playlists'))

class HttpGetHandler(BaseHTTPRequestHandler):
    """Обработчик с реализованным методом do_GET."""
    def _set_headers(self, type_c):
        self.send_response(200)
        self.send_header('Content-type', type_c)
        self.end_headers()

    def m3u_exists(self, filename):
        f_m3u = os.path.join(m3u_dir, filename)
        if os.path.isfile(f_m3u):
            file = open(f_m3u, 'r', encoding='utf-8')
            lines = len(file.readlines())
            file.close()
            return {'f_m3u': f_m3u, 'valid':True, 'lines': lines}
        else:
            return {'f_m3u': f_m3u, 'valid':False, 'lines': 0}

    def read_file(self, filename):
        out = ''
        with open(filename, mode = 'r', encoding='utf-8') as f:
            for line in f:
                out+=line
        return out

    def save_file(self, filename, data , m = 'a'):
        with open(filename, mode = m, encoding='utf-8') as f:
            f.write(data)

    def get_path(self, uripath, u_dict={}, err_dict={}):
        end_dic = {} #{'group_by_channels':1,'show_epg':1} # default settings
        end_dic.update(u_dict)

        if self.path.find("?")>-1 and self.path.find("=")>-1:
            try:
                split_and = self.path[len(uripath)+2:].split("&")
                user_dict_params = {}
                
                if len(split_and):
                    for val in split_and:
                        name, znach = val.split("=")
                        if len(name)<=0:
                            continue
                        
                        user_dict_params[name] = int(znach) if znach.isdigit() else unquote(znach)
                        
                end_dic.update(user_dict_params)
                
            except:
                pass
        else:
            end_dic.update(err_dict)
        
        return end_dic

    def playlist(self):
        args = self.get_path(uripath='playlist.m3u', u_dict={'group_by_channels':1,'show_epg':1}, err_dict={'category':'movies'}) # u_dict default settings
        txt = ""
        try:
            argi = get_options(args)
            for chunk in main(argi):
                txt += chunk
            if argi.file_name:
                sav(txt, argi.file_name)
                
        except:
            txt = f"Ace Engine не запущен или ошибка в коде..."
        self.wfile.write(txt.encode())

    def files_m3u(self):
        file_m3u_path = self.path[len('files.m3u')+2:]
        name, znach = file_m3u_path.split("=")
        self.films(filename=znach)
             

    def films(self, filename ='films.m3u'):
        f_m3u, valid, lines = self.m3u_exists(filename).values()
        if valid:
            if lines == 0:
                self.wfile.write(f'File "{filename}" found, but he is empty!'.encode())
            else:
                self.wfile.write(self.read_file(f_m3u).encode())                
        else:   
            self.wfile.write(f'File not found from "{f_m3u}" check path!'.encode())

    def remove_m3u(self, filename=None):

        if filename is None:
            p = self.path[len('remove_m3u')+2:]
            name, znach= p.split('=')

            if not znach:
                self.wfile.write(f'<p>File {filename} not found!</p><p><a href="/">Go to home</a></p>'.encode())
                return

            filename = znach            

        file_m3u = os.path.join(m3u_dir, filename)

        if os.path.exists(file_m3u):
            os.remove(file_m3u)
            self.wfile.write(f'<p>File {filename} removed!</p><p><a href="/">Go to home</a></p>'.encode())

    def get_all_list(self):
        m3udir = m3u_dir
        return os.listdir(m3udir)
    
    def index(self):
        list_m3u = self.get_all_list()
        m3uhtml = ''
        if len(list_m3u):
            list_ul = ''.join([f"""
<li>
<a href='http://localhost:8000/files.m3u?file={l}'>{l}</a>
<span style='color:white;background: red; font-weight:bold;;cursor:pointer; padding: 2px; margin-left: 10px;font-size: 0.6rem;' title='Remove file: {l}' onclick='removeFile("{l}");'>X</span>
</li>
""" for l in list_m3u])
            m3uhtml = f'<div class="list_m3u"><h3>List m3u files on server:</h3><ol>{list_ul}</ol></div>'

        script = '''
        <script>
        function removeFile(file){
            if(confirm(`You want delete ${file}?`)){
                location.href = `/remove_m3u?=${file}`
            }
        }
        </script>
'''
        
        self.wfile.write(f'''
<!doctype html>
<html>
    <header>
        <title>Main Page</title>
        {script}
    </header>
    <body>
    <h3>Main menu:</h3>
        <ul>
            <li><a href="/index">Домой</a></li>
            <li><a href="/playlist.m3u">Ace TV Torrent</a></li>
            <li>
                <ul>
                <li><b>Commands request list:</b></li>
                <li><b>Example:</b> <a target="__blank" href="http://localhost:8000/playlist.m3u?target=192.168.1.2:6878&file_name=tv_list.m3u&category=movies">http://localhost:8000/playlist.m3u?target=192.168.1.2:6878&file_name=tv_list.m3u&category=movies</a></li>
                <li><b>query</b> - Pattern to search tv channels. [String]</li>
                <li><b>quiet</b> - increase output quiet. [Boolean]</li>
                <li><b>name</b> - Exact tv channels to search for, doesn't effect json output. [str]</li>
                <li><b>category</b> - filter by category.</li>
                <li><b>proxy</b> - proxy host:port to conntect to engine api.</li>
                <li><b>targe</b>t - target host:port to conntect to engine hls.</li>
                <li><b>page_size</b> - page size (max 200).</li>
                <li><b>group_by_channels</b> - group output results by channel.</li>
                <li><b>show_epg</b> - include EPG in the response.</li>
                <li><b>json</b> - json output.</li>
                <li><b>html</b> - html output.</li>
                <li><b>xml_epg</b> - make XML EPG.</li>
                <li><b>debug</b> - debug mode.</li>
                <li><b>file_name</b> - file name save [folder playlists]</li>
                <li><b>url</b> - output single bare url of the stream instead of playlist</li>
                <li><b>after</b> - availability updated at.</li>
                <li><b>version</b> - Show version number.</li>
                </ul>
            </li>
            <li>------</li>
            <li><a href="/playlist.m3u?html=1">AceStream TV HTML</a></li>
            <li>------</li>
            <li><a href="/films.m3u">Films Torrent</a></li>
            <li><a href="/torrserv.m3u">TorrServ List</a></li>
            <li><a href="/frame?path_vid=&name_vid=">TorrServ return video</a></li>            
        </ul>
        <hr>
        {m3uhtml}
    </body>
</html>'''.encode())

    def frame(self):
        uri = self.get_path(uripath='frame')
        path_vid = uri.get('path_vid')
        name_vid = uri.get('name_vid')
        index_vid = uri.get('index_vid', 1)

        if path_vid == '':
            path_vid = None
            
        if name_vid == '':
            path_vid = None
            
        if not path_vid and not name_vid:            
            
            self.wfile.write(f'''
<!doctype html>
<html>
    <head>
        <style>
        * {{
            padding:0;
            margin:0;
        }}
        </style>
    </head>
    <body>
        <h3>NOT CORRECT REQUEST: Not valid 'path_vid' = '{path_vid}' or 'name_vid' = '{name_vid}'!</h3>
    </body>
</html>'''.encode())
        else:

            path_vid = unquote(path_vid)
            name_vid = unquote(name_vid)
            
            #link_tor = f'http://localhost:8090/stream/{path_vid}?link={hash_vid}&index={index_vid}&play'
            link_tor = f'{path_vid}&index={index_vid}&play'

            source = ''
            if name_vid.endswith('.mp3') or name_vid.endswith('.ogg'):
                source = f'<source src="{link_tor}" type="audio/mp3" />'
                
            elif name_vid.endswith('.m3u8'):
                source = f'<source src="{link_tor}" type="application/x-mpegURL" />'
                
            else:
                source = f'<source src="{link_tor}" type="video/mp4" />'

            jscode = '''
            const player = videojs('media_tor', {
              controls: true,
              autoplay: true,
              preload: 'auto',
              muted: true,
              //fluid: true,
              //fill: true
              aspectRatio: '16:9',
              responsive: true,
            })

            /*player.ready(function() {
                this.play()
                setTimeout(function(){
                    player.muted(false)
                    this.play()
                }, 5000)                
            });*/
'''

            codeHTML = f'''
<!doctype html>
<html>
    <head>
        <style>
        * {{
            padding:0;
            margin:0;
        }}
        </style>
        <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
    </head>
    <body>
        <video-js id="media_tor">
            {source}
            <p class="vjs-no-js">
            To view this video or audio please enable JavaScript, and consider upgrading to a web browser that
            <a href="https://videojs.com/html5-video-support/" target="_blank">supports HTML5 video or video</a>
            </p>
        </video-js>
        
        <script src="https://vjs.zencdn.net/7.20.3/video.min.js" type="text/javascript"></script>

        <script>{jscode}</script>
    </body>
</html>'''
            
            self.wfile.write(codeHTML.encode())
        

    def torrserv_m3u(self):
        torrserv_path =  self.get_path(uripath='torrserv.m3u')

        if 'link' not in torrserv_path:
             self.wfile.write(f'''Request not yet params "link"!
Support params:
link - link torrent.
name - name list item

Adv. options:
pls - work from playlist file
---> op - operations = add or cls (work only with "pls")'''.encode())

             return

        f_m3u, valid, lines = self.m3u_exists('torrserv_list.m3u').values()

        m3u_ = f'''#EXTINF:-1, {torrserv_path.get('name','Noname')} - TorrServ
http://{config.get('ip','localhost')}:{config.get('port_torrserv','8090')}/stream/fname?link={torrserv_path['link']}&index=1&play\n'''
        
        if 'pls' in torrserv_path:
            if valid:
                
                if 'op' in torrserv_path:
                    if torrserv_path['op']=='cls':
                        m3u_ = '#EXTM3U\n'+m3u_
                        mode = 'w'
                    elif torrserv_path['op']=='add':
                        mode = 'a'
                    else:
                        mode = 'a'

                    self.save_file(filename=f_m3u, data=m3u_, m = mode)                               

            else:         
                m3u_ = '#EXTM3U\n'+m3u_
                self.save_file(filename=f_m3u, data=m3u_)
                
                
            self.films('torrserv_list.m3u')
        else:
            m3u_ = '#EXTM3U\n'+m3u_
            self.wfile.write(m3u_.encode())
        
    def do_GET(self):
        self.send_response(200)
        
        if self.path == '/index' or self.path == '/':
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.index()

        if self.path.find('/frame')>-1:
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.frame()
            
        elif self.path.find('/playlist.m3u')>-1:
            self.send_header('Content-type', 'text/html; charset=utf-8' if self.path.find('/playlist.m3u?html=1')>-1 else 'text/plain; charset=utf-8')
            self.end_headers()
            self.playlist()
            
##        elif self.path == '/films.m3u':
##            # audio/x-mpequrl
##            self.send_header('Content-type', 'text/plain; charset=utf-8')
##            self.end_headers()
##            self.films()
            
        elif self.path.find('/files.m3u')>-1:
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.files_m3u()

        elif self.path.find('/torrserv.m3u')>-1:
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.torrserv_m3u()

        elif self.path.find('/remove_m3u')>-1:
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.remove_m3u()
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run_deamon(server_class=ThreadedHTTPServer, handler_class=BaseHTTPRequestHandler):
  server_address = ('', 8000)
  ip_port = ':'.join(['localhost' if x=='' else str(x) for x in server_address])
  httpd = server_class(server_address, handler_class)
  try:
      print(f'''Server запущен!\nРаботает на: {ip_port}''')
      httpd.serve_forever()
  except KeyboardInterrupt:
      httpd.server_close()
      

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
  server_address = ('', 8000)
  httpd = server_class(server_address, handler_class)
  try:
      ip_port = ':'.join(['localhost' if x=='' else str(x) for x in server_address])
      print(f'''Server запущен!\nРаботает на: {ip_port}''')
      httpd.serve_forever()
  except KeyboardInterrupt:
      httpd.server_close()

if __name__ == "__main__":
    run(handler_class=HttpGetHandler)
