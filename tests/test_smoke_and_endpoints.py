import os
import re
import pytest
from app import create_app, db

@pytest.fixture(scope='module')
def test_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        yield app

@pytest.fixture
def client(test_app):
    return test_app.test_client()


def test_template_url_for_endpoints(test_app):
    """
    Scan all Jinja2 HTML templates and verify that every url_for('...') endpoint
    exists in app.view_functions or is the 'static' endpoint.
    """
    templates_dir = os.path.join(test_app.root_path, 'templates')
    endpoint_pattern = re.compile(r"url_for\(\s*['\"]([a-zA-Z0-9_\.]+)['\"]")

    found_endpoints = []
    missing_endpoints = []

    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, templates_dir)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = endpoint_pattern.findall(content)
                    for ep in matches:
                        found_endpoints.append((ep, rel_path))

    for ep, template_name in found_endpoints:
        if ep != 'static' and ep not in test_app.view_functions:
            missing_endpoints.append(f"Template '{template_name}' calls missing endpoint '{ep}'")

    assert len(missing_endpoints) == 0, f"Found missing url_for endpoints in templates:\n" + "\n".join(missing_endpoints)


def test_all_get_routes_smoke(test_app, client):
    """
    Logs in as admin, then requests EVERY GET route in app.url_map
    (replaces <int:id> / <id> with 1 from seed data, skips logout and delete routes)
    and asserts response status_code < 400.
    """
    # 1. Login as admin
    login_resp = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert login_resp.status_code == 200

    tested_routes = []
    failed_routes = []

    for rule in test_app.url_map.iter_rules():
        # Check if GET is supported
        if 'GET' not in rule.methods:
            continue

        # Skip static assets
        if rule.endpoint == 'static':
            continue

        # Skip logout and delete routes
        if 'logout' in rule.rule or 'delete' in rule.rule or 'delete' in rule.endpoint:
            continue

        # Build path replacing <int:id> or <id> with 1
        path = rule.rule
        if '<int:id>' in path:
            path = path.replace('<int:id>', '1')
        elif '<id>' in path:
            path = path.replace('<id>', '1')

        # Request route
        resp = client.get(path, follow_redirects=True)
        tested_routes.append(path)

        if resp.status_code >= 400:
            failed_routes.append((path, rule.endpoint, resp.status_code, resp.data[:300]))

    assert len(tested_routes) > 20, "Should test all registered GET routes"
    assert len(failed_routes) == 0, f"Routes failed with status >= 400:\n" + "\n".join(
        [f"Route {p} ({ep}) -> HTTP {st}: {err}" for p, ep, st, err in failed_routes]
    )


def test_secret_key_production_validation(monkeypatch):
    """
    Verify that in production mode, Config raises ValueError if SECRET_KEY is missing.
    """
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.delenv('SECRET_KEY', raising=False)

    from app.config import get_secret_key
    with pytest.raises(ValueError, match="SECRET_KEY environment variable is missing in production mode"):
        get_secret_key()
