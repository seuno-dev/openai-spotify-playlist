import json

import openai
import spotipy
from dotenv import dotenv_values
from flask import Flask, session, request, jsonify, render_template
from spotipy import FlaskSessionCacheHandler, SpotifyOauthError

config = dotenv_values(".env")

app = Flask(__name__, template_folder="templates")
app.secret_key = config["FLASK_SECRET_KEY"]

openai.api_key = config["OPENAI_SECRET_KEY"]

messages = [
    {"role": "system",
     "content": "You will create a list of songs and its artist based on user's input. "
                "The output format should in JSON array of object which have 2 fields, "
                "song and artist. Should return at least 10 songs. Separate the artists by comma instead of saying 'featuring'."},
    {"role": "user", "content": "romantic songs"},
    {"role": "assistant",
     "content": '[{"song": "Perfect", "artist": "Ed Sheeran"}, {"song": "All of Me", "artist": "John Legend"}, '
                '{"song": "Someone Like You", "artist": "Adele"}, {"song": "Fix You", "artist": "Coldplay"}, '
                '{"song": "I Will Always Love You", "artist": "Whitney Houston"}, '
                '{"song": "Breathe", "artist": "Lee Hi"}, {"song": "Something Just Like This", "artist": "The Chainsmokers, Coldplay"}, '
                '{"song": "Stay With Me", "artist": "Chanyeol"}, {"song": "Beautiful", "artist": "Crush"}, '
                '{"song": "Uptown Funk", "artist": "Mark Ronson, Bruno Mars"}]'}
]

spotify_client = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id=config["SPOTIFY_CLIENT_ID"],
        client_secret=config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri="http://127.0.0.1:9999",
        cache_handler=FlaskSessionCacheHandler(session),
        scope="playlist-modify-private"
    )
)


def get_tracks(gpt_playlist: list) -> list:
    spotify_tracks = []

    for gpt_track in gpt_playlist:
        spotify_track = spotify_client.search(q=f"{gpt_track['song']} artist:{gpt_track['artist']}", limit=1)
        track_items = spotify_track["tracks"]["items"]
        if len(track_items) == 0:
            print(gpt_track, "not found")
            continue
        spotify_tracks.append(track_items[0])

    return spotify_tracks


def get_track_artists(track) -> str:
    artists = ""
    for i, artist in enumerate(track['artists']):
        artists += f" {artist['name']}"
        if i != len(track['artists']) - 1:
            artists += ","
    return artists


def get_track_song(track) -> str:
    return track['name']


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_playlist():
    data = json.loads(request.data)
    query = data['query']

    try:
        spotify_user = spotify_client.current_user()
    except SpotifyOauthError:
        return jsonify({"error": "Failed to authenticate to Spotify!"}), 403

    prompt = [{"role": "user", "content": query}]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages + prompt,
        max_tokens=1024
    )

    gpt_playlist = json.loads(response["choices"][0]["message"]["content"])
    spotify_tracks = get_tracks(gpt_playlist)
    if len(spotify_tracks) > 0:
        spotify_playlist = spotify_client.user_playlist_create(spotify_user["id"], public=False, name=query)
        spotify_client.playlist_add_items(spotify_playlist["id"], [track['id'] for track in spotify_tracks])

        tracks = [{"artist": get_track_artists(track), "song": get_track_song(track)} for track in spotify_tracks]
        return jsonify({"playlist_url": spotify_playlist['external_urls']['spotify'], "tracks": tracks})


if __name__ == '__main__':
    app.run()
