import os
from app import create_app
from app.models.base import db

app = create_app()

@app.cli.command("seed-db")
def seed_db_command():
    """Seed database with sample operational data."""
    from seed import seed_database
    seed_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    env_mode = (os.environ.get('FLASK_ENV') or os.environ.get('ENV') or '').lower()
    is_prod = env_mode == 'production' or os.environ.get('PRODUCTION', '').lower() in ('true', '1')
    debug_mode = (not is_prod) and (os.environ.get('FLASK_DEBUG', '1') == '1')
    host = '0.0.0.0' if is_prod else '127.0.0.1'

    print(f"\n[*] Police Station Management System (PSMS) starting on http://{host}:{port} (debug={debug_mode})\n")
    app.run(debug=debug_mode, host=host, port=port)
