from playlistmanager import discography_playlist
from playlistmanager.musicbrainz import AlbumSorter, Filter, MusicBrainz
from playlistmanager.pandora import Pandora


def _disambiguate_source_artist(similar_artist_choices):
    return [{**info, "disambiguation": ", ".join(similar["name"] for similar in info["similar"])} for info in similar_artist_choices]

def _get_similar_artists(pandora, artist_name):
    search_result = pandora.search_artist(artist_name, count=5)
    artist_info = search_result["annotations"]
    choices = []
    for artist_id in search_result["results"]:
        similar_info = [{"id": artist["pandoraId"], "name": artist["name"]} for artist in pandora.get_similar_artists(artist_id)]
        choices.append({"id": artist_id, "name": artist_info[artist_id]["name"], "similar": similar_info})
    return choices

def similar_artists_playlist(artist_name, artist_id, similar_artist_musicbrainz_ids=[], release_filter=Filter.create(), album_sorter=AlbumSorter.create(), pandora_config={}):
    musicbrainz = MusicBrainz.connect(USER_AGENT)
    pandora = Pandora.connect(**pandora_config)

    if not similar_artist_musicbrainz_ids:
        similar_artists = pandora.get_similar_artists(artist_id)

        artist_ids = []
        for similar_artist in similar_artists:
            search_result = musicbrainz.search_artist(similar_artist["name"], 85)
            similar_artist_musicbrainz = discography_playlist._prompt_for_artist(search_result, similar_artist["name"]) if len(search_result) > 1 else search_result[0]
            artist_ids.append(similar_artist_musicbrainz["id"])
        similar_artist_musicbrainz_ids = artist_ids.copy()

    album_ids = []
    for similar_artist_id in similar_artist_musicbrainz_ids:
        albums_info = discography_playlist.get_artist_albums_info(musicbrainz, similar_artist_id, release_filter, album_sorter)
        albums = discography_playlist.get_pandora_albums(pandora, albums_info)
        album_ids.extend(discography_playlist.process_albums(albums, albums_info[0]["artists"][0]))
    return discography_playlist.create_playlist(pandora, artist_name, album_ids, "{artist} Similar Artists")

def similar_artists_playlist_cli(artist_name, match_threshhold, release_filter=Filter.create(), album_sorter=AlbumSorter.create(), token=None):
    pandora_config = {}
    if token:
        pandora_config["auth_token"] = token

    musicbrainz = MusicBrainz.connect(USER_AGENT)
    pandora = Pandora.connect(**pandora_config)

    choices = _get_similar_artists(pandora, artist_name)
    choices_with_info = _disambiguate_source_artist(choices)
    artist = discography_playlist._prompt_for_artist(choices_with_info, artist_name) if len(choices_with_info) > 1 else choices_with_info[0]

    return similar_artists_playlist(artist_name, artist["id"], release_filter=release_filter, album_sorter=album_sorter, pandora_config=pandora_config)