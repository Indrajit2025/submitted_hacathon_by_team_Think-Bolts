// Initialize AOS
AOS.init({
    duration: 800,
    easing: 'ease-out-cubic',
    once: true
});

// Initialize custom cursor
new kursor({
    type: 1,
    removeDefaultCursor: true,
    color: '#4f46e5'
});

// Initialize MicroModal
MicroModal.init({
    openTrigger: 'data-micromodal-trigger',
    disableScroll: true,
    awaitOpenAnimation: true,
    awaitCloseAnimation: true
});

// Initialize SimpleBar
document.querySelectorAll('[data-simplebar]').forEach(element => {
    new SimpleBar(element);
});