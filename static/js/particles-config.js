function initParticles() {
    particlesJS("particles-js", {
        "particles": {
            "number": {
                "value": 100,
                "density": {
                    "enable": true,
                    "value_area": 800
                }
            },
            "color": {
                "value": "#6366f1"
            },
            "shape": {
                "type": "circle"
            },
            "opacity": {
                "value": 0.7,
                "random": false
            },
            "size": {
                "value": 4,
                "random": true
            },
            "line_linked": {
                "enable": true,
                "distance": 150,
                "color": "#6366f1",
                "opacity": 0.6,
                "width": 1.5
            },
            "move": {
                "enable": true,
                "speed": 2,
                "direction": "none",
                "random": false,
                "straight": false,
                "out_mode": "out",
                "bounce": false
            }
        },
        "interactivity": {
            "detect_on": "canvas",
            "events": {
                "onhover": {
                    "enable": true,
                    "mode": "grab"
                },
                "onclick": {
                    "enable": true,
                    "mode": "push"
                },
                "resize": true
            },
            "modes": {
                "grab": {
                    "distance": 200,
                    "line_linked": {
                        "opacity": 0.8
                    }
                }
            }
        },
        "retina_detect": true
    });
}