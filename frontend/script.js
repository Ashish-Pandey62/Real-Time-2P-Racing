const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

canvas.width = 800;
canvas.height = 800;

const centerX = canvas.width / 2;
const centerY = canvas.height / 2;

// More complex, realistic track points
const trackPoints = [
  { x: centerX - 200, y: centerY - 300 }, // Top left
  { x: centerX + 250, y: centerY - 250 }, // Top right with curve
  { x: centerX + 350, y: centerY }, // Right long stretch
  { x: centerX + 200, y: centerY + 250 }, // Bottom right curve
  { x: centerX - 150, y: centerY + 300 }, // Bottom left
  { x: centerX - 350, y: centerY + 100 }, // Left long stretch
];

const trackWidth = 100;
const outerTrackRadius = 400;
const innerTrackRadius = 300;

// Car properties
const car = {
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
};

// Controls
const controls = {
  ArrowUp: false,
  ArrowDown: false,
  ArrowLeft: false,
  ArrowRight: false,
};

// Event listeners
window.addEventListener("keydown", (e) => {
  if (e.key in controls) controls[e.key] = true;
});
window.addEventListener("keyup", (e) => {
  if (e.key in controls) controls[e.key] = false;
});

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

function drawCar() {
  ctx.save();
  ctx.translate(car.x, car.y);
  ctx.rotate(car.angle);
  ctx.fillStyle = "#e74c3c";
  ctx.fillRect(-car.width / 2, -car.height / 2, car.width, car.height);
  ctx.restore();
}

function updateCarControls() {
  if (controls.ArrowUp) {
    car.speed = Math.min(car.speed + car.acceleration, car.maxSpeed);
  }
  if (controls.ArrowDown) {
    car.speed = Math.max(car.speed - car.deceleration, -car.maxSpeed / 2);
  }
  if (controls.ArrowLeft) {
    car.angle -= car.turnSpeed * (car.speed !== 0 ? 1 : 0);
  }
  if (controls.ArrowRight) {
    car.angle += car.turnSpeed * (car.speed !== 0 ? 1 : 0);
  }

  // Update position
  car.x += Math.cos(car.angle) * car.speed;
  car.y += Math.sin(car.angle) * car.speed;

  // Gradual speed reduction
  car.speed *= 0.98;
}

function constrainCarToTrack() {
  const dx = car.x - centerX;
  const dy = car.y - centerY;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance > outerTrackRadius - car.width / 2) {
    // Outer boundary collision
    const correction = (outerTrackRadius - car.width / 2) / distance;
    car.x = centerX + dx * correction;
    car.y = centerY + dy * correction;
    car.speed *= 0.5;
  }

  if (distance < innerTrackRadius + car.width / 2) {
    // Inner boundary collision
    const correction = (innerTrackRadius + car.width / 2) / distance;
    car.x = centerX + dx * correction;
    car.y = centerY + dy * correction;
    car.speed *= 0.5;
  }
}

const finishLineX = 300;
const finishLineY = 10;
const finishLineWidth = 20;
const finishLineHeight = 100;

function gameLoop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawTrack();

  ctx.fillStyle = "orange"; // Color of the finishing line
  ctx.fillRect(finishLineX, finishLineY, finishLineWidth, finishLineHeight);

  updateCarControls();
  constrainCarToTrack();
  drawCar();

  requestAnimationFrame(gameLoop);
}

gameLoop();
