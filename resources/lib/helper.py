import requests

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import xbmcplugin


class Helper:
    def __init__(self, base_url=None, handle=None):
        self.base_url = base_url
        self.handle = handle
        self.addon = xbmcaddon.Addon()
        self.addon_name = self.addon.getAddonInfo('id')
        self.addon_version = self.addon.getAddonInfo('version')
        self.logging_prefix = f'===== [{self.addon_name} - {self.addon_version}] ====='
        self.http_session = requests.Session()
        # API
        self.host = 'sport.tvp.pl'
        self.headers = {
            'Host': self.host,
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/5.0.0-alpha.2',
        }

    def log(self, string):
        msg = f'{self.logging_prefix}: {string}'
        xbmc.log(msg=msg, level=1)

    def get_setting(self, string):
        return xbmcaddon.Addon(self.addon_name).getSettingString(string)

    def set_setting(self, setting, string):
        return xbmcaddon.Addon(self.addon_name).setSettingString(id=setting, value=string)

    def open_settings(self):
        xbmcaddon.Addon(self.addon_name).openSettings()

    def add_item(self, title, url, playable=False, info=None, art=None, content=None, folder=True):
        list_item = xbmcgui.ListItem(label=title)
        if playable:
            list_item.setProperty('IsPlayable', 'true')
            folder = False
        if art:
            list_item.setArt(art)
        else:
            art = {
                'icon': self.addon.getAddonInfo('icon'),
                'fanart': self.addon.getAddonInfo('fanart')
            }
            list_item.setArt(art)
        if info:
            list_item.setInfo('Video', info)
        if content:
            xbmcplugin.setContent(self.handle, content)

        xbmcplugin.addDirectoryItem(self.handle, url, list_item, isFolder=folder)

    def eod(self, cache=True):
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=cache)

    def notification(self, heading, message):
        xbmcgui.Dialog().notification(heading, message, time=7000)

    def make_request(self, url, method, params=None, payload=None, headers=None, allow_redirects=None, verify=None,
                     json=True):
        self.log(f'Request URL: {url}')
        self.log(f'Method: {method}')
        if params:
            self.log(f'Params: {params}')
        if payload:
            self.log(f'Payload: {payload}')
        if headers:
            self.log(f'Headers: {headers}')

        if method == 'get':
            with self.http_session as req:
                if json:
                    return req.get(url, params=params, headers=headers, allow_redirects=allow_redirects,
                                   verify=verify).json()
                else:
                    return req.get(url, params=params, headers=headers, allow_redirects=allow_redirects, verify=verify)
        else:  # post
            with self.http_session as req:
                return req.post(url, params=params, json=payload, headers=headers)

    def play_video(self, stream_url, drm_protocol, mime_type):
        from inputstreamhelper import Helper  # pylint: disable=import-outside-toplevel

        play_item = xbmcgui.ListItem(path=stream_url)
        is_helper = Helper(drm_protocol, drm='com.widevine.alpha')
        if is_helper.check_inputstream():
            play_item.setProperty('inputstream', is_helper.inputstream_addon)
            play_item.setMimeType(mime_type)
            play_item.setProperty('inputstream.adaptive.manifest_type', drm_protocol)
            play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            play_item.setContentLookup(False)
            xbmcplugin.setResolvedUrl(self.handle, True, listitem=play_item)

    def return_channels(self):
        from resources.lib.addon import live
        return live()

    def add_searching(self, result):
        file = xbmcvfs.translatePath(f'special://home/userdata/addon_data/{self.addon_name}/searching.txt')
        append = result + ','

        with xbmcvfs.File(file) as f:
            buffer = f.read()

        with xbmcvfs.File(file, 'w') as f:
            f.write(buffer + append)

    def export_playlist(self):
        file = None
        m3u_path = self.get_setting('tvpgo_m3u_path')
        file_name = self.get_setting('tvpgo_file_name')

        if not file_name or not m3u_path:
            self.notification('TVP GO', 'Ustaw nazwę pliku i ścieżkę')
            return

        self.notification('TVP GO', 'Generuje listę')
        data = '#EXTM3U\n'

        for item in self.return_channels():
            data += (
                f'#EXTINF:0 tvg-id="{item["id"]}" tvg-logo="{item["logo"]}" group-title="TVP GO",{item["title"]}\n'
                f'plugin://plugin.video.tvpgo/play_live?code={item["id"]}\n')

        try:
            file = xbmcvfs.File(m3u_path + file_name, 'w')
            file.write(data)
        finally:
            file.close()
        self.notification('TVP GO', 'Lista m3u wygenerowana')
