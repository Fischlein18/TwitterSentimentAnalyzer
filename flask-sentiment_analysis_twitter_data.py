from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob

import twitter_credentials

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re

from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

# # # # TWITTER CLIENT # # # #
class TwitterClient:
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(
            self.twitter_client.user_timeline, id=self.twitter_user
        ).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(
            num_friends
        ):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(
            self.twitter_client.home_timeline, id=self.twitter_user
        ).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets


# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator:
    def authenticate_twitter_app(self):
        auth = OAuthHandler(
            twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET
        )
        auth.set_access_token(
            twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET
        )
        return auth


# # # # TWITTER STREAMER # # # #
class TwitterStreamer:
    """
    Class for streaming and processing live tweets.
    """

    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords:
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """

    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, "a") as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True

    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)


# # # # TWEET SENTiMENT ANALYZER # # # #
class TweetAnalyzer:
    """
    Functionality for analyzing and categorizing content from tweets.
    """

    def clean_tweet(self, tweet):
        return " ".join(
            re.sub(
                "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet
            ).split()
        )

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))

        # if analysis.sentiment.polarity > 0:
        #     return 1
        # elif analysis.sentiment.polarity == 0:
        #     return 0
        # else:
        #     return -1

        return analysis.sentiment.polarity

    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=["tweets"])

        df["id"] = np.array([tweet.id for tweet in tweets])
        df["len"] = np.array([len(tweet.text) for tweet in tweets])
        df["date"] = np.array([tweet.created_at for tweet in tweets])
        df["source"] = np.array([tweet.source for tweet in tweets])
        df["likes"] = np.array([tweet.favorite_count for tweet in tweets])
        df["retweets"] = np.array([tweet.retweet_count for tweet in tweets])

        return df


class TwitterSentiment(Resource):
    def get(self):
        return {"about": "Twitter Sentiment Analyzer!"}


class TwitterSentimentAccount(Resource):
    def get(self, acc_name):
        twitter_client = TwitterClient()
        tweet_analyzer = TweetAnalyzer()

        api = twitter_client.get_twitter_client_api()

        tweets = api.user_timeline(screen_name=acc_name, count=20)

        df = tweet_analyzer.tweets_to_data_frame(tweets)
        df["sentiment"] = np.array(
            [tweet_analyzer.analyze_sentiment(tweet) for tweet in df["tweets"]]
        )

        return (
            {
                "average sentiment": df["sentiment"].mean(),
                "number of positive tweets": len(df.loc[df["sentiment"] > 0]),
                "number of non-positive tweets": len(df.loc[df["sentiment"] <= 0]),
                "number of re-tweets": int(df["retweets"].sum()),
            },
            201,
        )


class TwitterSentimentHashtag(Resource):
    def get(self, hashtag):
        twitter_client = TwitterClient()
        tweet_analyzer = TweetAnalyzer()

        api = twitter_client.get_twitter_client_api()

        tweets = api.search(q="#SAP", since="2019-06-02", lang="en")

        df = tweet_analyzer.tweets_to_data_frame(tweets)
        df["sentiment"] = np.array(
            [tweet_analyzer.analyze_sentiment(tweet) for tweet in df["tweets"]]
        )

        return (
            {
                "average sentiment": df["sentiment"].mean(),
                "number of positive tweets": len(df.loc[df["sentiment"] > 0]),
                "number of non-positive tweets": len(df.loc[df["sentiment"] <= 0]),
                "number of re-tweets": int(df["retweets"].sum()),
            },
            201,
        )


class Recent(Resource):
    def get(self, num):
        return {"result": num * 10}


api.add_resource(TwitterSentiment, "/")
api.add_resource(TwitterSentimentAccount, "/twittersentimentaccount/<string:acc_name>")
api.add_resource(TwitterSentimentHashtag, "/twittersentimenthashtag/<string:hashtag>")

if __name__ == "__main__":
    app.run(debug=True)


# curl -v http://127.0.0.1:5000/twittersentimentaccount/realDonaldTrump
# curl -v http://127.0.0.1:5000/
