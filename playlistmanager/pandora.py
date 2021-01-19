import math
import os
import requests

ALL_SEARCH_TYPES = ["AL", "AR", "CO", "TR", "SF", "PL", "ST", "PC", "PE"]
SEARCH_ENDPOINT = "v3/sod/search"
PLAYLIST_CREATE_ENDPOINT = "v4/playlists/create"
PLAYLIST_APPEND_ENDPOINT = "v4/playlists/appendItems"
PLAYLIST_REMOVE_ENDPOINT = "v7/playlists/deleteTracks"
GET_PLAYLISTS_ENDPOINT = "v6/collections/getSortedPlaylists"
GET_PLAYLIST_TRACKS_ENDPOINT = "v7/playlists/getTracks"
EDIT_PLAYLIST_ENDPOINT = "v7/playlists/editTracks"
ARTIST_DISCOGRAPHY_ENDPOINT = "v4/catalog/getArtistDiscographyWithCollaborations"
LIBRARY_ADD_ENDPOINT = "v6/collections/addItem"
LIBRARY_GET_ENDPOINT = "v6/collections/getItems"

RELEASE_TYPES = {
    "Deluxe": 0,
    "OriginalAlbum": 1
}

class Pandora:
    BASE = "https://www.pandora.com"
    BASE_API = f"{BASE}/api"

    @staticmethod
    def connect(**kwargs):
        session = requests.Session()

        # Retrieve CSRF token
        cookies = session.head(Pandora.BASE).cookies
        session.headers.update({"X-CsrfToken": cookies["csrftoken"]})

        pandora = Pandora(session)

        if "auth_token" in kwargs:
            pandora.session.headers.update({"X-AuthToken": kwargs["auth_token"]})
        else:
            pandora.login()

        return pandora

    def __init__(self, session):
        self.session = session

    def _request(self, endpoint, data):
        response = self.session.post(f"{Pandora.BASE_API}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def login(self, username=None, password=None):
        username = username or os.environ.get("PANDORAUSR")
        password = password or os.environ.get("PANDORAPW")
        if not username or not password:
            raise ValueError("Missing Pandora username and password. Expected as either parameters or environment variables.")

        login_result = self._request("v1/auth/login", {"username": username, "password": password})
        self.session.headers.update({"X-AuthToken": login_result["authToken"]})

    def library_add(self, track_id):
        return self._request(LIBRARY_ADD_ENDPOINT, {"request": {"pandoraId": track_id}})
    
    def library_add_bulk(self, track_ids):
        for track_id in track_ids:
            self.library_add(track_id)

    def library_get_items(self, limit=10000, *, cursor=None):
        return self._request(LIBRARY_GET_ENDPOINT, {"request": {"limit": limit, "cursor": cursor}})

    def get_playlist_tracks_info(self, playlist_info, offset=0, limit=100):
        playlist_version = 0 if offset == 0 else playlist_info["version"]
        return self._request(GET_PLAYLIST_TRACKS_ENDPOINT, {"request": {"pandoraId": playlist_info["pandoraId"], "playlistVersion": playlist_version, "offset": offset, "limit": limit, "annotationLimit": limit}})

    def get_all_playlists(self):
        return self._request(GET_PLAYLISTS_ENDPOINT, {"request": {"sortOrder": "ALPHA", "offset": 0, "limit": 100, "annotationLimit": 100}})

    def get_playlist_info(self, id):
        return self._request(GET_PLAYLIST_TRACKS_ENDPOINT, {"request": {"pandoraId": id, "playlistVersion": 0, "limit": 0}})

    def playlist_remove(self, playlist_info, track_ids):
        return self._request(PLAYLIST_REMOVE_ENDPOINT, {"request": {"pandoraId": playlist_info["pandoraId"], "trackItemIds": track_ids}})

    # The move_set should be a list of moves to submit in a single request.
    # Each move is a list, consisting of the itemId, old index, and new index.
    # e.g. [[1, 0, 5], [4, 3, 6]]
    def playlist_edit(self, playlist_info, move_set):
        moves = [{"itemId": int(move[0]), "oldIndex": int(move[1]), "newIndex": int(move[2])} for move in move_set]
        self._request(EDIT_PLAYLIST_ENDPOINT, {"request": {"pandoraId": playlist_info["pandoraId"], "playlistVersion": playlist_info["version"], "moves": moves}})

    # The move_list should be a list. Each element is the list of moves to be
    # made in a single request. Each move is a list, consisting of the itemId,
    # old index, and new index.
    # e.g. [[[1, 0, 5], [4, 3, 6]], [[3, 1, 9]]]
    def playlist_edit_bulk(self, playlist_info, move_list):
        for move_set in move_list:
            self.playlist_edit(playlist_info, move_set)

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

    def get_playlist_tracks_paginated(self, playlist_info, offset=0, limit=100):
        tracks = []
        tracks_info = self.get_playlist_tracks_info(playlist_info, offset, limit)
        for track in tracks_info["tracks"]:
            track_id = track["trackPandoraId"]
            detail = tracks_info["annotations"][track_id]
            tracks.append({
                "track_id": track_id,
                "item_id": track["itemId"],
                "name": detail["name"],
                "artist": detail["artistName"],
                "album": detail["albumName"]
            })
        return tracks

    def get_playlist_tracks(self, playlist_info):
        tracks = []
        while True:
            tracks.extend(self.get_playlist_tracks_paginated(playlist_info, len(tracks)))
            if len(tracks) >= playlist_info["totalTracks"]:
                break

        return tracks

    # new_tracklist_ids should be Pandora itemIds, NOT the trackPandoraId.
    def update_playlist(self, playlist_info, new_tracklist_ids):
        current_track_ids = [track["item_id"] for track in self.get_playlist_tracks(playlist_info)]
        new_tracklist_ids = [int(id) for id in new_tracklist_ids]

        moves = []
        for new_index, item_id in enumerate(new_tracklist_ids):
            old_index = current_track_ids.index(item_id)
            if new_index != old_index:
                moves.append([item_id, old_index, new_index])

        deletions = list(set(current_track_ids) - set(new_tracklist_ids))

        # Note the order is important here. Deleting after moving means the
        # move indices don't need to be adjusted.
        self.playlist_edit(playlist_info, moves)
        self.playlist_remove(playlist_info, deletions)

    # track_ids should be Pandora itemIds, NOT the trackPandoraId.
    def library_add_from_playlist(self, playlist_info, track_ids):
        track_ids = [int(id) for id in track_ids]
        to_add = []
        for playlist_track_info in self.get_playlist_tracks(playlist_info):
            if playlist_track_info["item_id"] in track_ids:
                to_add.append(playlist_track_info["track_id"])
        
        self.library_add_bulk(to_add)

    def library_get_all(self):
        collection = []

        cursor = None
        while True:
            library = self.library_get_items(10000, cursor=cursor)
            collection.extend(library["items"])
            cursor = library.get("cursor")
            if not cursor:
                break

        return collection

    def library_get_all_track_ids(self):
        collection = self.library_get_all()
        return {item["pandoraId"] for item in collection if item["pandoraType"] == "TR"}