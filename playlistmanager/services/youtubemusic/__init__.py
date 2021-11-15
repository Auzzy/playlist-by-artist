import json
import re

import requests
from bs4 import BeautifulSoup
from ytmusicapi import YTMusic


NAMES = ("ytm", "youtubemusic", "youtube")


LINK_CHANNEL_RE = re.compile("https?://www\.youtube\.com\/channel\/(?P<channel>[^/]*)(?!/.*)?")
LINK_USER_RE = re.compile("https?://www\.youtube\.com\/user\/(?P<user>[^/]*)(?!/.*)?")

_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "dnt": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "x-goog-authuser": "0",
    "x-origin": "https://music.youtube.com"
}

def auth_to_config(auth):
    return {"cookie": auth} if auth else {}

def create_client(client_config):
    return YTMusic(auth=json.dumps({**_HEADERS, **client_config}))


# Pretty sure I actually don't need to care. It looks like giving a YouTube ID to YouTube Music produces the info I need.
'''
def _map_yt_id_to_ytm(ytm, yt_id):
    # The YouTube channel ID is not the same as the YouTube Music ID. There is
    # some info shared between the two, which lets us perform a mapping, but
    # it's a pain.
    # The best way is to ask YouTube for the artist's main page, grab the list
    # of albums there (a subset of all their albums), get each album's details,
    # then take the intersection of the artist IDs. This ensures we only get
    # the ID of the artist(s) who show up on all of them, which should be a
    # single ID, but could be multiple.
    artist_result = ytm.get_artist(yt_id)
    artist_album_results = artist_result["albums"]["results"]
    if artist_album_results:
        artists = []
        for album in artist_album_results:
            album_result = ytm.get_album(album["browseId"])
            artists.append({artist["id"] for artist in album_result["artists"]})
        return set.intersection(*artists)

    else:
        # This artist has no albums?
        pass
'''

# To add albums to a playlist, there are two choices. You can pass the list of
# video IDs, or pass each album playlist one-by-one. While passing the entire
# list of video IDs in one shot at playlist creation is more convenient, since
# they're video IDs, the music video associated with the track (if it exists)
# is added to the playlist instead of just the audio track. When passing the
# album playlists, this is not the case; they're all audio tracks. As this is
# the desired behavior, we have to go with the less convenient code.
def _create_ytm_playlist(ytm, search_name, album_playlist_ids, name_format):
    playlist_name = name_format.format(artist=search_name)
    playlist_id = ytm.create_playlist(playlist_name, "")
    for album_playlist_id in album_playlist_ids:
        ytm.add_playlist_items(playlist_id, source_playlist=album_playlist_id)
    return playlist_name

def _find_album_by_name(album_info, yt_album_names):
    album_aliases = {name.lower() for name in [album_info["title"]] + album_info["aliases"]}

    # Check for exact match, first on the title then each alias.
    for alias in album_aliases:
        if alias in yt_album_names:
            return alias

    # Check if any alias is in the list of YouTube album names. Starts by
    # checking the entire YouTube list for the full title, then moves on to
    # aliases.
    # This is deliberately a separate loop to prioritize any exact match.
    for alias in album_aliases:
        for yt_album_name in yt_album_names:
            if alias in yt_album_name:
                return yt_album_name

    return None

def _get_yt_artist_discog(ytm, artist_ids, albums_info):
    album_id_by_name = {}
    for artist_id in reversed(list(artist_ids)):
        artist_album_summary = ytm.get_artist(artist_id)["albums"]
        album_browse_id = artist_album_summary.get("browseId")
        if album_browse_id:
            artist_album_list = ytm.get_artist_albums(album_browse_id, artist_album_summary["params"])
        else:
            artist_album_list = artist_album_summary["results"]

        album_id_by_name.update({info["title"].lower(): info["browseId"] for info in artist_album_list})

    unselected_albums = list(album_id_by_name.keys())
    album_playlist_ids = []
    for info in albums_info:
        yt_album_name = _find_album_by_name(info, unselected_albums)
        if not yt_album_name:
            print(f"Could not find \"{info['title']}\" on YouTube Music. Skipping.")
            continue

        album_playlist_id = ytm.get_album(album_id_by_name[yt_album_name])["audioPlaylistId"]
        album_playlist_ids.append(album_playlist_id)

        # Drop this album name from the search list to prevent duplicates.
        unselected_albums.remove(yt_album_name)

    return album_playlist_ids

def _extract_channel_id(yt_url):
    yt_page_src = requests.get(yt_url).text
    return BeautifulSoup(yt_page_src, "html.parser").find(itemprop="channelId").attrs["content"]

def _yt_channel_id_from_url(yt_url):
    yt_match = LINK_CHANNEL_RE.match(yt_url)
    if yt_match:
        return yt_match.group("channel")
    else:
        return _extract_channel_id(yt_url)

def _get_ytm_artist(ytm, albums_info, artist_links, search_name):
    yt_links = artist_links.get("youtube", [])
    if yt_links:
        return {_yt_channel_id_from_url(yt_link) for yt_link in yt_links}
    else:
        # If there's no YouTube link, search for the artist.

        # First version is to just grab the artist YouTube says is most likely who they're referring to.
        artist_choices = search_artists(search_name, client=ytm)
        return {artist_choices[0]["id"]}

def get_similar_artists(artist_id, client_config):
    similar_artists = create_client(client_config).get_artist(artist_id).get("related", {}).get("results", [])
    return [artist["title"] for artist in similar_artists]

def search_artists(search_name, client_config={}, *, client=None):
    ytm = client or create_client(client_config)

    search_results = ytm.search(search_name, filter="artists", limit=5, ignore_spelling=True)
    choices = []
    for result in search_results:
        artist_id = result["browseId"]
        related_results = ytm.get_artist(artist_id).get("related", {}).get("results", [])
        similar_info = [{"id": artist["browseId"], "name": artist["title"]} for artist in related_results]
        choices.append({"id": artist_id, "name": result["artist"], "similar": similar_info})
    return choices

def create_discography_playlist(albums_info, artist_links, search_name, client_config, name_format="{artist} Discography"):
    ytm = create_client(client_config)

    artist_ids = _get_ytm_artist(ytm, albums_info, artist_links, search_name)
    album_playlist_ids = _get_yt_artist_discog(ytm, artist_ids, albums_info)
    return _create_ytm_playlist(ytm, search_name, album_playlist_ids, name_format)

def create_similar_artists_playlist(albums_info_by_artist, search_name, client_config, name_format="{artist} Similar Artists"):
    ytm = create_client(client_config)

    album_playlist_ids = []
    for similar_name, info in albums_info_by_artist.items():
        artist_ids = _get_ytm_artist(ytm, info["albums"], info["links"], similar_name)
        album_playlist_ids.extend(_get_yt_artist_discog(ytm, artist_ids, info["albums"]))
    return _create_ytm_playlist(ytm, search_name, album_playlist_ids, name_format)
