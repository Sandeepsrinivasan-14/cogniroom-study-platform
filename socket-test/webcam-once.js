const { io } = require("socket.io-client");

const ROOM_ID = process.env.ROOM_ID || "2";
const USER_ID = parseInt(process.env.USER_ID || "3", 10);
const LOAD    = parseFloat(process.env.LOAD || "0.7");

const socket = io("http://localhost:8000", {
  transports: ["websocket"],
});

socket.on("connect", () => {
  console.log("connected", socket.id);

  socket.emit("join_room_socket", { room_id: ROOM_ID });

  setTimeout(() => {
    console.log("emitting webcam_load_update", { room_id: ROOM_ID, user_id: USER_ID, load_score: LOAD });
    socket.emit("webcam_load_update", {
      room_id: ROOM_ID,
      user_id: USER_ID,
      load_score: LOAD,
    });
  }, 500);

  setTimeout(() => {
    console.log("disconnecting");
    socket.disconnect();
  }, 1500);
});

socket.on("connect_error", (err) => {
  console.error("connect_error", err.message);
});
