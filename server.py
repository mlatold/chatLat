from urllib.urlparse import urlparse, parse_qsl
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import os

PATH = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
sockets = []

class WSHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print('new connection', self)
		self.write_message("Hello World")
		sockets.append(self)

	def on_message(self, message):
		print('message received %s' % parse_qsl(urlparse(message)[4]))

	def on_close(self):
		print('connection closed')

class WebHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html")

application_sockets = tornado.web.Application([
	(r'/ws', WSHandler),
], debug=DEBUG)

application_web = tornado.web.Application([
	(r'/fonts/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, 'fonts')}),
	(r'/css/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, 'css')}),
	(r'/js/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, 'js')}),
	(r'/', WebHandler)
], debug=DEBUG)

if __name__ == "__main__":
	http_server = tornado.httpserver.HTTPServer(application_sockets)
	http_server.listen(8888)

	http_server = tornado.httpserver.HTTPServer(application_web)
	http_server.listen(8080)

	tornado.ioloop.IOLoop.instance().start()