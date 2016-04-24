/*var redis = require("redis"),
        client = redis.createClient();

    client.on("error", function (err) {
        console.log("Error " + err);
    });

    client.on("message", function (channel, message) {
        console.log("client channel " + channel + ": " + message);
    });

    client.subscribe("temperatures");

*/

    /*
    Node.js server script
    Required node packages: express, redis, socket.io
*/

 
var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var redis = require('redis');
var rclient = redis.createClient();
rclient.subscribe("temperatures");

rclient.on("error", function (err) {
    console.log("Error " + err);
});

rclient.on("subscribe", function (channel, count) {
    console.log("Subscription OK");
});

rclient.on("message", function (channel, message) {
        console.log("client channel " + channel + ": " + message);
        io.emit('socktemp', message);
});

app.get('/', function(req, res){
  res.sendfile('index.html');
});

    io.on('connection', function(socket) {
        console.log('a socket user connected');

        rclient.on("temperatures", function (channel, message) {
            console.log("client channel " + channel + ": " + message);
            io.emit('socktemp', message);
        });

        socket.on('disconnect', function(){
            console.log('user disconnected');
            rclient.unsubscribe("temperatures");
        });
    });
     
    http.listen(3000, function() {
        console.log('listen to Port 3000');
    });
 

        var subscribe = redis.createClient();
        subscribe.subscribe('temperatures');
 
        subscribe.on("message", function(channel, message) {
            client.send(message);
            console.log("client channel " + channel + ": " + message);
        });
 
        client.on('message', function(msg) {
        });
 
        client.on('disconnect', function() {
            subscribe.quit();
        });
    