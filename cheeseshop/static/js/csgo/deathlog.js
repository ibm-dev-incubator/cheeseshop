var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var port = process.env.PORT || 3000;
var bodyParser = require('body-parser');
app.use(bodyParser.json()); // for parsing application/json

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

app.post('/gsi', function(req, res){
  console.log("got a post request");
  io.emit('chat message', req.body);
  //Object.keys(req.body).forEach(function(key){
  //  io.emit('chat message', key + JSON.stringify(req.body[key]));
 // });
  res.sendFile(__dirname + '/response.html');
});


io.on('connection', function(socket){
  socket.on('chat message', function(msg){
    io.emit('chat message', msg);
  });
});

http.listen(port, function(){
  console.log('listening on *:' + port);
});
