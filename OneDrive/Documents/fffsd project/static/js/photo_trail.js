/**
 * AuraHealth AI - Cursor-Reactive Photography Trail
 * Editorial experience spawning organically masked wellness imagery along cursor path.
 */

(function () {
    // Respect user accessibility preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    // Disable on primary touch devices
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) return;

    // Curated high-resolution Unsplash health, medical science & Indian food imagery
    const trailImages = [
        'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=300&q=80', // Fresh wholesome greens
        'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=300&q=80', // Indian Dosa & Chutney
        'https://images.unsplash.com/photo-1505576399279-565b52d4ac71?auto=format&fit=crop&w=300&q=80', // Preventive medical wellness
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=300&q=80', // Colorful healthy bowl
        'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=300&q=80', // Vibrant salads
        'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=300&q=80'  // Medical science laboratory
    ];

    let lastX = 0;
    let lastY = 0;
    let imageIndex = 0;
    const minDistance = 75; // Minimum px distance required before spawning next node
    let activeNodes = 0;
    const maxActiveNodes = 8; // Prevent DOM congestion

    // Container for trail nodes
    let trailContainer = document.querySelector('.photo-trail-container');
    if (!trailContainer) {
        trailContainer = document.createElement('div');
        trailContainer.className = 'photo-trail-container';
        document.body.appendChild(trailContainer);
    }

    // Attach to editorial zones
    const triggerZones = document.querySelectorAll('.photo-trail-zone, .hero-wrapper');
    if (triggerZones.length === 0) return;

    function spawnPhotoNode(x, y) {
        if (activeNodes >= maxActiveNodes) return;

        const imgUrl = trailImages[imageIndex];
        imageIndex = (imageIndex + 1) % trailImages.length;

        const node = document.createElement('div');
        node.className = 'photo-trail-node';
        node.style.backgroundImage = `url("${imgUrl}")`;
        node.style.left = `${x}px`;
        node.style.top = `${y}px`;

        // Slight organic tilt
        const randomRotation = (Math.random() - 0.5) * 24;
        node.style.transform = `translate(-50%, -50%) scale(0.6) rotate(${randomRotation}deg)`;

        trailContainer.appendChild(node);
        activeNodes++;

        // Trigger entrance animation
        requestAnimationFrame(() => {
            node.style.opacity = '0.9';
            node.style.transform = `translate(-50%, -50%) scale(1.0) rotate(${randomRotation}deg)`;
        });

        // Trigger decay and cleanup
        setTimeout(() => {
            node.style.opacity = '0';
            node.style.transform = `translate(-50%, -50%) scale(0.7) translateY(15px) rotate(${randomRotation}deg)`;
            setTimeout(() => {
                if (node.parentNode) {
                    node.parentNode.removeChild(node);
                    activeNodes--;
                }
            }, 500);
        }, 900);
    }

    triggerZones.forEach((zone) => {
        zone.addEventListener('mousemove', (e) => {
            const currentX = e.clientX;
            const currentY = e.clientY;

            const dist = Math.hypot(currentX - lastX, currentY - lastY);
            if (dist > minDistance) {
                lastX = currentX;
                lastY = currentY;
                spawnPhotoNode(currentX, currentY);
            }
        });
    });
})();
