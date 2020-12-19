import math
import os
import requests

ALL_SEARCH_TYPES = ["AL", "AR", "CO", "TR", "SF", "PL", "ST", "PC", "PE"]
SEARCH_ENDPOINT = "v3/sod/search"
PLAYLIST_CREATE_ENDPOINT = "v4/playlists/create"
PLAYLIST_APPEND_ENDPOINT = "v4/playlists/appendItems"
ARTIST_DISCOGRAPHY_ENDPOINT = "v4/catalog/getArtistDiscographyWithCollaborations"

RELEASE_TYPES = {
    "Deluxe": 0,
    "OriginalAlbum": 1
}

class Pandora:
    BASE = "https://www.pandora.com/"
    BASE_API = f"{BASE}/api"

    @staticmethod
    def connect():
        session = requests.Session()

        # Retrieve CSRF token
        cookies = session.head(Pandora.BASE).cookies
        session.headers.update({"X-CsrfToken": cookies["csrftoken"]})

        pandora = Pandora(session)
        pandora.login()
        return pandora

    def __init__(self, session):
        self.session = session

    def _request(self, endpoint, data):
        return self.session.post(f"{Pandora.BASE_API}/{endpoint}", json=data).json()

    def login(self):
        login_result = self._request("v1/auth/login", {"username": "mathfreak65@gmail.com", "password": os.environ["PANDORAPW"]})
        self.session.headers.update({"X-AuthToken": login_result["authToken"]})

    def playlist_append(self, playlist_info, item_ids, *, update_info=False):
        new_playlist_info = self._request(PLAYLIST_APPEND_ENDPOINT, {"pandoraId": playlist_info["pandoraId"], "playlistVersion": playlist_info["version"], "itemPandoraIds": item_ids})
        if update_info:
            # Update playlist info with new response
            playlist_info.update({key: val for key, val in new_playlist_info.items() if key in playlist_info})
        return new_playlist_info

    def playlist_create(self, name):
        return self._request(PLAYLIST_CREATE_ENDPOINT, {"details": {"name": name}})

    def search(self, query, types=ALL_SEARCH_TYPES, count=20):
        return self._request(SEARCH_ENDPOINT, {"query": query, "types": types, "count": count})

    def search_album(self, query, count=20):
        return self.search(query, ["AL"], count)

    def search_artist(self, query, count=20):
        return self.search(query, ["AR", "CO"], count)

    def get_artist_discography(self, artist_id, *, annotation_limit=0):
        return self._request(ARTIST_DISCOGRAPHY_ENDPOINT, {"artistPandoraId": artist_id, "annotationLimit": annotation_limit})

    ### Higher-level operations
    def get_album(self, artist_info, album_name):
        artist_discography_info = self.get_artist_discography(artist_info["pandoraId"])

        # Uses the search function to account for differences in recorded album
        # name between the services, and between the versions. For example,
        # deluxe versions.
        search_result = self.search_album(f"{artist_info['name']} {album_name}", 5)

        for album_id in search_result["results"]:
            album_info = search_result["annotations"][album_id]
            if album_info["pandoraId"] in artist_discography_info["discography"]:
                return album_info

    def get_albums(self, artist_info, album_names):
        return {album_name: self.get_album(artist_info, album_name) for album_name in album_names}
