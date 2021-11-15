from playlistmanager import cli
from playlistmanager.discography_playlist import discography_playlist_cli


if __name__ == "__main__":
    args = cli.parse_args()

    discography_playlist_cli(
        args["service"], args["artist"], args["match_threshhold"], args["filter"], args["sorter"], args["auth"])
