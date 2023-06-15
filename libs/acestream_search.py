#from . import __version__
import os
#import _version as __version__
import json
from itertools import count
from datetime import datetime, timedelta
import argparse
import lxml.etree as ET

# workaround for python2 vs python3 compatibility
from urllib.request import urlopen, quote


# define default time slot for updated availability
def default_after():
    age = timedelta(days=7)
    now = datetime.now()
    return datetime.strftime(now - age, '%Y-%m-%d %H:%M:%S')


# transform date time to timestamp
def time_point(point):
    epoch = '1970-01-01 03:00:00'
    isof = '%Y-%m-%d %H:%M:%S'
    epoch = datetime.strptime(epoch, isof)
    try:
        point = datetime.strptime(point, isof)
    except ValueError:
        print("Use 'Y-m-d H:M:S' date time format, for example \'" +
              datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') +
              '\'')
        exit()
    else:
        return int((point - epoch).total_seconds())


# get command line options with all defaults set
def get_options(args={}):

    parser = argparse.ArgumentParser(
        description='Produce acestream m3u playlist, xml epg or json data.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog=args.get('prog', None)
    )

    parser.add_argument(
        'query',
        nargs='?',
        type=str,
        default='',
        help='Pattern to search tv channels.'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='increase output quiet.'
    )
    parser.add_argument(
        '-n', '--name',
        nargs='+',
        type=str,
        help="Exact tv channels to search for, doesn't effect json output."
    )
    parser.add_argument(
        '-c', '--category',
        type=str,
        default='',
        help='filter by category.'
    )
    parser.add_argument(
        '-p', '--proxy',
        type=str,
        default='localhost:6878',
        help='proxy host:port to conntect to engine api.'
    )
    parser.add_argument(
        '-t', '--target',
        type=str,
        default='localhost:6878',
        help='target host:port to conntect to engine hls.'
    )
    parser.add_argument(
        '-s', '--page_size',
        type=int, default=200,
        help='page size (max 200).'
    )
    parser.add_argument(
        '-g', '--group_by_channels',
        action='store_true',
        help='group output results by channel.'
    )
    parser.add_argument(
        '-e', '--show_epg',
        action='store_true',
        help='include EPG in the response.'
    )
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='json output.'
    )
    parser.add_argument(
        '-html', '--html',
        action='store_true',
        help='html output.'
    )
    parser.add_argument(
        '-x', '--xml_epg',
        action='store_true',
        help='make XML EPG.'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='debug mode.'
    )

    parser.add_argument(
        '-file', '--file_name',
        type=str,
        default='playlist.m3u',
        help='file name save'
    )
    
    parser.add_argument(
        '-u', '--url',
        action='store_true',
        help='output single bare url of the stream instead of playlist'
    )
    parser.add_argument(
        '-a', '--after',
        type=str,
        default=default_after(),
        help='availability updated at.'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s {0}'.format('1.0.0.0'),
        help='Show version number and exit.'
    )
    if __name__ == '__main__':
        opts = parser.parse_args()
    else:
        opts = parser.parse_known_args()[0]
    opts.__dict__.update(args)
    opts.after = time_point(opts.after)
    # They could be string or boolean, but should be integer
    if opts.show_epg:
        opts.show_epg = 1
        opts.group_by_channels = 1
    if opts.group_by_channels:
        opts.group_by_channels = 1
    # epg requires group by channels option being set
    if opts.xml_epg:
        opts.show_epg = 1
        opts.group_by_channels = 1
    if 'help' in args:
        opts.help = parser.format_help()
    if 'usage' in args:
        opts.usage = parser.format_usage()
    return opts


# api url
def endpoint(args):
    return 'http://' + args.proxy + '/server/api'


# authorization token
def get_token(args):
    query = 'method=get_api_access_token'
    try:
        body = urlopen(endpoint(args) + '?' + query).read().decode()
    except IOError:
        print('Couldn\'t connect to ' + endpoint(args))
        if args.debug:
            raise
        exit()
    else:
        try:
            response = json.loads(body)
        except ValueError:
            print('Couldn\'t get token from ' + endpoint(args) + '?' + query)
            if args.debug:
                print(body)
            exit()
        else:
            return response['result']['token']


# build request to api with all options set
def build_query(args, page):
    return 'token=' + get_token(args) + \
           '&method=search&page=' + str(page) + \
           '&query=' + quote(args.query) + \
           '&category=' + quote(args.category) + \
           '&page_size=' + str(args.page_size) + \
           '&group_by_channels=' + str(args.group_by_channels) + \
           '&show_epg=' + str(args.show_epg)


# fetch one page with json data
def fetch_page(args, query):
    url = endpoint(args) + '?' + query
    return json.loads(urlopen(url).read().decode('utf8'))


# compose m3u playlist from json data and options
name_unk = 1
def make_playlist(args, item, logo=None):
    global name_unk

    if item['availability_updated_at'] >= args.after \
            and (not args.name or item['name'].strip() in args.name):
        title = '#EXTINF:-1'
        if args.show_epg and 'channel_id' in item:
            title += ' tvg-id="' + str(item['channel_id']) + '"'


        name = item['name'].replace('Астрахань', 'Astragan')
        if name == '.':
            name = 'Без названия ' + str(name_unk)
            name_unk +=1
            
        title += ' tvg-name="' + name + '"'
        
        logo_past = ''
        if logo:
            logo_past = ' tvg-logo="' + logo + '"'

        categ = ''
        if 'categories' in item:
            category_items = set(';'.join((x.lower() if not x.find('|')!=-1 else ';'.join(x.split('|')).lower() for x in item['categories'] if len(x)>0)).split(';'))
            categ = ' group-title="' + ';'.join(category_items) + '"'

        if args.url:
            return ('http://' + args.target + '/ace/manifest.m3u8?infohash=' + item['infohash'])
        else:
        
            return (title + categ + logo_past + ', ' + name + '\n' + 'http://' + args.target + '/ace/manifest.m3u8?infohash=' + item['infohash'] + '\n')
    
##        if not args.quiet:
##            if 'categories' in item:
##                categories = ''
##                for kind in item['categories']:
##                    categories += ' ' + kind
##                    if item['categories'].index(kind) > 0:
##                        categories = ',' + categories
##                title += ' [' + categories + ' ]'
##
##            dt = datetime.fromtimestamp(item['availability_updated_at'])
##            title += ' ' + dt.isoformat(sep=' ')
##            title += ' a=' + str(item['availability'])
##            if 'bitrate' in item:
##                title += " b=" + str(item['bitrate'])
##                
##        if args.url:
##            return ('http://' + args.target + '/ace/manifest.m3u8?infohash=' +
##                    item['infohash'])
##        else:
##            return (title + '\n' +
##                    'http://' + args.target + '/ace/manifest.m3u8?infohash=' +
##                    item['infohash'] + '\n')

# html out
name_unk_html = 1
def make_html(args, item):
    global name_unk_html

    if item['availability_updated_at'] >= args.after \
            and (not args.name or item['name'].strip() in args.name):
        title = '<div class="boxtv">'
        if args.show_epg and 'channel_id' in item:
            title += f'<div>tvg-id: {str(item["channel_id"])}</div>'

        name = item['name']
        if name == '.':
            name = 'Без названия ' + str(name_unk_html)
            name_unk_html +=1
            
        title+= f'<div class="tvname">Name: {name}</div>'
 
        if not args.quiet:
            if 'categories' in item:
                categories = ''
                for kind in item['categories']:
                    categories += ' ' + kind
                    if item['categories'].index(kind) > 0:
                        categories = ' ' + categories
                title += f'<div>{categories}</div>'

            dt = datetime.fromtimestamp(item['availability_updated_at'])
            title += f'<div>{dt.isoformat(sep=" ")}</div><div>a={str(item["availability"])}</div>'
            
            if 'bitrate' in item:
                title += f"<div>bitrate: {str(item['bitrate'])}</div>"
        if args.url:
            return ('http://' + args.target + '/ace/manifest.m3u8?infohash=' +
                    item['infohash'])
        else:
            return (title + '<div><a href="' +
                    'http://' + args.target + '/ace/manifest.m3u8?infohash=' +
                    item['infohash'] + '">'+'http://' + args.target + '/ace/manifest.m3u8?infohash=' +
                    item['infohash']+'</a></div></div>')

# build xml epg
def make_epg(args, group):
    if 'epg' in group and (not args.name or group['name'] in args.name):
        start = datetime.fromtimestamp(
            int(group['epg']['start'])).strftime('%Y%m%d%H%M%S')
        stop = datetime.fromtimestamp(
            int(group['epg']['stop'])).strftime('%Y%m%d%H%M%S')
        channel_id = str(group['items'][0]['channel_id'])
        channel = ET.Element('channel')
        channel.set('id', channel_id)
        display = ET.SubElement(channel, 'display-name')
        display.set('lang', 'ru')
        display.text = group['name']
        if 'icon' in group:
            icon = ET.SubElement(channel, 'icon')
            icon.set('src', group['icon'])
        programme = ET.Element('programme')
        programme.set('start', start + ' +0300')
        programme.set('stop', stop + ' +0300')
        programme.set('channel', channel_id)
        title = ET.SubElement(programme, 'title')
        title.set('lang', 'ru')
        title.text = group['epg']['name']
        if 'description' in group['epg']:
            desc = ET.SubElement(programme, 'desc')
            desc.set('lang', 'ru')
            desc.text = group['epg']['description']
        xmlstr = ET.tostring(channel, encoding="unicode", pretty_print=True)
        xmlstr += ET.tostring(programme, encoding="unicode", pretty_print=True)
        return '  ' + xmlstr.replace('\n', '\n  ')


# channels stream generator
def get_channels(args):
    page = count()
    while True:
        query = build_query(args, next(page))
        chunk = fetch_page(args, query)['result']['results']

        if len(chunk) == 0 or not args.group_by_channels and  chunk[0]['availability_updated_at'] < args.after:
            break

        yield chunk


# iterate the channels generator
def convert_json(args):
 
    for channels in get_channels(args):
        #print(channels)
        # output raw json data
        if args.json:
            yield json.dumps(channels, ensure_ascii=False, indent=4)
        # output xml epg
        elif args.xml_epg:
            for group in channels:
                yield make_epg(args, group)
                
        # html playlist output
        elif args.html:
            html = ''
            if args.group_by_channels:
                for group in channels:
                    for item in group['items']:
                        match = make_html(args, item)
                        if match:
                            html += match
            else:
                for item in channels:
                    match = make_html(args, item)
                    if match:
                        # If option "url" set we need only single item.
                        if args.url:
                            yield match
                            # Break iteration as soon as first matching item found.
                            break
                        html += match
            if html:
                yield html.strip('<br>')
                
        # and finally main thing: m3u playlist output   
        else:
            m3u = ''
            if args.group_by_channels:
                for group in channels:
                    logo = None
                    
                    if 'icon' in group:
                        logo = group['icon']
                    
                    for item in group['items']:
                        match = make_playlist(args, item, logo)
                        if match:
                            m3u += match
            else:
                for item in channels:
                    logo = None

                    if 'icon' in item:
                        logo = item['icon']
                        
                    match = make_playlist(args, item, logo)
                    if match:
                        # If option "url" set we need only single item.
                        if args.url:
                            yield match
                            # Break iteration as soon as first matching item found.
                            break
                        m3u += match
            if m3u:
                yield m3u.strip('\n')


def iter_data(args):
    '''Iterate all data types according to options.'''
    if args.name:
        channels = args.name
        # set "query" to "name" to speed up handling
        for station in channels:
            args.query = station
            args.name = [station]
            yield convert_json(args)
    else:
        yield convert_json(args)


def pager(args):
    '''chunked output'''
    for page in iter_data(args):
        if page:
            for item in page:
                if item:
                    yield(item)


def main(args):
    '''Wrap all output with header and footer.'''
    if args.xml_epg:
        yield '<?xml version="1.0" encoding="utf-8" ?>\n<tv>'
    elif args.json:
        yield '['
    elif args.html:
        try:
            filter_keys = ['query','category','target','show_epg']
            params_set = [f'<b>{k}</b> = <i>{v}</i>' for k,v in vars(args).items() if k in filter_keys]
            params_set = '<br>'.join(params_set)
            head = '''<!doctype html>
            <html>
            <head>
            <meta charset=utf-8>
            <title>Ace TV List</title>
            <style>
            body{
            font: normal 10px monospace;
            }
            .boxtv{
            border: 1px solid black;
            margin: 2px;
            padding: 3px;
            word-break: all;
            }
            .boxtv:nth-of-type(odd){
            background: silver;
            }
            .tvname{
            font-weight: bold;
            color: blue;
            }
            .main_box {
            width: 60%;
            margin: 0 auto;
            }
            .main_box_info {
            border: 1px solid black;
            text-align: center;
            background: linear-gradient(0deg, #126493, #1769d3fa);
            color: white;
            font: 14px normal monospace;
            padding: 5px;
            }
            </style>
            </head>'''
            body = f'''<body>
            <div class="main_box">
            <div class="main_box_info">Info params: <br>{params_set}</div>
            <div class="main_box_channel">
            <'''
            head = head + body
            yield head
        except Exception as e:
            yield e
    elif not args.url:
        yield '#EXTM3U url-tvg="http://www.teleguide.info/download/new3/xmltv.xml.gz"\n'
        
    # make a correct json list of pages
    for page in pager(args):
        if args.json:
            page = page.strip('[]\n') + ','
        yield page
        
    if args.xml_epg:
        yield '</tv>'
    elif args.json:
        yield '    {\n    }\n]'
    elif args.html:
    	yield '''</div></div></body></html>'''

def sav(chunk,name='playlist.m3u'):
    with open(os.path.join(os.path.dirname(__file__).replace('libs',''),'playlists', name), mode='w+', encoding='utf-8') as f:
        f.write(chunk)

# command line function
def cli():
    if __name__ == '__main__':
        args = get_options({
            'show_epg': 1,
            'xml_epg':0,
            'group_by_channels':1,
            'category':'movies',
            #'target':'192.168.1.2:6878',
            #'query':'нтв',
            })
    else:
        args = get_options()
        
    out =""

    for chunk in main(args):
        out+=chunk

    sav(out, 'list_acetv.html' if args.html else args.file_name)

# run command line script
if __name__ == '__main__':
    cli()
