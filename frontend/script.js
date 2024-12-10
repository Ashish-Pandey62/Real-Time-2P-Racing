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
const innerTrackRadius = 300;

// Car properties for two players
const cars = [
  {
    x: trackPoints[0].x,
    y: trackPoints[0].y,
    width: 40,
    height: 20,
    angle: 0,
    speed: 0,
    maxSpeed: 5,
    acceleration: 0.1,
    deceleration: 0.05,
    turnSpeed: 0.05,
    color: "#e74c3c",
  },
  {
    x: trackPoints[1].x,
    y: trackPoints[1].y,
    width: 40,
    height: 20,
    angle: 0,
    speed: 0,
    maxSpeed: 5,
    acceleration: 0.1,
    deceleration: 0.05,
    turnSpeed: 0.05,
    color: "#3498db",
  },
];

// Player controls
const controls = {
  player1: {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
  },
  player2: { w: false, s: false, a: false, d: false },
};

// Handle keyboard input
window.addEventListener("keydown", (e) => {
  if (e.key in controls.player1) controls.player1[e.key] = true;
  if (e.key in controls.player2) controls.player2[e.key] = true;
});

window.addEventListener("keyup", (e) => {
  if (e.key in controls.player1) controls.player1[e.key] = false;
  if (e.key in controls.player2) controls.player2[e.key] = false;
});

// Draw the racetrack
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

// Update car movement based on player controls
function updateCarControls(car, carControls) {
  if (carControls.ArrowUp || carControls.w) {
    car.speed = Math.min(car.speed + car.acceleration, car.maxSpeed);
  }
  if (carControls.ArrowDown || carControls.s) {
    car.speed = Math.max(car.speed - car.deceleration, -car.maxSpeed / 2);
  }
  if (carControls.ArrowLeft || carControls.a) {
    car.angle -= car.turnSpeed * (car.speed !== 0 ? 1 : 0);
  }
  if (carControls.ArrowRight || carControls.d) {
    car.angle += car.turnSpeed * (car.speed !== 0 ? 1 : 0);
  }

  car.x += Math.cos(car.angle) * car.speed;
  car.y += Math.sin(car.angle) * car.speed;
  car.speed *= 0.98; // Gradual deceleration
}

// Prevent cars from going out of the track
function constrainCarToTrack(car) {
  const dx = car.x - centerX;
  const dy = car.y - centerY;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance > outerTrackRadius - car.width / 2) {
    const correction = (outerTrackRadius - car.width / 2) / distance;
    car.x = centerX + dx * correction;
    car.y = centerY + dy * correction;
    car.speed *= 0.5;
  }

  if (distance < innerTrackRadius + car.width / 2) {
    const correction = (innerTrackRadius + car.width / 2) / distance;
    car.x = centerX + dx * correction;
    car.y = centerY + dy * correction;
    car.speed *= 0.5;
  }
}

// Collision handling function
function handleCollision(car1, car2) {
  // Determine relative movement: car1 vs. car2
  const car1Momentum = Math.abs(car1.speed);
  const car2Momentum = Math.abs(car2.speed);

  if (car1Momentum > car2Momentum) {
    // Car1 is likely the hitter
    car1.speed *= 0.7; // Decrease car1's speed
    car2.speed += 2; // Boost car2's speed
    car2.speed = Math.min(car2.speed, car2.maxSpeed);
  } else {
    // Car2 is likely the hitter
    car2.speed *= 0.7; // Decrease car2's speed
    car1.speed += 2; // Boost car1's speed
    car1.speed = Math.min(car1.speed, car1.maxSpeed);
  }
}

// Check for collision between two cars
// Check for collision between two cars
function checkCollision(car1, car2) {
  if (
    car1.x < car2.x + car2.width &&
    car1.x + car1.width > car2.x &&
    car1.y < car2.y + car2.height &&
    car1.y + car1.height > car2.y
  ) {
    handleCollision(car1, car2);
    return true;
  }
  return false;
}

// Draw cars
function drawCar(car) {
  ctx.save();
  ctx.translate(car.x, car.y);
  ctx.rotate(car.angle);
  ctx.fillStyle = car.color;
  ctx.fillRect(-car.width / 2, -car.height / 2, car.width, car.height);
  ctx.restore();
}

// Draw finishing line
function drawFinishLine() {
  const finishLineX = centerX + 350; // X coordinate for the finishing line
  ctx.fillStyle = "orange";
  ctx.fillRect(finishLineX - 50, centerY, 100, 10);
}

// Main game loop
function gameLoop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawTrack();
  drawFinishLine();

  updateCarControls(cars[0], controls.player1);
  updateCarControls(cars[1], controls.player2);

  constrainCarToTrack(cars[0]);
  constrainCarToTrack(cars[1]);

  checkCollision(cars[0], cars[1]);

  drawCar(cars[0]);
  drawCar(cars[1]);

  requestAnimationFrame(gameLoop);
}

gameLoop();
