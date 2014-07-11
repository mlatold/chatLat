ChatLat
=======

A simple sockets chat application in Python. It runs on the Tornado framework.

It uses SQLite3 to store chat messages, and will assosiate your username with your IP address for 7 days. Upon loading the application, it will retrieve the last 5 messages in the last day.
