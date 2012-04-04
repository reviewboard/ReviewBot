import tornado.httpserver
import tornado.ioloop
import tornado.web

from reviewbot.server import handlers

application = tornado.web.Application([
    (r"/", handlers.MainHandler),
    (r"/review_request_published/", handlers.PublishedHandler),
])


class ReviewBotHTTPServer(object):

    def __init__(self):
        self.http_server = tornado.httpserver.HTTPServer(application)
        self.http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()
