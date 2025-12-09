
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
document.body.appendChild(canvas);

canvas.style.position = 'fixed';
canvas.style.top = '0';
canvas.style.left = '0';
canvas.style.width = '100%';
canvas.style.height = '100%';
canvas.style.pointerEvents = 'none';
canvas.style.zIndex = '1'; // Behind content but in front of BG

let width, height;
let particles = [];

// Configuration
const PARTICLE_COUNT = 150;
const SPEED_MIN = 1;
const SPEED_MAX = 3;
const SIZE_MIN = 0.5;
const SIZE_MAX = 2;

function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
}

class Particle {
    constructor() {
        this.reset();
        this.y = Math.random() * height; // Random start height
    }

    reset() {
        this.x = Math.random() * width;
        this.y = -10;
        this.speed = SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN);
        this.size = SIZE_MIN + Math.random() * (SIZE_MAX - SIZE_MIN);
        this.drift = (Math.random() - 0.5) * 0.5;
        this.opacity = 0.1 + Math.random() * 0.5;
    }

    update() {
        this.y += this.speed;
        this.x += this.drift;

        if (this.y > height) {
            this.reset();
        }
    }

    draw() {
        ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

function init() {
    resize();
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
    }
    animate();
}

function animate() {
    ctx.clearRect(0, 0, width, height);
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    requestAnimationFrame(animate);
}

window.addEventListener('resize', resize);
init();
