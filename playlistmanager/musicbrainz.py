import collections
import requests
import time
from operator import itemgetter

from playlistmanager import __version__

DEFAULT_USER_AGENT = f"PlaylistManager/{__version__} (github.com/Auzzy/playlist-manager)"


class Filter:
    @staticmethod
    def create(**filter_args):
        request_filter = collections.defaultdict(set)
        if not filter_args.get("include_compilations") and not filter_args.get("include_all"):
            request_filter["secondary-types"].add("Compilation")
        if not filter_args.get("include_remixes") and not filter_args.get("include_all"):
            request_filter["secondary-types"].add("Remix")
        if not filter_args.get("include_live") and not filter_args.get("include_all"):
            request_filter["secondary-types"].add("Live")
        if not filter_args.get("include_soundtracks") and not filter_args.get("include_all"):
            request_filter["secondary-types"].add("Soundtrack")

        request_args = collections.defaultdict(set)
        if filter_args.get("include_eps") or filter_args.get("include_all"):
            request_args["types"].add("ep")
        if filter_args.get("include_singles") or filter_args.get("include_all"):
            request_args["types"].add("single")

        request_args["types"].add("album")

        return Filter(request_args, request_filter)

    def __init__(self, request_args, request_filter):
        self.request_args = request_args
        self.request_filter = request_filter

    def get_request_args(self):
        return {"types": self.request_args["types"].copy()}

    def post_request_filter(self, items):
        filtered_items = []
        for field, values in self.request_filter.items():
            for item in items[:]:
                if not any(value in item[field] for value in values):
                    filtered_items.append(item)
        return filtered_items


class Sorter:
    SORT_ORDER_ASC = "asc"
    SORT_ORDER_DESC  ="desc"
    SORT_ORDERS = (SORT_ORDER_ASC, SORT_ORDER_DESC)

    def __init__(self, field, order):
        self.field = field
        # Default to ascending
        self.order = Sorter.SORT_ORDER_DESC if order in ("desc", "descending") else Sorter.SORT_ORDER_ASC

        self._key_func = itemgetter(self.field) if self.field else None
        self._asc = self.order == Sorter.SORT_ORDER_ASC

    def sort(self, items):
        return sorted(items, key=self._key_func, reverse=not self._asc) if self._key_func else items

class AlbumSorter(Sorter):
    SORT_FIELDS = {
        "name": "title",
        "release": "first-release-date",
        "type": "primary-type",
        "subtypes": "secondary-types"
    }

    @staticmethod
    def create(**sort_args):
        sort_field = sort_args.get("sort_field", "release")
        sort_order = sort_args.get("sort_order") or Sorter.SORT_ORDER_ASC

        if sort_field:
            sort_value = AlbumSorter.SORT_FIELDS.get(sort_field)
            if not sort_value:
                raise ValueError(f"Unexpected sort field. Expected one of: {', '.join(AlbumSorter.SORT_FIELDS)}")
        else:
            sort_value = None

        if sort_order not in Sorter.SORT_ORDERS:
            raise ValueError(f"Unexpected sort order. Expected one of: {', '.join(Sorter.SORT_ORDERS)}")

        return AlbumSorter(sort_value, sort_order)


class MusicBrainz:
    BASE_API = "https://musicbrainz.org/ws/2"

    @staticmethod
    def connect(user_agent=DEFAULT_USER_AGENT):
        session = requests.Session()
        session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json"
        })
        return MusicBrainz(session)

    def __init__(self, session):
        self.session = session

    def _request(self, endpoint, params={}):
        while True:
            response = self.session.get(f"{MusicBrainz.BASE_API}/{endpoint}", params={**params, "fmt": "json"})
            if response.status_code != 503:
                break

            time.sleep(1)
        return response.json()

    def search_artist(self, name, threshhold=0):
        search_name = name.replace(" ", "+")
        result = self._request("artist", {"query": search_name})
        return [artist for artist in result["artists"] if artist["score"] >= threshhold]

    def lookup(self, resource, id, *, inc=None):
        params = {"inc": inc} if inc else {}
        return self._request(f"{resource}/{id}", params)


    def browse(self, endpoint, params, *, limit=20, offset=0, inc=None):
        return self._request(endpoint, {"limit": limit, "offset": offset, "inc": inc, **params})

    def browse_release_groups(self, *, artist_id=None, collection_id=None, release_id=None, status=None, types=[], **kwargs):
        return self.browse("release-group", {
                "inc": "artist-credits+aliases",
                "artist": artist_id,
                "collection_id": collection_id,
                "release": release_id,
                "type": '|'.join(types),
                "status": status
            },
            **kwargs)

    ### Higher-level operations

    def get_artist(self, artist_id):
        return self.lookup("artist", artist_id)

    def get_all_artist_albums(self, artist_id, *, filter_=Filter.create(), sorter=AlbumSorter.create()):
        all_albums = []
        while True:
            params = {
                "artist_id": artist_id,
                "limit": 100,
                "offset": len(all_albums),
                **filter_.get_request_args()
            }
            albums_result = self.browse_release_groups(**params)
            all_albums.extend(albums_result["release-groups"])
            if len(all_albums) >= albums_result["release-group-count"]:
                break

            # Slow down to avoid exceeding the rate limit
            time.sleep(2)

        all_albums = filter_.post_request_filter(all_albums)
        all_albums = sorter.sort(all_albums)
        return all_albums

    def get_artist_albums_info(self, artist_id, release_filter=Filter.create(), album_sorter=AlbumSorter.create()):
        albums_info = self.get_all_artist_albums(artist_id, filter_=release_filter, sorter=album_sorter)

        # The name an artist uses for a release may be an alias. Since Pandora
        # treats different names as separate artists (usually), the name on the
        # release needs to be used for searching. That's also why we use
        # "artist-credit.*.name" instead of "artist-credit.*.artist.name"
        # Keeping it a list retains the order returned by get_all_artist_albums().
        get_artist_names = lambda album: [artist["name"] for artist in album["artist-credit"]]
        get_album_aliases = lambda album: [alias["name"] for alias in album["aliases"]]
        return [{"artists": get_artist_names(album), "title": album["title"], "aliases": get_album_aliases(album)} for album in albums_info]

    def get_artist_links(self, id):
        relations = self.lookup("artist", id, inc="url-rels")["relations"]
        relations_by_type = collections.defaultdict(list)
        for relation in relations:
            relations_by_type[relation["type"]].append(relation["url"]["resource"])
        return dict(relations_by_type)
