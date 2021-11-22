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
