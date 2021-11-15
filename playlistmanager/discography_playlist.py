import argparse
import collections

from playlistmanager.musicbrainz import AlbumSorter, Filter, MusicBrainz
from playlistmanager.services import get_service

USER_AGENT = "PlaylistManager/0.1"

def _prompt_for_artist(matches, search_name):
    print(f"MusicBrainz found multiple artists matching \"{search_name}\". Please select one:")
    while True:
        for num, match in enumerate(matches, start=1):
            match_str = f"{num}. {match['name']}"
            disambig = match.get("disambiguation", match.get("country"))
            if disambig:
                match_str += f" ({disambig})"
            print(match_str)

        try:
            choice = int(input(f"Please select an artist [1-{len(matches)}]: "))
        except ValueError:
            pass
        else:
            if int(choice) in range(1, len(matches) + 1):
                return matches[choice - 1]

        print("Invalid choice.")

def discography_playlist(service_name, search_name, artist_id, release_filter=Filter.create(), album_sorter=AlbumSorter.create(), client_config={}):
    musicbrainz = MusicBrainz.connect(USER_AGENT)

    artist_links = musicbrainz.get_artist_links(artist_id)
    albums_info = musicbrainz.get_artist_albums_info(artist_id, release_filter, album_sorter)

    return get_service(service_name).create_discography_playlist(albums_info, artist_links, search_name, client_config)

def discography_playlist_cli(service_name, search_name, match_threshhold, release_filter=Filter.create(), album_sorter=AlbumSorter.create(), auth=None):
    musicbrainz = MusicBrainz.connect(USER_AGENT)

    search_result = musicbrainz.search_artist(search_name, match_threshhold)
    artist = _prompt_for_artist(search_result, search_name) if len(search_result) > 1 else search_result[0]

    client_config = get_service(service_name).auth_to_config(auth)

    return discography_playlist(service_name, search_name, artist["id"], release_filter, album_sorter, client_config)
