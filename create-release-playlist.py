import argparse
import collections

from musicbrainz import AlbumSorter, Filter, MusicBrainz
from pandora import Pandora

USER_AGENT = "PandoraPlaylistManager/0.1"


def create_playlist(pandora, artist_name, albums_by_name, name_format="{artist} Discography"):
    album_ids = []
    for name, albums in albums_by_name.items():
        if not albums:
            print(f"Could not find \"{name}\" on Pandora. Skipping.")
            continue

        for album in albums:
            if album["pandoraId"] in album_ids:
                print(f"Duplicate album ID. Probably couldn't find \"{name}\" on Pandora, so search turned up another album by {artist_name}. Skipping.")
                continue

            album_ids.append(album["pandoraId"])

    playlist_info = pandora.playlist_create(name_format.format(artist=artist_name))
    pandora.playlist_append(playlist_info, album_ids, update_info=True)

def get_pandora_albums(pandora, albums_info):
    albums_by_artists = collections.defaultdict(set)
    # Partition album info by artist name(s).
    for album_info in albums_info:
        albums_by_artists[" ".join(album_info["artists"])].update([album_info["title"]] + album_info["aliases"])

    # Pandora is inconsistent with its handling of multi-artist albums, likely
    # driven by licensing. Some show up  under one artist but not the other,
    # some are joined to form a new artist. So we load the albums associated
    # with each artist that match the requested names, and sort them out after.
    artist_cache = {}
    for artist_name, album_names in albums_by_artists.items():
        if artist_name not in artist_cache:
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

def _prompt_for_artist(matches, artist_name):
    print(f"MusicBrainz found multiple artists matching \"{artist_name}\". Please select one:")
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

def _match_artists(musicbrainz, artist_name, match_threshhold):
    search_result = musicbrainz.search_artist(artist_name)

    matches = [artist for artist in search_result["artists"] if artist["score"] >= match_threshhold]
    if len(matches) > 1:
        return _prompt_for_artist(matches, artist_name)
    else:
        return matches[0]

def get_artist_albums_info(musicbrainz, artist_name, match_threshhold, release_filter, album_sorter):
    artist = _match_artists(musicbrainz, artist_name, match_threshhold)
    albums_info = musicbrainz.get_all_artist_albums(artist["id"],
            filter_=release_filter,
            sorter=album_sorter)

    # The name an artists uses for a release may be an alias. Since Pandora
    # treats different names as separate arists (usually), the name on the
    # release needs to be used for searching. That's also why we use
    # "artist-credit.*.name" instead of "artist-credit.*.artist.name"
    # Keeping it a list retains the order returned by get_all_artist_albums().
    get_artist_names = lambda album: [artist["name"] for artist in album["artist-credit"]]
    get_album_aliases = lambda album: [alias["name"] for alias in album["aliases"]]
    return [{"artists": get_artist_names(album), "title": album["title"], "aliases": get_album_aliases(album)} for album in albums_info]

def main(artist_name, match_threshhold, release_filter, album_sorter):
    musicbrainz = MusicBrainz.connect(USER_AGENT)
    pandora = Pandora.connect()

    albums_info = get_artist_albums_info(musicbrainz, artist_name, match_threshhold, release_filter, album_sorter)
    albums = get_pandora_albums(pandora, albums_info)
    create_playlist(pandora, artist_name, albums)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("artist", help="Create a playlist of this artist's releases.")
    parser.add_argument("--match-threshhold", type=int, choices=range(1, 101), metavar="{1..100}", default=85,
            help="Minimum MusicBrainz score to be considered a match. Default: %(default).")

    parser.add_argument("--sort-field", default="release")
    parser.add_argument("--sort-order", default=AlbumSorter.SORT_ORDER_ASC)
    parser.add_argument("--no-sort", action="store_false", dest="sort")

    filter_group = parser.add_argument_group("Filters", "Customize types of releases to be included.")
    filter_group.add_argument("--include-compilations", action="store_true")
    filter_group.add_argument("--include-remixes", action="store_true")
    filter_group.add_argument("--include-live", action="store_true")
    filter_group.add_argument("--include-soundtracks", action="store_true")
    filter_group.add_argument("--include-eps", action="store_true")
    filter_group.add_argument("--include-singles", action="store_true")
    filter_group.add_argument("--include-all", action="store_true")

    args = vars(parser.parse_args())

    album_filter = Filter.create(**args)
    album_sorter = AlbumSorter.create(**args) if args["sort"] else AlbumSorter.create(sort_field=None)

    return {**args, "filter": album_filter, "sorter": album_sorter}

if __name__ == "__main__":
    args = parse_args()

    main(args["artist"], args["match_threshhold"], args["filter"], args["sorter"])
