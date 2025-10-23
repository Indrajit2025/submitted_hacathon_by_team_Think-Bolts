// Initialize AOS
AOS.init({
    duration: 1000,
    once: true,
});

// Animated Counters
const counters = document.querySelectorAll('[data-count]');
const speed = 200; // The lower the #, the faster the count

const animateCounters = () => {
    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute('data-count');
            const count = +counter.innerText.replace('+', '').replace('%', '');
            const inc = target / speed;

            if (count < target) {
                const newCount = Math.ceil(count + inc);
                if (counter.hasAttribute('data-count') && counter.getAttribute('data-count').includes('95')) {
                    counter.innerText = newCount + '%';
                } else {
                    counter.innerText = newCount + '+';
                }
                setTimeout(updateCount, 1);
            } else {
                if (counter.hasAttribute('data-count') && counter.getAttribute('data-count').includes('95')) {
                     counter.innerText = target + '%';
                } else {
                     counter.innerText = target + '+';
                }
            }
        };
        updateCount();
    });
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounters();
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const impactSection = document.getElementById('impact');
if(impactSection) {
    observer.observe(impactSection);
}

// Particles.js
particlesJS('particles-js', {
    "particles": {
        "number": {
            "value": 80,
            "density": {
                "enable": true,
                "value_area": 800
            }
        },
        "color": {
            "value": "#ffffff"
        },
        "shape": {
            "type": "circle",
        },
        "opacity": {
            "value": 0.5,
            "random": false,
        },
        "size": {
            "value": 3,
            "random": true,
        },
        "line_linked": {
            "enable": true,
            "distance": 150,
            "color": "#ffffff",
            "opacity": 0.4,
            "width": 1
        },
        "move": {
            "enable": true,
            "speed": 6,
            "direction": "none",
            "random": false,
            "straight": false,
            "out_mode": "out",
            "bounce": false,
        }
    },
    "interactivity": {
        "detect_on": "canvas",
        "events": {
            "onhover": {
                "enable": true,
                "mode": "repulse"
            },
            "onclick": {
                "enable": true,
                "mode": "push"
            },
            "resize": true
        },
        "modes": {
            "repulse": {
                "distance": 100,
                "duration": 0.4
            },
            "push": {
                "particles_nb": 4
            },
        }
    },
    "retina_detect": true
});

// Scrollspy
const navLinks = document.querySelectorAll('.navbar a');
const sections = document.querySelectorAll('section');

window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= sectionTop - 60) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(current)) {
            link.classList.add('active');
        }
    });
});

// Dropdown
const dropdown = document.querySelector('.dropdown');

dropdown.addEventListener('click', (e) => {
    e.preventDefault();
    dropdown.classList.toggle('open');
});