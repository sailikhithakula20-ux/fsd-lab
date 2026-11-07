/**
 * AuraHealth AI - GSAP ScrollTrigger & Storytelling Controller
 * Drives horizontal pinned services rail and vertical overlapping reveals.
 */

(function () {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

    gsap.registerPlugin(ScrollTrigger);

    // --- Horizontal Services Rail ---
    const railViewport = document.querySelector('.services-rail-viewport');
    const railTrack = document.querySelector('.services-rail-track');

    if (railViewport && railTrack) {
        // Desktop / Large screen horizontal pin
        const isDesktop = window.innerWidth >= 992;

        if (isDesktop) {
            const calculateDistance = () => -(railTrack.scrollWidth - window.innerWidth + 120);

            gsap.to(railTrack, {
                x: calculateDistance,
                ease: "none",
                scrollTrigger: {
                    trigger: railViewport,
                    pin: true,
                    scrub: 1.2,
                    start: "top top",
                    end: () => `+=${railTrack.scrollWidth - window.innerWidth + 400}`,
                    invalidateOnRefresh: true,
                    anticipatePin: 1
                }
            });
        } else {
            // Mobile & Tablet: Allow natural horizontal touch-swiping
            railTrack.style.overflowX = 'auto';
            railTrack.style.width = '100%';
            railTrack.style.padding = '0 1rem 1.5rem';
        }
    }

    // --- Section Reveal Animations ---
    const revealCards = document.querySelectorAll('.showcase-card, .story-section');
    revealCards.forEach((card) => {
        gsap.fromTo(card, 
            { opacity: 0.85, y: 30 },
            {
                opacity: 1,
                y: 0,
                duration: 0.8,
                ease: "power2.out",
                scrollTrigger: {
                    trigger: card,
                    start: "top 88%",
                    toggleActions: "play none none none"
                }
            }
        );
    });
})();
