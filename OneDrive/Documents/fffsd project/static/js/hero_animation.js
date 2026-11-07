/**
 * AuraHealth AI - Signature 3D DNA Helix & Fluid Ink in Water Simulation
 * Technology: Three.js WebGL + Parametric Geometry + Procedural Curl Physics
 * Concept: "A Medical Clinic Told Through Ink in Water"
 */

(function () {
    const container = document.getElementById('hero-webgl-canvas');
    if (!container || typeof THREE === 'undefined') return;

    // --- Performance & Visibility Setup ---
    let isVisible = true;
    let animationFrameId = null;

    // --- Three.js Scene Setup ---
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 0, 48);

    const renderer = new THREE.WebGLRenderer({
        canvas: container,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance'
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));

    // --- Lighting ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x104C35, 1.8);
    dirLight1.position.set(20, 30, 20);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x8A9A5B, 1.2);
    dirLight2.position.set(-20, -20, 15);
    scene.add(dirLight2);

    // --- Group for DNA Double Helix ---
    const dnaGroup = new THREE.Group();
    // Offset slightly to the right to frame hero headline cleanly
    dnaGroup.position.set(10, 0, 0);
    scene.add(dnaGroup);

    // --- Parametric DNA Helix Construction ---
    const helixRadius = 5.2;
    const helixHeight = 44;
    const turns = 3.2;
    const strandSteps = 240;
    const basePairInterval = 5;

    const strand1Points = [];
    const strand2Points = [];

    const sphereGeom = new THREE.SphereGeometry(0.24, 12, 12);
    const strand1Mat = new THREE.MeshStandardMaterial({
        color: 0x104C35,
        roughness: 0.35,
        metalness: 0.2
    });
    const strand2Mat = new THREE.MeshStandardMaterial({
        color: 0x6A8E7F,
        roughness: 0.4,
        metalness: 0.15
    });
    const rungMat = new THREE.MeshStandardMaterial({
        color: 0xD5E1DC,
        roughness: 0.5,
        transparent: true,
        opacity: 0.8
    });

    for (let i = 0; i <= strandSteps; i++) {
        const t = (i / strandSteps) * Math.PI * 2 * turns;
        const y = ((i / strandSteps) - 0.5) * helixHeight;
        
        const x1 = Math.cos(t) * helixRadius;
        const z1 = Math.sin(t) * helixRadius;
        const p1 = new THREE.Vector3(x1, y, z1);
        strand1Points.push(p1);

        const x2 = Math.cos(t + Math.PI) * helixRadius;
        const z2 = Math.sin(t + Math.PI) * helixRadius;
        const p2 = new THREE.Vector3(x2, y, z2);
        strand2Points.push(p2);

        // Add node spheres along backbone
        if (i % 2 === 0) {
            const node1 = new THREE.Mesh(sphereGeom, strand1Mat);
            node1.position.copy(p1);
            dnaGroup.add(node1);

            const node2 = new THREE.Mesh(sphereGeom, strand2Mat);
            node2.position.copy(p2);
            dnaGroup.add(node2);
        }

        // Add connecting nucleotide base-pair rungs
        if (i % basePairInterval === 0) {
            const rungCurve = new THREE.LineCurve3(p1, p2);
            const rungGeom = new THREE.TubeGeometry(rungCurve, 1, 0.08, 6, false);
            const rungMesh = new THREE.Mesh(rungGeom, rungMat);
            dnaGroup.add(rungMesh);
        }
    }

    // Smooth spline tubes for DNA backbone ribbons
    const curve1 = new THREE.CatmullRomCurve3(strand1Points);
    const curve2 = new THREE.CatmullRomCurve3(strand2Points);
    const tube1 = new THREE.Mesh(new THREE.TubeGeometry(curve1, 160, 0.16, 8, false), strand1Mat);
    const tube2 = new THREE.Mesh(new THREE.TubeGeometry(curve2, 160, 0.16, 8, false), strand2Mat);
    dnaGroup.add(tube1);
    dnaGroup.add(tube2);

    // --- Procedural Ink-in-Water Particle System ---
    const particleCount = 14000;
    const particleGeom = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    // Particle state tracking
    const particleData = [];
    const colorEmerald = new THREE.Color(0x104C35);
    const colorSage = new THREE.Color(0x6A8E7F);
    const colorMist = new THREE.Color(0xD5E1DC);

    for (let i = 0; i < particleCount; i++) {
        // Pick an emitter point on the helix
        const strandChoice = Math.random() > 0.5 ? strand1Points : strand2Points;
        const anchorPoint = strandChoice[Math.floor(Math.random() * strandChoice.length)];

        const x = anchorPoint.x + (Math.random() - 0.5) * 1.5;
        const y = anchorPoint.y + (Math.random() - 0.5) * 1.5;
        const z = anchorPoint.z + (Math.random() - 0.5) * 1.5;

        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;

        colors[i * 3] = colorEmerald.r;
        colors[i * 3 + 1] = colorEmerald.g;
        colors[i * 3 + 2] = colorEmerald.b;

        sizes[i] = Math.random() * 2.4 + 1.0;

        particleData.push({
            anchorX: anchorPoint.x,
            anchorY: anchorPoint.y,
            anchorZ: anchorPoint.z,
            vx: (Math.random() - 0.5) * 0.04,
            vy: (Math.random() - 0.5) * 0.04 + 0.015,
            vz: (Math.random() - 0.5) * 0.04,
            life: Math.random() * 100,
            maxLife: 100 + Math.random() * 120
        });
    }

    particleGeom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    particleGeom.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // Custom Canvas Particle Texture (Soft Radial Gradient Ink Droplet)
    function createInkParticleTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 64;
        canvas.height = 64;
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
        gradient.addColorStop(0.35, 'rgba(235, 245, 240, 0.85)');
        gradient.addColorStop(0.7, 'rgba(106, 142, 127, 0.35)');
        gradient.addColorStop(1, 'rgba(11, 41, 27, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 64, 64);
        return new THREE.CanvasTexture(canvas);
    }

    const particleMaterial = new THREE.PointsMaterial({
        size: 1.6,
        vertexColors: true,
        map: createInkParticleTexture(),
        transparent: true,
        opacity: 0.75,
        blending: THREE.NormalBlending,
        depthWrite: false
    });

    const particleSystem = new THREE.Points(particleGeom, particleMaterial);
    dnaGroup.add(particleSystem);

    // --- Interactive Cursor Repulsion Physics ---
    const mouse3D = new THREE.Vector3(9999, 9999, 0);
    const mouseNormalized = { x: 0, y: 0 };
    const raycaster = new THREE.Raycaster();
    const interactionPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);

    window.addEventListener('mousemove', (event) => {
        const rect = container.getBoundingClientRect();
        mouseNormalized.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouseNormalized.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouseNormalized, camera);
        raycaster.ray.intersectPlane(interactionPlane, mouse3D);
    });

    // Touch device fallback: gracefully reset mouse repulsion
    window.addEventListener('mouseleave', () => {
        mouse3D.set(9999, 9999, 0);
    });

    // --- Pseudo-Perlin / Curl Noise Approximation for Viscous Ink Flow ---
    function curlNoise(x, y, z, time) {
        const s = 0.08;
        const t = time * 0.4;
        const nx = Math.sin(y * s + t) * Math.cos(z * s * 0.8);
        const ny = Math.cos(x * s + t) * Math.sin(z * s * 0.6);
        const nz = Math.sin((x + y) * s * 0.5 + t);
        return { x: nx * 0.06, y: ny * 0.06, z: nz * 0.06 };
    }

    // --- Animation Loop ---
    let clock = new THREE.Clock();

    function animate() {
        if (!isVisible) return;
        animationFrameId = requestAnimationFrame(animate);

        const delta = clock.getDelta();
        const time = clock.getElapsedTime();

        // 1. Rotate DNA Double Helix gently
        dnaGroup.rotation.y = time * 0.22;
        dnaGroup.rotation.z = Math.sin(time * 0.15) * 0.06;

        // 2. Update Fluid Ink Particle Dynamics
        const posAttr = particleGeom.attributes.position;
        const colorAttr = particleGeom.attributes.color;

        // Transform mouse to dnaGroup local coordinates for collision repulsion
        const localMouse = mouse3D.clone();
        dnaGroup.worldToLocal(localMouse);

        const repulsionRadius = 7.5;
        const repulsionStrength = 0.55;

        for (let i = 0; i < particleCount; i++) {
            const data = particleData[i];
            data.life += delta * 24;

            let px = posAttr.getX(i);
            let py = posAttr.getY(i);
            let pz = posAttr.getZ(i);

            // Curl noise drift (ink dissolving in water)
            const noise = curlNoise(px, py, pz, time);
            px += noise.x + data.vx;
            py += noise.y + data.vy;
            pz += noise.z + data.vz;

            // Cursor Repulsion Physics: Part particles outward from cursor path
            const dx = px - localMouse.x;
            const dy = py - localMouse.y;
            const dz = pz - localMouse.z;
            const distSq = dx * dx + dy * dy + dz * dz;

            if (distSq < repulsionRadius * repulsionRadius) {
                const dist = Math.sqrt(distSq) + 0.001;
                const force = (1.0 - dist / repulsionRadius) * repulsionStrength;
                px += (dx / dist) * force;
                py += (dy / dist) * force;
                pz += (dz / dist) * force * 0.5;
            }

            // Life cycle & rebirth from helix backbone
            if (data.life >= data.maxLife) {
                const strandChoice = Math.random() > 0.5 ? strand1Points : strand2Points;
                const anchor = strandChoice[Math.floor(Math.random() * strandChoice.length)];
                px = anchor.x + (Math.random() - 0.5) * 0.8;
                py = anchor.y + (Math.random() - 0.5) * 0.8;
                pz = anchor.z + (Math.random() - 0.5) * 0.8;
                data.life = 0;
            }

            posAttr.setXYZ(i, px, py, pz);

            // Color transition from emerald to misty sage
            const lifeProgress = data.life / data.maxLife;
            const targetColor = lifeProgress < 0.5 ? colorEmerald.clone().lerp(colorSage, lifeProgress * 2)
                                                  : colorSage.clone().lerp(colorMist, (lifeProgress - 0.5) * 2);
            colorAttr.setXYZ(i, targetColor.r, targetColor.g, targetColor.b);
        }

        posAttr.needsUpdate = true;
        colorAttr.needsUpdate = true;

        renderer.render(scene, camera);
    }

    // --- Viewport Resize Handler ---
    function onWindowResize() {
        const width = container.clientWidth;
        const height = container.clientHeight;
        if (width === 0 || height === 0) return;

        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));

        // Adjust DNA position based on screen width
        if (width < 768) {
            dnaGroup.position.set(0, 0, -10); // Center on mobile
            dnaGroup.scale.set(0.75, 0.75, 0.75);
        } else if (width < 1200) {
            dnaGroup.position.set(6, 0, -4);
            dnaGroup.scale.set(0.9, 0.9, 0.9);
        } else {
            dnaGroup.position.set(10, 0, 0);
            dnaGroup.scale.set(1, 1, 1);
        }
    }
    window.addEventListener('resize', onWindowResize);
    onWindowResize();

    // --- Intersection Observer (Pause rendering when out of viewport) ---
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            isVisible = entry.isIntersecting;
            if (isVisible && !animationFrameId) {
                animate();
            } else if (!isVisible && animationFrameId) {
                cancelAnimationFrame(animationFrameId);
                animationFrameId = null;
            }
        });
    }, { threshold: 0.05 });

    observer.observe(container);

    // Initial trigger
    animate();
})();
