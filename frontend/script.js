function restartGame() {
  location.reload();
}

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

canvas.width = 800;
canvas.height = 800;

const centerX = canvas.width / 2;
const centerY = canvas.height / 2;

// Track Points
const trackPoints = [
  { x: centerX - 200, y: centerY - 300 },
  { x: centerX + 250, y: centerY - 250 },
  { x: centerX + 350, y: centerY },
  { x: centerX + 200, y: centerY + 250 },
  { x: centerX - 150, y: centerY + 300 },
  { x: centerX - 350, y: centerY + 100 },
];

const outerTrackRadius = 400;
const innerTrackRadius = 250;

const carImages = {
  player1: new Image(),
  player2: new Image(),
};

carImages.player1.src = "car1.png";
carImages.player2.src = "car2.png";

// const winnerOverlay = document.createElement("div");
// winnerOverlay.id = "winner-overlay";
// winnerOverlay.style.cssText = `
//     display: none;
//     position: fixed;
//     top: 0;
//     left: 0;
//     width: 100%;
//     height: 100%;
//     background: rgba(0, 0, 0, 0.7);
//     z-index: 1000;
//     justify-content: center;
//     align-items: center;
// `;

// const winnerModal = document.createElement("div");
// winnerModal.style.cssText = `
//     background: white;
//     padding: 40px;
//     border-radius: 15px;
//     text-align: center;
//     box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
// `;

// document.body.appendChild(winnerOverlay);
// winnerOverlay.appendChild(winnerModal);

// function showWinnerModal(winnerId) {
//   winnerModal.innerHTML = `
//         <h1>🏆 Player ${winnerId} Wins! 🏆</h1>
//         <p>Congratulations on completing the race!</p>
//         <button onclick="restartGame()">Play Again</button>
//     `;
//   winnerOverlay.style.display = "flex";
// }

const cars = [
  {
    x: centerX - 8,
    y: centerY - 280,
    width: 60,
    height: 30,
    angle: 0,
    speed: 0,
    maxSpeed: 5,
    color: "#e74c3c",
  },
  {
    x: centerX - 8,
    y: centerY - 340,
    width: 60,
    height: 30,
    angle: 0,
    speed: 0,
    maxSpeed: 5,
    color: "#3498db",
  },
];

const controls = {
  player1: {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
  },
  player2: {
    w: false,
    s: false,
    a: false,
    d: false,
  },
};

let localPlayerId = null;

// WebSocket connection
let socket = new WebSocket("ws://127.0.0.1:8000/ws/game/");

socket.onopen = function () {
  console.log("Connected to WebSocket server");
};

socket.onmessage = function (e) {
  try {
    const data = JSON.parse(e.data);
    console.log("Received:", data);

    if (data.type === "player_joined") {
      localPlayerId = data.player_id;
      console.log("You are player", localPlayerId);
    } else if (data.type === "game_event") {
      // Fully update cars based on server data
      if (data.player1) {
        cars[0].x = data.player1.x;
        cars[0].y = data.player1.y;
        cars[0].angle = data.player1.angle;
        cars[0].speed = data.player1.speed;
      }
      if (data.player2) {
        cars[1].x = data.player2.x;
        cars[1].y = data.player2.y;
        cars[1].angle = data.player2.angle;
        cars[1].speed = data.player2.speed;
      }

      // if (data.game_finished && data.winner) {
      //   showWinnerModal(data.winner);
      // }

      if (checkTrackCollision(cars[0]) || checkTrackCollision(cars[1])) {
        console.log("Track boundary detected by server");
      }

      if (checkCarCollision(cars[0], cars[1])) {
        console.log("Car collision detected by server");
      }
    }
  } catch (error) {
    console.error("Error parsing message:", error);
  }
};

socket.onclose = function (e) {
  console.error("WebSocket closed unexpectedly");
};

// Input event listeners
window.addEventListener("keydown", (e) => {
  if (e.key in controls.player1) controls.player1[e.key] = true;
  if (e.key in controls.player2) controls.player2[e.key] = true;

  socket.send(
    JSON.stringify({
      type: "player_input",
      player1: controls.player1,
      player2: controls.player2,
    })
  );
});

window.addEventListener("keyup", (e) => {
  if (e.key in controls.player1) controls.player1[e.key] = false;
  if (e.key in controls.player2) controls.player2[e.key] = false;

  socket.send(
    JSON.stringify({
      type: "player_input",
      player1: controls.player1,
      player2: controls.player2,
    })
  );
});

// Collision Detection partttt
function checkTrackCollision(car) {
  const dx = car.x - centerX;
  const dy = car.y - centerY;
  const distanceFromCenter = Math.sqrt(dx * dx + dy * dy);

  const carDiagonal =
    Math.sqrt((car.width / 2) ** 2 + (car.height / 2) ** 2) - 60;

  return (
    distanceFromCenter + carDiagonal > outerTrackRadius ||
    distanceFromCenter - carDiagonal < innerTrackRadius
  );
}

function checkCarCollision(car1, car2) {
  // Calculate distance between car centers
  const dx = car1.x - car2.x;
  const dy = car1.y - car2.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  // Collision threshold
  const collisionThreshold = (car1.width + car2.width) / 2 - 20;

  return distance < collisionThreshold;
}

// Game rendering and loop
function drawTrack() {
  // Outer track boundary
  ctx.beginPath();
  ctx.arc(centerX, centerY, outerTrackRadius, 0, Math.PI * 2);
  ctx.fillStyle = "#2c3e50";
  ctx.fill();

  // Inner track boundary
  ctx.beginPath();
  ctx.arc(centerX, centerY, innerTrackRadius, 0, Math.PI * 2);
  ctx.fillStyle = "#34495e";
  ctx.fill();

  // Road surface
  ctx.beginPath();
  ctx.arc(centerX, centerY, innerTrackRadius, 0, Math.PI * 2);
  ctx.arc(centerX, centerY, outerTrackRadius, Math.PI * 2, 0, true);
  ctx.fillStyle = "#7f8c8d";
  ctx.fill();

  // Track lines
  ctx.strokeStyle = "#ecf0f1";
  ctx.lineWidth = 2;
  ctx.setLineDash([10, 10]);

  ctx.beginPath();
  ctx.arc(centerX, centerY, outerTrackRadius - 5, 0, Math.PI * 2);
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(centerX, centerY, innerTrackRadius + 5, 0, Math.PI * 2);
  ctx.stroke();

  ctx.setLineDash([]);
}

function drawCar(car, carImage) {
  ctx.save();
  ctx.translate(car.x, car.y);
  ctx.rotate(car.angle);
  ctx.drawImage(
    carImage,
    -car.width / 2,
    -car.height / 2,
    car.width,
    car.height
  );
  ctx.restore();
}

function drawFinishLine() {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(centerX, centerY - 250);
  ctx.lineTo(centerX, centerY - 390);
  ctx.strokeStyle = "orange";
  ctx.lineWidth = 10;
  ctx.stroke();
  ctx.restore();
}

function gameLoop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawTrack();
  drawFinishLine();
  drawCar(cars[0], carImages.player1);
  drawCar(cars[1], carImages.player2);

  if (checkTrackCollision(cars[0]) || checkTrackCollision(cars[1])) {
    console.log("Track collision detected!");
  }

  if (checkCarCollision(cars[0], cars[1])) {
    console.log("Car collision detected!");
  }

  requestAnimationFrame(gameLoop);
}

// Wait for images to load before starting game loop, yes this is a hack haha
let imagesLoaded = 0;
carImages.player1.onload = carImages.player2.onload = () => {
  imagesLoaded++;
  if (imagesLoaded === 2) {
    gameLoop();
  }
};
