const io = require('socket.io-client');
const readline = require('readline');

const rl = readline.createInterface({input: process.stdin, output: process.stdout});
const socket = io('http://localhost:8000', {transports: ['websocket']});

socket.on('connect', () => {
  console.log('Connected:', socket.id);
  rl.question('Room ID? ', (roomId) => {
    socket.emit('joinroom', {roomid: parseInt(roomId)});
    rl.on('line', (line) => {
      if (line === 'exit') rl.close();
      else socket.emit('chatmessage', {message: line, roomid: parseInt(roomId)});
    });
  });
});

socket.on('chatmessage', (data) => console.log('← Chat:', data));
socket.on('disconnect', () => console.log('Disconnected'));
