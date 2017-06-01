import webapp2
import json


class BufferFile(object):
    def __init__(self, limit=1000, filename="likes.csv"):
        self.filename = filename
        self.limit = limit
        self.ids = []
        self.stats = {}

    @property
    def size(self):
        return len(self.ids)

    def like(self, id):
        self.__process(id, "likes")

    def dislike(self, id):
        self.__process(id, "dislikes")

    def __process(self, id, opinion):
        self.free()
        if id not in self.stats:
            self.ids.append(id)
            self.stats[id] = {"likes": 0, "dislikes": 0}
        self.stats[id][opinion] += 1
        self.write("{},{}".format(id, opinion))

    def free(self):
        if self.size > self.limit:
            del self.stats[self.ids[0]]
            del self.ids[0]

    def write(self, messsage):
        with open(self.filename, "a") as f:
            f.write(messsage + "\n")

    def get(self, id):
        if id in self.stats:
            d = self.stats[id]
            return (d["likes"], d["dislikes"])
        else:
            return (0, 0)


class Handler(webapp2.RequestHandler):
    def get(self, id, script):
        buff = self.app.config.get("BufferFile")
        if script == "script.js":
            # Javascript
            likes, dislikes = buff.get(id)
            self.response.content_type = "text/javascript"
            self.response.write(
                "likes = {}; dislikes = {};".format(likes, dislikes)
            )
        else:
            # Html
            self.response.content_type = "text/html"
            opinion = self.request.get("opinion")
            if opinion == "like":
                buff.like(id)
            if opinion == "dislike":
                buff.dislike(id)
            with open("stats.html") as f:
                self.response.write("\n".join(f.readlines()))


app = webapp2.WSGIApplication([
    webapp2.Route('/<:(\d)+>/<:(script\.js)?>', Handler,  methods=['GET'])
], debug=False, config={"BufferFile": BufferFile()})


def main(host, port):
    from paste import httpserver
    httpserver.serve(app, host=host, port=port)


if __name__ == '__main__':
    import os
    dir = os.path.dirname(__file__)
    if dir != "":
        os.chdir(dir)
    with open("config.json") as f:
        config = json.load(f)
    main(config["host"], config["port"])
