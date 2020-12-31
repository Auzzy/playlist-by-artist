import argparse

from playlistmanager import createplaylist
from playlistmanager.musicbrainz import AlbumSorter, Filter

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("artist", help="Create a playlist of this artist's releases.")
    parser.add_argument("--auth-token")

    parser.add_argument("--match-threshhold", type=int, choices=range(1, 101), metavar="{1..100}", default=85,
            help="Minimum MusicBrainz score to be considered a match. Default: %(default)s.")

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

    createplaylist.discography_playlist_cli(
        args["artist"], args["match_threshhold"], args["filter"], args["sorter"], token=args["auth_token"])