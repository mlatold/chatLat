from urllib.parse import parse_qsl
from datetime import datetime
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import sqlite3
from time import time
import cgi
import os
PATH = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
VALID_COLOURS = ["black", "blue", "red", "orange", "green", "purple", "brown"]
sockets = []
db = sqlite3.connect('chat.db')

class WSHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		sockets.append(self)

	def on_message(self, ws_message):
		ws_data = dict(parse_qsl(ws_message))
		if "name" not in ws_data:
			return
		if "message" not in ws_data:
			ws_data["message"] = ""
		if ws_data["colour"] not in VALID_COLOURS:
			ws_data["colour"] = VALID_COLOURS[0]
		message = cgi.escape(ws_data["message"])
		time = "[" + datetime.now().strftime('%H:%M:%S') + "] "
		c = db.cursor()
		c.execute("insert into chat (date, name, message) values (?, ?, ?)", [str(int(time())), ws_data["name"], message])
		db.commit()
		c.close()
		for socket in sockets:
			socket.write_message('<div style="color: ' + ws_data["colour"] + '">' + time + '<strong>' + ws_data["name"] + ':</strong> ' + message + '</div>')

	def on_close(self):
		sockets.remove(self)

class WebHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html")

application_sockets = tornado.web.Application([
	(r"/ws", WSHandler),
], debug=DEBUG)

application_web = tornado.web.Application([
	(r"/fonts/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(PATH, "fonts")}),
	(r"/css/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(PATH, "css")}),
	(r"/js/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(PATH, "js")}),
	(r"/", WebHandler)
], debug=DEBUG)

if __name__ == "__main__":
	http_server = tornado.httpserver.HTTPServer(application_sockets)
	http_server.listen(8888)

	http_server = tornado.httpserver.HTTPServer(application_web)
	http_server.listen(8080)

	tornado.ioloop.IOLoop.instance().start()