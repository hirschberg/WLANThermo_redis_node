var connect = require('connect'),
    express = require('express'),
    cors = require('cors'),
    serveStatic = require('serve-static'),
    socket = require('socket.io'),
    redis = require('redis'),
    bodyParser = require('body-parser'),
    child_process = require('child_process'),
    apn = require('apn'),
    set = '',
    pushTokens = ['887f2152de9bd8d71a0cac293fcdfa79e1eaf5e12109d813360a85e1d958efaf'];

var app = express();
app.use(cors());
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies

var server = app.use(serveStatic(__dirname+'/../client')).
    listen(8080);

/* REDIS */
var rclient = redis.createClient();
rclient.subscribe("clientdata");
var settingsrclient = redis.createClient();

rclient.on("error", function (err) {
    console.log("Error " + err);
});

rclient.on("subscribe", function (channel, count) {
    console.log("Subscription to Clientdata OK");
    var settingtypes = ['daemon_logging','display','email','logging','measure','pitmaster','push','sound','version','webcam'];
    var clientsettings = {};
    settingtypes.forEach(function(entry,i) {
        settingsrclient.hgetall('config:'+entry, function(err, results) {
            if (err) {
                // do something like callback(err) or whatever
                console.log(err);
            } else {
                // do something with results
                clientsettings[entry] = results;
                //console.log(results);

                if (i === settingtypes.length - 1) {
                    set = JSON.stringify(clientsettings);
                    console.log(set);
                }
            }
        });
        //hier kommt nichts an --> objekt/Array????
        console.log(i + "/" + settingtypes.length);

    });
    

});

/* REDIS End */

/* APN */
var apnService = new apn.connection({ production: false, cert: './certs/cert.pem', key: './certs/key.pem' });
console.log('apn');
apnService.on("connected", function() {
    console.log(" APN Connected");
});

apnService.on("transmissionError", function(errCode, notification, device) {
    console.error("Notification caused error: " + errCode + " for device ", device, notification);
    if (errCode === 8) {
        console.log("A error code of 8 indicates that the device token is invalid. This could be for a number of reasons - are you using the correct environment? i.e. Production vs. Sandbox");
    }
});

apnService.on("timeout", function () {
    console.log("APN Connection Timeout");
});

apnService.on("disconnected", function() {
    console.log("Disconnected from APNS");
});

apnService.on("socketError", function() {
    //console.error;
    console.log('socketerror');
});

apnService.on("error", function() {
    //console.error;
    console.log('error');
});


// If you plan on sending identical paylods to many devices you can do something like this.
function pushNotificationToMany(text) {
    console.log("Sending the same notification each of the devices with one call to pushNotification.");
    var note = new apn.notification();
    note.setAlertText(text);
    note.badge = 1;
    note.sound = 'default';

    apnService.pushNotification(note, pushTokens);
}

pushNotificationToMany("Hello, WLAN-Thermo wurde gestartet!");

/* APN End */


var io = socket.listen(server);

io.on('connection', function(socket) {

	console.log('client connected');
    socket.emit('clientsettings',set);

/*    setTimeout(function() {
        socket.emit('hello', 'paul');
        console.log('sent out an hello');
    }, 1000);*/
});

    io.on('ready', function(socket) {
        socket.broadcast.emit('ready');
        console.log('got an ready message');
    });

    rclient.on("message", function (channel, message) {
            console.log("client channel " + channel + ": " + message);
            //socket.emit('socktemp', message);

            if (channel == 'clientdata') {
                var sensorData = JSON.parse(message);
                //console.log(sensorData);
                for (var key in sensorData.sensors){
                    if(sensorData.sensors[key].current != 999.9 && sensorData.sensors[key].current > sensorData.sensors[key].temp_max) {
                        console.log('sensor übertemp',key, sensorData.sensors[key].current);
                        sensorData.sensors[key].warning = 'hot';
                        if (sensorData.sensors[key].web_alert == 'true') {
                            pushNotificationToMany('Sensor '+sensorData.sensors[key].name+' hat Übertemperatur :'+sensorData.sensors[key].current);
                        }
                    }
                    else if (sensorData.sensors[key].current != 999.9 && sensorData.sensors[key].current < sensorData.sensors[key].temp_min) {
                        console.log('sensor untertemp',key, sensorData.sensors[key].current);
                        sensorData.sensors[key].warning = 'cold';
                        if (sensorData.sensors[key].web_alert == 'true') {
                            pushNotificationToMany('Sensor '+sensorData.sensors[key].name+' hat Untertemperatur :'+sensorData.sensors[key].current);
                        }
                    }
                }
                console.log(sensorData);
            }

            io.emit('socktemp',JSON.stringify(sensorData));
    });

    io.on('disconnect', function () {
        socket.broadcast.emit('user disconnected');
    });


//});

// CORS (Cross-Origin Resource Sharing) headers to support Cross-site HTTP requests

/*server.all('*', function(req, res, next) {
       res.header("Access-Control-Allow-Origin", "*");
       res.header("Access-Control-Allow-Headers", "X-Requested-With");
       res.header('Access-Control-Allow-Headers', 'Content-Type');
       next();
});*/

app.post('/settings/', function(req,res, next) {
    console.log(req.body);
    var request = req.body;
    console.log('----------- Jetzt kommt der Loop _____________');
    for(var attributename in request){
        //console.log(attributename+": "+request[attributename]);
        for(var subattributename in request[attributename]){
            console.log(attributename+":"+subattributename+" "+request[attributename][subattributename]);
            settingsrclient.hset("config:"+attributename, subattributename, request[attributename][subattributename]);
        }
    }
    settingsrclient.hset("config:push", "active", "0", redis.print);
    res.send('hallo');
    //hier soll der Speichervorgang der Einstellungen erfolgen
    next();
});

app.post('/sensorsettings/', function(req,res, next) {
    res.send('sensorsettings'+req.body.id+' saved');
    for(var attributename in req.body){
        if(attributename == 'id'){
            continue;
        }
        console.log("sensors:"+req.body.id+":"+attributename+" "+req.body[attributename]);
        settingsrclient.hset("sensors:"+req.body.id, attributename, req.body[attributename]);
    }
});

app.post('/timer/', function(req,res,next) {
    res.send('timer set');
/**

    TODO:
    - Timer setup
    - hier vielleicht einen Socket emit absenden für die verbundenen Clients

 */

});


app.post('/log/', function(req,res,next) {
    var returnVal = [];
    settingsrclient.lrange('log:temp',0,100, function(error, logs) {
        if (error) {
            console.log('Error: '+ error);
        } else {

            logs.forEach(function(log,i){
                singleEntry = JSON.parse(log);
                returnVal.push(singleEntry);
                //console.log("log: " + singleEntry[0].time);

                if(i === logs.length-1) {
                    res.send(JSON.stringify(returnVal));
                    console.log(JSON.stringify(returnVal));
                }
            });
        }
    });
    console.log('query log');
    
/**

    TODO:
    - Timer setup
    - hier vielleicht einen Socket emit absenden für die verbundenen Clients

 */

});


app.post('/pushtoken/', function(req,res,next) {
    res.send('got token '+req.body.token);
    //console.log(req.body.token);
    pushTokens.push(req.body.token);
    console.log(pushTokens);
/**

    TODO:
    - Timer setup
    - hier vielleicht einen Socket emit absenden für die verbundenen Clients

 */

});

/** SHUTDOWN funktioniert **/
app.post('/shutdown/', function(req,res,next) {
    child_process.exec('shutdown', function(err, stdout, stderr){
        console.log(err);
        console.log(stdout);
        console.log(stderr);
    });
    res.send('shutdown set');
});
/** REBOOT funktioniert **/
app.post('/reboot/', function(req,res,next) {
    child_process.exec('reboot', function(err, stdout, stderr){
        console.log(err);
        console.log(stdout);
        console.log(stderr);
    });
    res.send('reboot set');
});


console.log("Server started and listen to http://127.0.0.1:8080");