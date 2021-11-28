# A place to hook into the ytmusicapi library and hotswap in the new functions.

def hook_parse_playlist():
    import re

    from ytmusicapi.parsers.browsing import parse_playlist as _orig_parse_playlist
    from ytmusicapi.parsers.utils import nav
    from ytmusicapi.parsers import SUBTITLE, SUBTITLE2, NAVIGATION_BROWSE_ID

    def parse_playlist(data):
        playlist = _orig_parse_playlist(data)
        if len(data['subtitle']['runs']) == 3:
            playlist["author"] = {
                "name": nav(data, SUBTITLE).strip(),
                "id": nav(data, SUBTITLE[:-1] + NAVIGATION_BROWSE_ID)
            }
            if re.search(r'\d+ ', nav(data, SUBTITLE2)):
                playlist['count'] = nav(data, SUBTITLE2).split(' ')[0]
        return playlist

    import ytmusicapi
    ytmusicapi.parsers.browsing.parse_playlist = parse_playlist
    ytmusicapi.mixins.browsing.parse_playlist = parse_playlist
    ytmusicapi.mixins.library.parse_playlist = parse_playlist
    ytmusicapi.mixins.explore.parse_playlist = parse_playlist

def hook_parse_playlist_items():
    from ytmusicapi.parsers.playlists import parse_playlist_items as _orig_parse_playlist_items
    from ytmusicapi.parsers.utils import nav
    from ytmusicapi.parsers import MENU_ITEMS, MRLIR, TOGGLE_MENU

    def parse_playlist_items(results, *args, **kwargs):
        songs = _orig_parse_playlist_items(results, *args, **kwargs)

        ADD_TO_LIBRARY = [TOGGLE_MENU, "defaultText", "runs"]

        # For simplicity, this is assuming the songs will be in the same order as the results. Matching them up is doable, but will require digging in and getting the setVideoId for each entry.
        for song, result in zip(songs, results):
            song["inLibrary"] = None

            data = result.get(MRLIR, {})
            if not data or "menu" not in data:
                continue

            song["inLibrary"] = True
            for item in nav(data, MENU_ITEMS):
                if TOGGLE_MENU in item and nav(item, ADD_TO_LIBRARY)[0]["text"].lower() == "add to library":
                        song["inLibrary"] = False
        
        return songs
    
    import ytmusicapi
    ytmusicapi.parsers.library.parse_playlist_items = parse_playlist_items
    ytmusicapi.mixins.playlists.parse_playlist_items = parse_playlist_items
    ytmusicapi.mixins.browsing.parse_playlist_items = parse_playlist_items
    ytmusicapi.mixins.library.parse_playlist_items = parse_playlist_items

hook_parse_playlist()
hook_parse_playlist_items()
