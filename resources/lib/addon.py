import re
import sys
import time
import json
import datetime

import routing
import xbmcgui
import xbmcvfs

from .helper import Helper

base_url = sys.argv[0]
handle = int(sys.argv[1])
helper = Helper(base_url, handle)
plugin = routing.Plugin()


@plugin.route('/')
def root():
    helper.add_item('Lista kanałów TV', plugin.url_for(live))
    helper.add_item('Program TV', plugin.url_for(epg_tv))
    helper.add_item('Archiwum', plugin.url_for(archive))
    helper.add_item('VOD GO', plugin.url_for(vod_go))
    helper.add_item('Szukaj', plugin.url_for(search))
    helper.add_item('Ustawienia', plugin.url_for(open_settings))
    helper.eod(cache=False)


@plugin.route('/live')
def live():
    channels_list = []
    program_tv = tvp_program()

    now = datetime.datetime.now()
    current_timestamp = int(now.timestamp())

    endpoint = '/api/tvp-stream/program-tv/stations'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)
    if response['data']:
        for data in response['data']:
            title = data['name']
            code = data['code']

            for epg in program_tv:
                if epg['station']['code'] == code:
                    if epg.get('items') is not None:
                        for item in epg['items']:
                            if int(item['date_start']) / 1000 < current_timestamp < int(item['date_end']) / 1000:
                                if item.get('program'):
                                    append = item['program']['title']
                                    title = title + ' - ' + f'[COLOR ff7f8c8d]{append}[/COLOR]'
                                    break

            image_height = str(data['image']['height'])
            image_width = str(data['image']['width'])
            image = data['image']['url'].replace('{width}', image_width).replace('{height}', image_height)
            fanart_height = str(data['image_square']['height'])
            fanart_width = str(data['image_square']['width'])
            fanart = data['image_square']['url'].replace('{width}', fanart_width).replace('{height}', fanart_height)

            info_label = {
                'title': title
            }

            images = {
                'icon': image,
                'fanart': fanart
            }

            channels_list.append({
                'title': data['name'],
                'id': code,
                'logo': image
            })

            helper.add_item(title, plugin.url_for(play_live, code=code), playable=True, info=info_label, art=images)
    helper.eod()

    return channels_list


@plugin.route('/epg_tv')
def epg_tv():
    program_tv = tvp_program()

    now = datetime.datetime.now()
    current_timestamp = int(now.timestamp())

    endpoint = '/api/tvp-stream/program-tv/stations'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)
    if response['data']:
        for data in response['data']:
            title = data['name']
            code = data['code']

            for epg in program_tv:
                if epg['station']['code'] == code:
                    if epg.get('items') is not None:
                        for item in epg['items']:
                            if int(item['date_start']) / 1000 < current_timestamp < int(item['date_end']) / 1000:
                                if item.get('program'):
                                    append = item['program']['title']
                                    title = title + ' - ' + f'[COLOR ff7f8c8d]{append}[/COLOR]'
                                    break

            image_height = str(data['image']['height'])
            image_width = str(data['image']['width'])
            image = data['image']['url'].replace('{width}', image_width).replace('{height}', image_height)
            fanart_height = str(data['image_square']['height'])
            fanart_width = str(data['image_square']['width'])
            fanart = data['image_square']['url'].replace('{width}', fanart_width).replace('{height}', fanart_height)

            info_label = {
                'title': title
            }

            images = {
                'icon': image,
                'fanart': fanart
            }

            helper.add_item(title, plugin.url_for(programs_list, code=code), info=info_label, art=images)
    helper.eod()


def tvp_program():
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.tvp.pl/program-tv',
        'Accept-Language': 'pl',
    }
    url = 'https://www.tvp.pl/program-tv'
    response = helper.make_request(url, 'get', headers=headers, json=False).text

    stations_regex = re.compile(r'window.__stationsProgram\[\d+]\s=\s(.*?)</script>', re.MULTILINE | re.DOTALL)

    epg = []

    for match in stations_regex.finditer(response):
        js_data = re.sub(r'},\n}', r'}\n}', match.group(1)).replace(';', '')
        data = json.loads(js_data)
        epg.append(data)

    return epg


@plugin.route('/programs_list')
def programs_list():
    code = plugin.args['code'][0]

    now = datetime.datetime.now()
    current_timestamp = int(now.timestamp())

    for epg in get_epg(code):
        org_title = epg['title']
        record_id = epg['record_id']
        start = time.strftime('%a, %d-%m-%Y %H:%M:%S', time.localtime(int(str(epg["date_start"])[:10])))
        title = f'[COLOR ff7f8c8d][{start}][/COLOR] [B]{org_title}[/B]'
        plotoutline = epg['description']
        plot = epg['description_long']

        if int(epg['date_start']) / 1000 < current_timestamp < int(epg['date_end']) / 1000:
            title = f'[COLOR ff7f8c8d][{start}][/COLOR] [B][COLOR orange]{org_title}[/COLOR][/B]'

        if epg.get('program'):
            if epg['program'].get('cycle'):
                if epg['program']['cycle']['image_logo']:
                    image_height = str(epg['program']['cycle']['image_logo']['height'])
                    image_width = str(epg['program']['cycle']['image_logo']['width'])
                    image = epg['program']['cycle']['image_logo']['url']
                    image = image.replace('{width}', image_width).replace('{height}', image_height)
                    images = {
                        'icon': image,
                        'fanart': image
                    }
                else:
                    image_height = str(epg['station']['image']['height'])
                    image_width = str(epg['station']['image']['width'])
                    image = epg['station']['image']['url']
                    image = image.replace('{width}', image_width).replace('{height}', image_height)
                    fanart_height = str(epg['station']['image_square']['height'])
                    fanart_width = str(epg['station']['image_square']['width'])
                    fanart = epg['station']['image_square']['url']
                    fanart = fanart.replace('{width}', fanart_width).replace('{height}', fanart_height)
                    images = {
                        'icon': image,
                        'fanart': fanart
                    }

                info_label = {
                    'title': org_title,
                    'plotoutline': plotoutline,
                    'plot': plot
                }

                helper.add_item(title, plugin.url_for(play_program, code=code, record_id=record_id), playable=True,
                                info=info_label, art=images)
    helper.eod()


@plugin.route('/play_program')
def play_program():
    code = plugin.args['code'][0]
    record_id = plugin.args['record_id'][0]
    endpoint = 'api/tvp-stream/stream/data'
    url = f'https://sport.tvp.pl/{endpoint}'
    params = {
        'station_code': code,
        'record_id': record_id,
        'device': 'android'
    }

    response = helper.make_request(url, 'get', params=params, headers=helper.headers)

    stream_url = response['data']['stream_url']

    helper.log(f' STREAM URL : {stream_url}')

    streams = helper.make_request(stream_url, 'get')
    stream = stream_data(streams["formats"])
    url_stream = stream['url']
    protocol_type = stream['protocol']
    stream_mime_type = stream['mime_type']

    helper.play_video(url_stream, protocol_type, stream_mime_type)


@plugin.route('/play_live')
def play_live():
    code = plugin.args['code'][0]

    endpoint = '/api/tvp-stream/stream/data'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'station_code': code,
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)

    stream_url = response['data']['stream_url']
    begin_time = re.split('^.*begin=(.*?)&live=.*', stream_url)[1]

    params = {
        'live': 'true',
        'time_shift': 'true',
        'begin': begin_time,
        'end': '',
        'device': 'android'
    }

    streams = helper.make_request(stream_url, 'get', params=params, headers=helper.headers)
    stream = stream_data(streams["formats"])
    url_stream = stream['url']
    protocol_type = stream['protocol']
    stream_mime_type = stream['mime_type']

    helper.play_video(url_stream, protocol_type, stream_mime_type)


def stream_data(streams):
    sorted_data = sorted(streams, key=lambda d: -int(d['totalBitrate']), reverse=True)

    for stream in sorted_data:
        if stream['mimeType'] == 'application/dash+xml':
            return {
                'url': stream['url'],
                'mime_type': 'application/xml+dash',
                'protocol': 'mpd'
            }

        elif stream['mimeType'] == 'application/x-mpegurl':
            return {
                'url': stream['url'],
                'mime_type': 'application/x-mpegURL',
                'protocol': 'hls'
            }

        elif stream['mimeType'] == 'video/mp2t':
            return {
                'url': stream['url'],
                'mime_type': 'application/x-mpegURL',
                'protocol': 'hls'
            }


def get_epg(code):
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    endpoint = '/api/tvp-stream/program-tv/index'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'station_code': code,
        'date': today,
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)

    return response['data']


@plugin.route('/archive')
def archive():
    endpoint = '/api/tvp-stream/program-tv/stations'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)
    if response['data']:
        for data in response['data']:
            title = data['name']
            code = data['code']

            image_height = str(data['image']['height'])
            image_width = str(data['image']['width'])
            image = data['image']['url'].replace('{width}', image_width).replace('{height}', image_height)
            fanart_height = str(data['image_square']['height'])
            fanart_width = str(data['image_square']['width'])
            fanart = data['image_square']['url'].replace('{width}', fanart_width).replace('{height}', fanart_height)

            info_label = {
                'title': title
            }

            images = {
                'icon': image,
                'fanart': fanart
            }

            helper.add_item(title, plugin.url_for(archive_days, code=code), info=info_label, art=images)
    helper.eod()


@plugin.route('/archive_days')
def archive_days():
    code = plugin.args['code'][0]
    now = datetime.datetime.now()
    date_range = [f'{now - datetime.timedelta(days=n):%Y-%m-%d}' for n in range(7)]
    for date in date_range:
        helper.add_item(date, plugin.url_for(programs_from_date, code=code, day=date))
    helper.eod()


@plugin.route('/programs_from_date')
def programs_from_date():
    code = plugin.args['code'][0]
    day = plugin.args['day'][0]

    endpoint = '/api/tvp-stream/program-tv/index'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'station_code': code,
        'date': day
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)

    for data in response['data']:
        org_title = data['title']
        code = data['station_code']
        record_id = data['record_id']
        start = time.strftime('%a, %d-%m-%Y %H:%M:%S', time.localtime(int(str(data["date_start"])[:10])))
        title = f'[COLOR ff7f8c8d][{start}][/COLOR] [B]{org_title}[/B]'
        plotoutline = data['description']
        plot = data['description_long']

        info_label = {
            'title': org_title,
            'plotoutline': plotoutline,
            'plot': plot
        }

        image_height = str(data['station']['image']['height'])
        image_width = str(data['station']['image']['width'])
        image = data['station']['image']['url'].replace('{width}', image_width).replace('{height}', image_height)
        fanart_height = str(data['station']['image_square']['height'])
        fanart_width = str(data['station']['image_square']['width'])
        fanart = data['station']['image_square']['url']
        fanart = fanart.replace('{width}', fanart_width).replace('{height}', fanart_height)

        images = {
            'icon': image,
            'fanart': fanart
        }

        helper.add_item(title, plugin.url_for(play_program, code=code, record_id=record_id), playable=True,
                        info=info_label, art=images)

    helper.eod()


@plugin.route('/vod_go')
def vod_go():
    endpoint = '/api/tvp-stream/block/list'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)

    for block in response['data']:
        if block['type'] == 'BLOCK_OCCURRENCES':
            title = block['title']

            helper.add_item(title, plugin.url_for(vod_go_block, category=title))

    helper.eod()


@plugin.route('/vod_go_block')
def vod_go_block():
    category = plugin.args['category'][0]
    endpoint = '/api/tvp-stream/block/list'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)

    for block in response['data']:
        if block['title'] == category:
            for item in block['items']:
                title = item['title']
                plotoutline = item['description']
                plot = item['description_long']
                code = item['station_code']
                record_id = item['record_id']

                image_height = str(item['program']['image']['height'])
                image_width = str(item['program']['image']['width'])
                image = item['program']['image']['url']
                image = image.replace('{width}', image_width).replace('{height}', image_height)

                info_label = {
                    'title': title,
                    'plotoutline': plotoutline,
                    'plot': plot
                }

                images = {
                    'icon': image,
                    'fanart': image
                }

                helper.add_item(title, plugin.url_for(play_program, code=code, record_id=record_id), playable=True,
                                info=info_label, art=images)

    helper.eod()


@plugin.route('/search')
def search():
    helper.add_item('Nowe wyszukiwanie', plugin.url_for(search_for))
    helper.add_item('Najczęściej wyszukiwane', plugin.url_for(most_popular))

    file = xbmcvfs.translatePath(f'special://home/userdata/addon_data/{helper.addon_name}/searching.txt')

    try:
        with xbmcvfs.File(file) as f:
            buffer = f.read()

        buffer = buffer.split(',')
        del buffer[-1]

        buffer = tuple(set(buffer))

        helper.add_item('[COLOR ff7f8c8d]Wyczyść wyszukiwania[/COLOR]', plugin.url_for(clear_searching))
        if len(buffer) > 0:
            for item in buffer:
                helper.add_item(item, plugin.url_for(search_for, query=item))
    except SyntaxError:
        pass

    helper.eod()


@plugin.route('/clear_searching')
def clear_searching():
    file = xbmcvfs.translatePath(f'special://home/userdata/addon_data/{helper.addon_name}/searching.txt')
    xbmcvfs.delete(file)
    helper.notification('Informacja', 'Wyczyszczono wyszukiwania')
    return True


@plugin.route('/most_popular')
def most_popular():
    endpoint = '/api/tvp-stream/search/most-popular'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'device': 'android'
    }
    searches = helper.make_request(url, 'get', params=params, headers=helper.headers)

    if searches.get('data'):
        for query in searches['data']:
            helper.add_item(query['query'], plugin.url_for(search_for, query=query['query']))

    helper.eod()


@plugin.route('/search_for')
def search_for():
    if plugin.args.get('query'):
        query = plugin.args['query'][0]
    else:
        query = xbmcgui.Dialog().input('Wyszukiwanie')

    helper.add_searching(query)

    if query != '':
        endpoint = '/api/tvp-stream/search/tabs'
        url = f'https://{helper.host}{endpoint}'
        params = {
            'query': query,
            'device': 'android'
        }
        searching = helper.make_request(url, 'get', params=params, headers=helper.headers)

        search_params = []

        for params in searching['data']:
            if 'vodprogrammesandepisodes' in params['params']['scope']:
                search_params.append(params['params'])

        search_results(search_params)


def search_results(search_params):
    images = {}

    endpoint = '/api/tvp-stream/search'
    url = f'https://{helper.host}{endpoint}'

    for params in search_params:
        results = helper.make_request(url, 'get', params=params, headers=helper.headers)

        for data in results['data']['occurrenceitem']:
            occurrence_id = data['id']
            org_title = data['title']
            sub_title = data['subtitle']
            title = org_title + f' - [COLOR ff7f8c8d]{sub_title}[/COLOR]'

            if data['program']['image']:
                image_height = str(data['program']['image']['height'])
                image_width = str(data['program']['image']['width'])
                image = data['program']['image']['url']
                image = image.replace('{width}', image_width).replace('{height}', image_height)

                images = {
                    'icon': image,
                    'fanart': image
                }

            helper.add_item(title, plugin.url_for(occurrenceitem, occurrence_id=occurrence_id),
                            art=images)

    helper.eod()


@plugin.route('/occurrenceitem')
def occurrenceitem():
    occurrence_id = plugin.args['occurrence_id'][0]
    images = {}

    endpoint = '/api/tvp-stream/program-tv/occurrence-video'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'id': occurrence_id,
        'device': 'android'
    }
    results = helper.make_request(url, 'get', params=params, headers=helper.headers)

    if results['data']['subtitle']:
        title = results['data']['title'] + f' - [COLOR ff7f8c8d]{results["data"]["subtitle"]}[/COLOR]'
    else:
        title = results['data']['title']

    plot_outline = results['data']['description']
    plot = results['data']['description_long']

    info_label = {
        'title': title,
        'plotoutline': plot_outline,
        'plot': plot
    }

    if results['data']['program']['image']:
        image_height = str(results['data']['program']['image']['height'])
        image_width = str(results['data']['program']['image']['width'])
        image = results['data']['program']['image']['url']
        image = image.replace('{width}', image_width).replace('{height}', image_height)

        images = {
            'icon': image,
            'fanart': image
        }

    list_item_title = '[COLOR ff7f8c8d][Odtwórz][/COLOR] ' + title
    helper.add_item(list_item_title, plugin.url_for(play_occurrence, play_id=occurrence_id), playable=True,
                    info=info_label, art=images)

    for tabs in results['data']['tabs']:
        if tabs['endpoint_type'] == 'SEASON_VIDEOS':
            seasons = tabs['params']['seasons']
            for season in seasons:
                tab_id = season['id']
                tab_name = season['title']

                helper.add_item(tab_name, plugin.url_for(occurrence_tab, tab_id=tab_id, page=1))

    helper.eod()


@plugin.route('/occurrence_tab')
def occurrence_tab():
    tab_id = plugin.args['tab_id'][0]
    page = int(plugin.args['page'][0])

    images = {}

    endpoint = '/api/tvp-stream/season/videos'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'id': tab_id,
        'page': page,
        'limit': 20,
        'device': 'android'
    }
    videos = helper.make_request(url, 'get', params=params, headers=helper.headers)

    for video in videos['data']:
        if video['subtitle']:
            title = video['title'] + f' - [COLOR ff7f8c8d]{video["subtitle"]}[/COLOR]'
        else:
            title = video['title']

        if video['program']['image']:
            image_height = str(video['program']['image']['height'])
            image_width = str(video['program']['image']['width'])
            image = video['program']['image']['url'].replace('{width}', image_width).replace('{height}', image_height)

            images = {
                'icon': image,
                'fanart': image
            }

        occurrence_id = video['id']

        helper.add_item(title, plugin.url_for(occurrenceitem, occurrence_id=occurrence_id), art=images)

    page += 1
    helper.add_item('Następna strona...', plugin.url_for(occurrence_tab, tab_id=tab_id, page=page))
    helper.eod()


@plugin.route('/play_occurrence')
def play_occurrence():
    play_id = plugin.args['play_id'][0]

    endpoint = '/api/tvp-stream/stream/data'
    url = f'https://{helper.host}{endpoint}'
    params = {
        'id': play_id,
        'device': 'android'
    }
    response = helper.make_request(url, 'get', params=params, headers=helper.headers)
    stream_url = response['data']['stream_url']

    params = {
        'live': 'false',
        'time_shift': 'true',
        'object_id': play_id,
        'device': 'android'
    }

    streams = helper.make_request(stream_url, 'get', params=params, headers=helper.headers)

    stream = stream_data(streams["formats"])
    url_stream = stream['url']
    protocol_type = stream['protocol']
    stream_mime_type = stream['mime_type']

    helper.play_video(url_stream, protocol_type, stream_mime_type)


@plugin.route('/settings')
def open_settings():
    helper.open_settings()


@plugin.route('/export_playlist')
def export_playlist():
    helper.export_playlist()


class Addon(Helper):
    def __init__(self):
        super().__init__()
        self.log(sys.argv)
        plugin.run()
