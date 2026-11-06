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


def test_health_check_endpoint(client):
    """Verify /health route returns 'OK' with HTTP 200 without requiring login."""
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.data.decode('utf-8').strip() == "OK"


def test_all_get_routes_smoke(test_app, client):
    """
    Log in as admin, then request EVERY GET route in app.url_map
    (replaces <int:id> / <id> with 1 from seed data, skips logout and delete routes)
    and assert response status_code < 400.
    """
    # 1. Login as admin
    login_resp = client.post(
        '/auth/login',
        data={'username': 'admin', 'password': 'admin123'},
        follow_redirects=True
    )
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

        # Build path replacing <int:id> or <id> with 1 from seed data
        path = rule.rule
        if '<int:id>' in path:
            path = path.replace('<int:id>', '1')
        elif '<id>' in path:
            path = path.replace('<id>', '1')

        # Request route
        resp = client.get(path, follow_redirects=True)
        tested_routes.append((path, rule.endpoint))

        if resp.status_code >= 400:
            failed_routes.append((path, rule.endpoint, resp.status_code, resp.data[:300]))

    assert len(tested_routes) > 25, "Should test all registered GET routes"
    assert len(failed_routes) == 0, f"Routes failed with status >= 400:\n" + "\n".join(
        [f"Route {p} ({ep}) -> HTTP {st}: {err}" for p, ep, st, err in failed_routes]
    )


def test_scan_templates_and_python_for_url_for_endpoints(test_app):
    """
    Scan all Jinja2 templates (.html) and Python source files (.py) across the project
    and verify that every url_for('...') endpoint exists in app.view_functions or is 'static'.
    """
    project_root = os.path.dirname(test_app.root_path)
    pattern = re.compile(r"url_for\(\s*['\"]([a-zA-Z0-9_\.]+)['\"]")

    found_endpoints = []
    missing_endpoints = []

    scan_targets = [
        os.path.join(test_app.root_path, 'templates'),
        os.path.join(test_app.root_path, 'routes'),
        os.path.join(test_app.root_path, 'models'),
        os.path.join(test_app.root_path, 'utils'),
        os.path.join(project_root, 'run.py'),
        os.path.join(project_root, 'seed.py'),
    ]

    for target in scan_targets:
        if os.path.isfile(target):
            files_to_scan = [target]
        elif os.path.isdir(target):
            files_to_scan = [
                os.path.join(root, f)
                for root, _, files in os.walk(target)
                for f in files
                if f.endswith('.html') or f.endswith('.py')
            ]
        else:
            continue

        for file_path in files_to_scan:
            rel_name = os.path.relpath(file_path, project_root)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = pattern.findall(content)
                for ep in matches:
                    found_endpoints.append((ep, rel_name))

    for ep, source_file in found_endpoints:
        if ep != 'static' and ep not in test_app.view_functions:
            missing_endpoints.append(f"Source file '{source_file}' calls missing endpoint '{ep}'")

    assert len(missing_endpoints) == 0, f"Found missing url_for endpoints:\n" + "\n".join(missing_endpoints)
