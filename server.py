from urllib.parse import parse_qsl
from datetime import datetime
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import sqlite3
import time
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
		c = db.cursor()
		# Grab last 5 messages from last day
		c.execute("select date, name, message, colour from chat where date > ? order by date desc limit 5", [str(int(time.time() - 86400))])
		prev_msg = []
		for pm in c.fetchall():
			prev_msg.append(render_message(datetime.fromtimestamp(pm[0]), pm[3], pm[1], pm[2]))
		self.write_message("".join(prev_msg[::-1]))
		c.close()

	def on_message(self, ws_message):
		c = db.cursor()
		ws_data = dict(parse_qsl(ws_message))
		# Name validation
		if "name" not in ws_data:
			self.write_message('<div class="fw-500" style="color: red">Error: Name field not filled out</div>')
			return
		if len(ws_data["name"]) > 25:
			self.write_message('<div class="fw-500" style="color: red">Error: Name is too long</div>')
			return
		# IP Address Validation
		c.execute("select * from chat where name = ? and ip != ? and date > ?",
			[ws_data["name"], self.request.remote_ip, str(int(time.time() - 604800))]).rowcount
		if len(c.fetchall()):
			self.write_message('<div class="fw-500" style="color: red">Error: Another IP address used that name in the last 7 days</div>')
			return
		# Message Validation
		if "message" not in ws_data:
			ws_data["message"] = ""
		# Colour Validation
		if ws_data["colour"] not in VALID_COLOURS:
			ws_data["colour"] = VALID_COLOURS[0]
		# Send Message
		message = cgi.escape(ws_data["message"])
		c.execute("insert into chat (date, name, message, colour, ip) values (?, ?, ?, ?, ?)",
					[str(int(time.time())), cgi.escape(ws_data["name"]), cgi.escape(ws_data["message"]), ws_data["colour"], self.request.remote_ip])
		db.commit()
		c.close()
		for socket in sockets:
			socket.write_message(render_message(datetime.now(), ws_data["colour"], cgi.escape(ws_data["name"]), cgi.escape(ws_data["message"])))

	def on_close(self):
		sockets.remove(self)

class WebHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("index.html")

def render_message(time, color, name, message):
	return '<div style="color: ' + color + '">[' + time.strftime('%H:%M:%S') + '] <strong>' + name + ':</strong> ' + message + '</div>'

application_sockets = tornado.web.Application([
	(r"/ws", WSHandler),
], debug=DEBUG)

application_web = tornado.web.Application([
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