const { io } = require("socket.io-client");

const socketUrl = "http://localhost:8000";
const roomId = process.env.ROOM_ID || 1;
const clientName = process.env.CLIENT_NAME || "A";

const socket = io(socketUrl, {
  transports: ["websocket"],
});

socket.on("connect", () => {
  console.log(`[${clientName}] connected`, socket.id);
  socket.emit("join_room_socket", { room_id: roomId });
});

socket.on("system_message", (data) => {
  console.log(`[${clientName}] system_message`, data);
});

["chat_message", "whiteboard_update", "quiz_start", "quiz_answer", "presence_update"].forEach((ev) => {
  socket.on(ev, (data) => {
    console.log(`[${clientName}] ${ev}`, JSON.stringify(data));
  });
});

process.stdin.setEncoding("utf8");
console.log(`[${clientName}] Type commands: whiteboard, quizstart, quizanswer, presence, chat, exit`);

process.stdin.on("data", (chunk) => {
  const cmd = chunk.trim();
  if (cmd === "whiteboard") {
    socket.emit("whiteboard_update", {
      room_id: roomId,
      user_id: 123,
      strokes: [{ x: 0, y: 0, x2: 10, y2: 10 }],
      page: 1,
      color: "#ff0000",
    });
  } else if (cmd === "quizstart") {
    socket.emit("quiz_start", {
      room_id: roomId,
      quiz_id: 1,
      started_by: 123,
    });
  } else if (cmd === "quizanswer") {
    socket.emit("quiz_answer", {
      room_id: roomId,
      quiz_id: 1,
      question_id: 1,
      user_id: 123,
      selected_index: 2,
      response_time_ms: 1500,
    });
  } else if (cmd === "presence") {
    socket.emit("presence_update", {
      room_id: roomId,
      user_id: 123,
      status: "active",
      tab_visible: true,
    });
  } else if (cmd === "chat") {
    socket.emit("chat_message", {
      message: `Hello from client ${clientName}`,
    });
  } else if (cmd === "exit") {
    socket.close();
    process.exit(0);
  } else {
    console.log("Commands: whiteboard, quizstart, quizanswer, presence, chat, exit");
  }
});
