from playlistmanager import discography_playlist, __version__
from playlistmanager.musicbrainz import AlbumSorter, Filter, MusicBrainz
from playlistmanager.services import get_service

USER_AGENT = f"PlaylistManager/{__version__}"


def _disambiguate_source_artist(similar_artist_choices):
    return [{**info, "disambiguation": ", ".join(similar["name"] for similar in info["similar"])} for info in similar_artist_choices]

def similar_artists_playlist(service_name, search_name, artist_id, similar_artist_musicbrainz_ids=[], release_filter=Filter.create(), album_sorter=AlbumSorter.create(), client_config={}):
    musicbrainz = MusicBrainz.connect(USER_AGENT)
    service = get_service(service_name)

    if not similar_artist_musicbrainz_ids:
        similar_artists = service.get_similar_artists(artist_id, client_config)

        artist_ids = []
        for similar_artist in similar_artists:
            search_result = musicbrainz.search_artist(similar_artist, 85)
            similar_artist_musicbrainz = discography_playlist._prompt_for_artist(search_result, similar_artist) if len(search_result) > 1 else search_result[0]
            artist_ids.append(similar_artist_musicbrainz["id"])
        similar_artist_musicbrainz_ids = artist_ids.copy()

    albums_info_by_artist = {}
    for similar_artist_id in similar_artist_musicbrainz_ids:
        name = musicbrainz.get_artist(similar_artist_id)["name"]
        albums_info_by_artist[name] = {
            "albums": musicbrainz.get_artist_albums_info(similar_artist_id, release_filter, album_sorter),
            "links": musicbrainz.get_artist_links(similar_artist_id)
        }

    return service.create_similar_artists_playlist(albums_info_by_artist, search_name, client_config)

def similar_artists_playlist_cli(service_name, search_name, match_threshhold, release_filter=Filter.create(), album_sorter=AlbumSorter.create(), auth=None):
    service = get_service(service_name)
    client_config = service.auth_to_config(auth)

    musicbrainz = MusicBrainz.connect(USER_AGENT)

    choices = service.search_artists(search_name, client_config)
    choices_with_info = _disambiguate_source_artist(choices)
    artist = discography_playlist._prompt_for_artist(choices_with_info, search_name) if len(choices_with_info) > 1 else choices_with_info[0]

    return similar_artists_playlist(service_name, search_name, artist["id"], release_filter=release_filter, album_sorter=album_sorter, client_config=client_config)
