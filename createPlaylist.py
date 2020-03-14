"""
Step1: Log into youtube
Step2: Grab liked videos
Step3: create new playlist
Step4: Search song
Step 5:Add song to the playlist
"""
import json
import requests
import os

from secrets import spotify_user_id
from secrets import spotifytoken
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

class CreatePlaylist:

    def __init__(self):
        self.user_id= spotify_user_id
        self.spotify_token= spotifytoken
        self.youtube_client= self.getYoutubeClient()
        self.all_song_info ={}

    #Log into youtube
    def getYoutubeClient(self):
        #copied from Youtube data api
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()
        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

        return youtube_client
    #Grab liked videos and creating a dictionary of important info
    def getLikedVideos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response=request.execute()

        #collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url= "https://www.youtube.com/watch?v{}".format(item["id"])

            #use youtube_dl to collect song name and artist
            video= youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            track= video["track"]
            artist = video["artist"]

            #save the important info
            self.all_song_info[video_title]= {
                "youtube_url": youtube_url,
                "track":track,
                "artist":artist,
                #add the uri
                "spotify_uri":self.getSpotifyUri(track,artist)
            }
    #Create new playlist
    def createPlaylist(self):

        requestBody= json.dumps({
            "name":"Youtube Liked Videos",
            "description":"All Liked Youtube Videos",
            "public":True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data= requestBody,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(self.spotify_token)
            }
        )
        response_json= response.json()
        return response_json["id"]

    #Search song
    def getSpotifyUri(self,track,artist):
        requestBody = json.dumps({
            "name": "Youtube Liked Videos",
            "description": "All Liked Youtube Videos",
            "public": True
        })
        query="https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}+type=offset=0limit=20".format(
            track,
            artist
        )
        response = requests.post(
            query,
            data=requestBody,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        songs= response_json["tracks"]["items"]


        #only use the first song
        uri= songs[0]["uri"]
        return uri


    #Add song
    def addSongToPlaylist(self):
        #populate our song dictionary
        self.getLikedVideos()
        #collect all of uri
        uris=[]
        for song,info in self.all_song_info.items():
            uris.append(info["spotify_uri"])
        #create a new playlist
        playlist_id=self.createPlaylist()
        #add all songs into new playlist
        request_data= json.dumps(uris)

        query= "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response= requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        return response_json

    if __name__ == '__main__':
        cp = createPlaylist()
        cp.add_song_to_playlist()