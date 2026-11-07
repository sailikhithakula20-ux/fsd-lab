"""
Test Suite for Phase 4:
Landing Page Structure, WebGL 3D Canvas, Static Assets, and Storytelling Components.
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


@pytest.fixture
def client():
    """Create a configured Flask test client."""
    test_app = create_app('testing')
    return test_app.test_client()


def test_landing_page_renders_successfully(client):
    """Verify landing page endpoint returns 200 and required signature components."""
    response = client.get('/')
    assert response.status_code == 200

    html = response.data.decode('utf-8')

    # 1. Headline verification
    assert "Your Health." in html
    assert "Your Future." in html

    # 2. WebGL 3D DNA Canvas element verification
    assert 'id="hero-webgl-canvas"' in html

    # 3. Horizontal Services Rail verification
    assert 'class="services-rail-track"' in html
    assert "Smart Food &amp; Nutrition Tracking" in html or "Smart Food & Nutrition Tracking" in html
    assert "Real-Time Deficit-Filling Engine" in html

    # 4. Academic research paper citation verification
    assert "FR-RANC" in html
    assert "IEEE Access" in html

    # 5. External and internal animation scripts verification
    assert "three.min.js" in html
    assert "ScrollTrigger.min.js" in html
    assert "hero_animation.js" in html
    assert "photo_trail.js" in html
    assert "landing_scroll.js" in html


def test_static_assets_served(client):
    """Verify all static stylesheets and scripts are served with status 200."""
    assets = [
        '/static/css/theme.css',
        '/static/js/hero_animation.js',
        '/static/js/photo_trail.js',
        '/static/js/landing_scroll.js'
    ]

    for asset_path in assets:
        resp = client.get(asset_path)
        assert resp.status_code == 200, f"Static asset {asset_path} failed with status {resp.status_code}"


if __name__ == '__main__':
    pytest.main(['-v', __file__])
