# A place to hook into the ytmusicapi library and hotswap in the new functions.

def hook_parse_playlist():
    import re

    from ytmusicapi.parsers.browsing import parse_playlist as _orig_parse_playlist
    from ytmusicapi.parsers.utils import nav
    from ytmusicapi.parsers import SUBTITLE2

    def parse_playlist(data):
        playlist = _orig_parse_playlist(data)
        if len(data['subtitle']['runs']) == 3 and re.search(r'\d+ ', nav(data, SUBTITLE2)):
            playlist['count'] = nav(data, SUBTITLE2).split(' ')[0]
        return playlist


    import ytmusicapi
    ytmusicapi.parsers.browsing.parse_playlist = parse_playlist
    ytmusicapi.mixins.browsing.parse_playlist = parse_playlist
    ytmusicapi.mixins.library.parse_playlist = parse_playlist
    ytmusicapi.mixins.explore.parse_playlist = parse_playlist

hook_parse_playlist()
