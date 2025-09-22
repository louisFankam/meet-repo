/**
 * Fireworks Animation Library
 * Crée des animations de feu d'artifice pour les likes et interactions
 */
class FireworksEngine {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.rockets = [];
        this.isActive = false;
        this.colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
            '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
            '#10ac84', '#ee5a24', '#0984e3', '#6c5ce7', '#a29bfe'
        ];
        this.init();
    }

    init() {
        // Créer le canvas si nécessaire
        if (!this.canvas) {
            this.canvas = document.createElement('canvas');
            this.canvas.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 9999;
            `;
            document.body.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');
            this.resizeCanvas();
            window.addEventListener('resize', () => this.resizeCanvas());
        }
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticle(x, y, color, velocity, size = 3) {
        return {
            x: x,
            y: y,
            vx: velocity.x,
            vy: velocity.y,
            color: color,
            size: size,
            life: 1.0,
            decay: Math.random() * 0.02 + 0.005,
            gravity: 0.1,
            trail: []
        };
    }

    createRocket(startX, startY, targetX, targetY, color) {
        const dx = targetX - startX;
        const dy = targetY - startY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const speed = 8;
        
        return {
            x: startX,
            y: startY,
            vx: (dx / distance) * speed,
            vy: (dy / distance) * speed,
            color: color,
            targetX: targetX,
            targetY: targetY,
            exploded: false,
            trail: []
        };
    }

    explode(x, y, color, intensity = 1) {
        const particleCount = Math.floor(30 * intensity);
        const angleStep = (Math.PI * 2) / particleCount;
        
        for (let i = 0; i < particleCount; i++) {
            const angle = angleStep * i + Math.random() * 0.5;
            const speed = Math.random() * 6 + 2;
            
            const velocity = {
                x: Math.cos(angle) * speed,
                y: Math.sin(angle) * speed
            };
            
            this.particles.push(this.createParticle(x, y, color, velocity));
        }

        // Créer des étincelles supplémentaires
        for (let i = 0; i < 10 * intensity; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 3 + 1;
            
            const velocity = {
                x: Math.cos(angle) * speed,
                y: Math.sin(angle) * speed
            };
            
            const sparkle = this.createParticle(x, y, '#ffffff', velocity, 1);
            sparkle.decay = 0.03;
            this.particles.push(sparkle);
        }
    }

    createHeartBurst(x, y, color) {
        // Créer une explosion en forme de cœur
        const heartPoints = this.getHeartPoints();
        
        heartPoints.forEach(point => {
            const speed = Math.random() * 4 + 2;
            const velocity = {
                x: point.x * speed,
                y: point.y * speed - 2
            };
            
            this.particles.push(this.createParticle(x, y, color, velocity, 4));
        });

        // Ajouter des particules aléatoires autour
        for (let i = 0; i < 20; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 5 + 1;
            
            const velocity = {
                x: Math.cos(angle) * speed,
                y: Math.sin(angle) * speed
            };
            
            this.particles.push(this.createParticle(x, y, color, velocity));
        }
    }

    getHeartPoints() {
        const points = [];
        const steps = 16;
        
        for (let i = 0; i < steps; i++) {
            const t = (i / steps) * Math.PI * 2;
            const x = 16 * Math.pow(Math.sin(t), 3);
            const y = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t));
            points.push({ x: x / 16, y: y / 16 });
        }
        
        return points;
    }

    launchFireworks(targetElement, type = 'normal') {
        if (!targetElement) return;

        const rect = targetElement.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        // Lancer plusieurs fusées
        const rocketCount = type === 'heart' ? 3 : 5;
        
        for (let i = 0; i < rocketCount; i++) {
            setTimeout(() => {
                const startX = Math.random() * this.canvas.width;
                const startY = this.canvas.height;
                const color = this.colors[Math.floor(Math.random() * this.colors.length)];
                
                const rocket = this.createRocket(startX, startY, centerX, centerY, color);
                this.rockets.push(rocket);
            }, i * 100);
        }

        this.start();
    }

    launchCelebration(x, y) {
        // Lancer une grande célébration
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#feca57', '#ff9ff3'];
        
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                const color = colors[i % colors.length];
                this.createHeartBurst(
                    x + (Math.random() - 0.5) * 100,
                    y + (Math.random() - 0.5) * 100,
                    color
                );
            }, i * 200);
        }
        
        this.start();
    }

    update() {
        // Mettre à jour les fusées
        this.rockets = this.rockets.filter(rocket => {
            rocket.x += rocket.vx;
            rocket.y += rocket.vy;

            // Ajouter à la traînée
            rocket.trail.push({ x: rocket.x, y: rocket.y });
            if (rocket.trail.length > 10) {
                rocket.trail.shift();
            }

            // Vérifier si la fusée a atteint sa cible
            const dx = rocket.targetX - rocket.x;
            const dy = rocket.targetY - rocket.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 20 || rocket.exploded) {
                rocket.exploded = true;
                this.createHeartBurst(rocket.x, rocket.y, rocket.color);
                return false;
            }

            return true;
        });

        // Mettre à jour les particules
        this.particles = this.particles.filter(particle => {
            // Mettre à jour la position
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += particle.gravity;

            // Ajouter à la traînée
            particle.trail.push({ x: particle.x, y: particle.y });
            if (particle.trail.length > 5) {
                particle.trail.shift();
            }

            // Réduire la vie
            particle.life -= particle.decay;

            return particle.life > 0;
        });

        // Arrêter l'animation s'il n'y a plus de particules
        if (this.particles.length === 0 && this.rockets.length === 0) {
            this.stop();
        }
    }

    draw() {
        // Effacer le canvas avec un effet de traînée
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Dessiner les fusées
        this.rockets.forEach(rocket => {
            // Dessiner la traînée
            rocket.trail.forEach((point, index) => {
                const alpha = index / rocket.trail.length;
                this.ctx.globalAlpha = alpha;
                this.ctx.fillStyle = rocket.color;
                this.ctx.beginPath();
                this.ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
                this.ctx.fill();
            });

            // Dessiner la fusée
            this.ctx.globalAlpha = 1;
            this.ctx.fillStyle = rocket.color;
            this.ctx.beginPath();
            this.ctx.arc(rocket.x, rocket.y, 3, 0, Math.PI * 2);
            this.ctx.fill();
        });

        // Dessiner les particules
        this.particles.forEach(particle => {
            const alpha = particle.life;
            
            // Dessiner la traînée
            particle.trail.forEach((point, index) => {
                const trailAlpha = (index / particle.trail.length) * alpha * 0.5;
                this.ctx.globalAlpha = trailAlpha;
                this.ctx.fillStyle = particle.color;
                this.ctx.beginPath();
                this.ctx.arc(point.x, point.y, particle.size * 0.5, 0, Math.PI * 2);
                this.ctx.fill();
            });

            // Dessiner la particule
            this.ctx.globalAlpha = alpha;
            this.ctx.fillStyle = particle.color;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fill();

            // Ajouter un effet de brillance
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = particle.color;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;
        });

        this.ctx.globalAlpha = 1;
    }

    animate() {
        if (!this.isActive) return;

        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }

    start() {
        if (!this.isActive) {
            this.isActive = true;
            this.animate();
        }
    }

    stop() {
        this.isActive = false;
        
        // Effacer le canvas après un délai
        setTimeout(() => {
            if (!this.isActive) {
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            }
        }, 1000);
    }

    destroy() {
        this.stop();
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// Fonction utilitaire pour lancer des feu d'artifice
window.LikeFireworks = {
    engine: null,

    init() {
        if (!this.engine) {
            this.engine = new FireworksEngine();
        }
    },

    launchLikeAnimation(element) {
        this.init();
        this.engine.launchFireworks(element, 'heart');
    },

    launchMatchAnimation(element) {
        this.init();
        this.engine.launchCelebration(
            element.getBoundingClientRect().left + element.getBoundingClientRect().width / 2,
            element.getBoundingClientRect().top + element.getBoundingClientRect().height / 2
        );
    },

    launchCelebration(x, y) {
        this.init();
        this.engine.launchCelebration(x, y);
    }
};

// Initialiser automatiquement
document.addEventListener('DOMContentLoaded', () => {
    window.LikeFireworks.init();
});