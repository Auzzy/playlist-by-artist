import collections
import itertools

from playlistmanager.services.pandora.client import Pandora

NAMES = ("pandora", )


def auth_to_config(token):
    return {"auth_token": token} if token else {}

def create_client(client_config):
    return Pandora.connect(**client_config)

def _create_pandora_playlist(search_name, album_ids, name_format, client_config={}, *, client=None):
    pandora = client or create_client(client_config)

    playlist_name = name_format.format(artist=search_name)
    playlist_info = client.playlist_create(playlist_name)
    pandora.playlist_append(playlist_info, album_ids, update_info=True)
    return playlist_name

def _process_albums(albums_by_name):
    album_ids = []
    for name, albums in albums_by_name.items():
        if not albums:
            print(f"Could not find \"{name}\" on Pandora. Skipping.")
            continue

        for album in albums:
            if album["pandoraId"] in album_ids:
                print(f"Duplicate album ID. Probably couldn't find \"{name}\" on Pandora, so search turned up another album by {album['artistName']}. Skipping.")
                continue

            album_ids.append(album["pandoraId"])

    return album_ids

def _get_pandora_albums(pandora, albums_info):
    albums_by_artists = collections.defaultdict(set)
    # Partition album info by artist name(s).
    for album_info in albums_info:
        albums_by_artists[" ".join(album_info["artists"])].update([album_info["title"]] + album_info["aliases"])

    # Pandora is inconsistent with its handling of multi-artist albums, likely
    # driven by licensing. Some show up under one artist but not the other,
    # some are joined to form a new artist. So we load the albums associated
    # with each artist that match the requested names, and sort them out after.
    artist_cache = {}
    for artist_name, album_names in albums_by_artists.items():
        if artist_name not in artist_cache:
            # Add entry to the cache to cover no results for the search.
            artist_cache[artist_name] = {}

            artist_results = pandora.search_artist(artist_name, 3)

            # There's no surefire way to link from MusicBrainz to Pandora.
            # So instead, we'll iterate over the search results until we
            # find an artist with at least one matching album, since it's
            # unlikely two artists with similar names will have released
            # albums with the same name.
            for artist_id in artist_results["results"]:
                artist_info = artist_results["annotations"][artist_id]

                artist_cache[artist_name] = pandora.get_albums(artist_info, album_names)
                if any(artist_cache[artist_name].values()):
                    break

    # Now we go through the original list of album names to determine the
    # correct ordering. This allows the intervleaving of LPs and EPs, and of
    # albums marked as from different artists.
    final_albums = collections.defaultdict(list)
    final_album_ids = collections.defaultdict(set)
    for album_info in albums_info:
        artist_name = " ".join(album_info["artists"])

        for album_name in [album_info["title"]] + album_info["aliases"]:
            pandora_album_info = artist_cache[artist_name].get(album_name)
            if pandora_album_info:
                if pandora_album_info["pandoraId"] not in final_album_ids[album_name]:
                    final_albums[album_name].append(pandora_album_info)
                    final_album_ids[album_name].add(pandora_album_info["pandoraId"])
                    break
        else:
            final_albums[album_name] = []

    return final_albums

def _get_album_ids(albums_info, client_config={}, *, client=None):
    pandora = client or create_client(client_config)

    albums = _get_pandora_albums(pandora, albums_info)
    return _process_albums(albums)

def get_similar_artists(artist_id, client_config):
    similar_artists = create_client(client_config).get_similar_artists(artist_id)
    return [artist["name"] for artist in similar_artists]

def search_artists(search_name, client_config):
    pandora = create_client(client_config)

    search_result = pandora.search_artist(search_name, count=5)
    artist_info = search_result["annotations"]
    choices = []
    for artist_id in search_result["results"]:
        similar_info = [{"id": artist["pandoraId"], "name": artist["name"]} for artist in pandora.get_similar_artists(artist_id)]
        choices.append({"id": artist_id, "name": artist_info[artist_id]["name"], "similar": similar_info})
    return choices

def create_discography_playlist(albums_info, artist_links, search_name, client_config, name_format="{artist} Discography"):
    pandora = create_client(client_config)

    album_ids = _get_album_ids(albums_info, client=pandora)
    return _create_pandora_playlist(search_name, album_ids, name_format, client=pandora)

def create_similar_artists_playlist(albums_info_by_artist, search_name, client_config, name_format="{artist} Similar Artists"):
    pandora = create_client(client_config)

    albums_info = list(itertools.chain.from_iterable(info["albums"] for info in albums_info_by_artist.values()))
    album_ids = _get_album_ids(albums_info, client=pandora)
    return _create_pandora_playlist(search_name, album_ids, name_format, client=pandora)
