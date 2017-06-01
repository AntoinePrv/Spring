#!/usr/bin/env python

import json
import tweepy
from ryver import Post
import logging
from random import randint
from os import path


class Tweet(Post):

    def __init__(self, tweet, config):
        super(Tweet, self).__init__()
        self.reviewUrl = config["reviewUrl"]
        self.genAttr(tweet)

    def genAttr(self, tweet):
        if not hasattr(self, "id"):
            self.id = tweet.id
            self.__raw = tweet._json
        if hasattr(tweet, "retweeted_status"):
            self.genAttr(tweet.retweeted_status)
        else:
            self.author = "Twitter - " + tweet.author.name
            self.author_image = tweet.author.profile_image_url_https
            self.text = tweet.full_text.encode("utf8")
            self.text += "\n\n_Give us feedback:_ "
            self.text += "[like]({0}/{1}/?opinion={2}) or [dislike]({0}/{1}/?opinion={3}) ?".format(
                self.reviewUrl,
                self.id,
                "like",
                "dislike"
            )
            self.text += self.__processEnding(tweet)

    def __processEnding(self, tweet):
        ending = ""
        if hasattr(tweet, "entities"):
            if "media" in tweet.entities:
                self.media = tweet.entities["media"]
                n = len(self.media)
                self.text = " ".join(self.text.split()[:-n])
                if len(self.media) > 0:
                    ending += " []({})".format(
                        self.media[0]["media_url_https"]
                    )
            if "urls" in tweet.entities:
                self.urls = tweet.entities["urls"]
                if len(self.urls) > 0:
                    ending = " []({})".format(self.urls[0]["url"]) + ending
        return ending

    def writeToFolder(self, folder):
        with open(path.join(folder, str(self.id) + ".json"), "w") as f:
            json.dump(self.__raw, f, indent=2, sort_keys=True)


class TwitterPuller(object):

    def __init__(self, **kwargs):
        with open("config.json") as f:
            self.config = json.load(f)
        self.config.update(kwargs)
        self.auth = tweepy.OAuthHandler(
            self.config["ConsumerKey"],
            self.config["ConsumerSecret"])
        self.auth.set_access_token(
            self.config["AccessToken"],
            self.config["AccessTokenSecret"])
        self.api = tweepy.API(self.auth)

    @property
    def lastId(self):
        return self.config["lastId"]

    @lastId.setter
    def lastId(self, x):
        self.config["lastId"] = x
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=2, sort_keys=True)

    def get(self, **kwargs):
        default = {
            "tweet_mode":       "extended",
            "count":            3,
            "include_entities": True,
            "result_type":      "popular",
            "since_id":         self.lastId,
        }
        default.update(kwargs)
        public_tweets = self.api.home_timeline(**default)
        public_tweets = map(lambda x: Tweet(x, self.config), public_tweets)
        if len(public_tweets) > 0:
            self.lastId = public_tweets[0].id
        return public_tweets


if __name__ == "__main__":
    import os
    dir = os.path.dirname(__file__)
    if dir != "":
        os.chdir(dir)

    # create logger
    logger = logging.getLogger("custom")
    logger.setLevel(logging.INFO)
    f = logging.FileHandler("main.log")
    f.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    # add formatter to ch
    f.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(f)

    try:
        pulled = TwitterPuller().get()
        n = len(pulled)
        logger.info("Pulled {} tweet(s)".format(n))
        for tweet in pulled:
            tweet.send()
            tweet.writeToFolder("history")
            logger.info(
                "Sent tweet {0} from {1}".format(
                    tweet.id,
                    tweet.author.encode("utf-8")
                ))
    except Exception as e:
        logger.error(e)
