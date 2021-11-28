#### NAMES

A tuple of names which can refer to this service. Case-insensitive.


#### auth\_to\_config(auth: str)

Takes a string use for authentication and turns it into a config dictionary which can be used to create a client.


#### create\_client(client\_config: dict<str: object>)

Should return an actual client for the given service. That client is intended to be a lower level interface to the service than the operations afforded by this module.


#### get\_similar\_artists(artist\_id: str, client\_config: dict<str: object>)

Retrieve the list of names of artists considered similar or related by this service.


#### search\_artists(search\_name: str, client\_config: dict<str: object> = {}, \*, client: object = None):

Search the service for artists with the given name. The search should be limited to artists if there is an option. The client can either be passed by keyword argument, or the config can be provided to create a fresh one.

The return value should be a list of dicts, where each is some info about an artist who matches the search term. Each dict should contain:
- id - the service specific ID of the artist
- name - the name of the artist
- similar - a list of dicts containing artists similar to this artist. Each dict should contain:
    - id - the service specific ID of the artist
    - name - the name of the artist

Ideally, this list should be arranged from most relevant to least relevant. If the service does not provide such info, then the ordering it returns should be used.


#### create\_discography\_playlist(albums\_info: list<dict<str: str|list>>, artist\_links: dict<str: list<str>>, search\_name: str, client\_config: dict<str: object>, name\_format: str = "{artist} Discography")

Orchestrate the creation of a playlist of the artist's entire discography.

albums\_info should be a list of dicts containing info on the albums associated with this artist, in the order they should appear on the playlist, such as returned by *musicbrainz.get\_artist\_albums_info*. Each dict should contain:

- artists - a list of artist names who get credit for this album, allowing for split or co-authored albums
- title - the proper name of the album
- aliases - a list of other names by which this album is known. This is primarily used to account for differences in the way names appear across services.

artist\_links should be a dict mapping service name to a list of URLs which point directly to the artist's page on the named service, such as is returned by *musicbrainz.get\_artist\_links*

search\_name is the name of the artist whose discography we're building.

client\_config is a dict containing the info needed to create a client for this service, as is returned by auth\_to\_config.

name\_format is the format of the resulting playlist name. You can use "{artist}" as a placeholder for the artist's name.


#### create\_similar\_artists\_playlist(albums\_info\_by\_artist: dict<str: list<dict<str: str|list>>>, search\_name: str, client\_config: dict<str: object>, name\_format: str = "{artist} Similar Artists"):

Orchestrate the creation of a playlist of the entire discography of artists considered similar to the source artist.

albums\_info should be a dict of strings mapping a similar artist to a list of dicts containing info about their discography. Each album list should be in the order they should appear on the playlist, such as returned by *musicbrainz.get\_artist\_albums\_info*. Each dict should contain:

- artists - a list of artist names who get credit for this album, allowing for split or co-authored albums
- title - the proper name of the album
- aliases - a list of other names by which this album is known. This is primarily used to account for differences in the way names appear across services.

search\_name is the name of the artist whose discography we're building.

client\_config is a dict containing the info needed to create a client for this service, as is returned by auth\_to\_config.

name\_format is the format of the resulting playlist name. You can use "{artist}" as a placeholder for the artist's name.


#### update\_playlist(playlist\_id: str, item\_ids: list<str>, client\_config: dict<str: object>)

Set the playlist order and contents to match the list of item\_ids (see *get\_playlist\_info* below for more details on item\_id). This means moving and deleting tracks; there is no mechanism for adding tracks.

#### add\_playlist\_tracks\_to\_library(playlist\_id: str, item\_ids: list<str>, client\_config: dict<str: object>)

Add the tracks indicated by item\_ids to the user's library (see *get\_playlist\_info* below for more details on item\_id).

#### get\_playlists\_info(client\_config: dict<str: object>)

Produce a list of dicts containing info on the user's playlists.

Each dict should consist of:

- id - the service specific ID of the playlist
- name - the name of the playlist
- totalTracks - the number of tracks on the playlist (as an int)
- duration [optional] - the length of the playlist in seconds (as an int)

#### get\_playlist\_info(playlist\_id: str, client\_config: dict<str: object>)

Produce a dict of info about this playlist.

The dict should contain:

- name: the name of the playlist
- duration: the lengt of the playlist in seconds (as an int).
- tracks: a list of dicts containing info about each track in the playlist, in order. Each dict should contain:
    - track\_id - the service specific ID of the track
    - item\_id - the id of this track instance in this playlist. This is usually different from track_id, since a track may be repeated.
    - name - the human-readable name of the track
    - artist - the name of the artist. If there are multiple, they should be concatenated, preferably with a forward slash (/).
    - album - the name of the album this instance comes from.
    - duration - the length of this track in seconds (as an int)

#### get\_playlist\_tracks\_in\_library(playlist\_id: str, client\_config: dict<str: object>)

Get a dict mapping the track\_id to a bool indicating if it's in the user's library.
