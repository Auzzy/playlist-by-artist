from playlistmanager import cli
from playlistmanager.similar_artists_playlist import similar_artists_playlist_cli


if __name__ == "__main__":
    args = cli.parse_args()

    similar_artists_playlist_cli(
        args["service"], args["artist"], args["match_threshhold"], args["filter"], args["sorter"], args["auth"])
