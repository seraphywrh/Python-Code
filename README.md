# Python-Code

## Cloud Based Multi-player Game

Designed a cloud-based game which can be played by 2 players simultaneously.

Used ZMQ to provide function of sockets by which clients and the server can send messages to each other.

   - Publish-Subscribe pattern of ZMQ.
   - Games run on local clients.
   - Clients gather messages and player’s input and send to server.
   - Once the server receives a message, it sends this message to all clients.
   - All clients react to commands from server.

Imported pygame library to realize game functions.

Built the computing server on EC2.

## Web Server & Client

Implemented socket-based web server&client.
 
Client sends HTTP protocol messages to the erver.

The server listens on a specified port and returns response messages to the client.

Supports 200, 404, and 501 status codes.

## Reliable UDP

 Created a reliable message protocol over UDP.

 Implemented the TCP-like 3-way handshake protocol.

 Reliable tearing down of the connection.