"""
Command-line interface for kiosk-show-replacement.

This module provides the main CLI commands for the application including
database management, server startup, and other administrative tasks.
"""

import click
from flask.cli import with_appcontext

from .init_db import main as init_db_command


@click.group()
def cli():
    """Kiosk Show Replacement CLI commands."""
    pass


# Add the init_db command to the CLI group
cli.add_command(init_db_command, name="init-db")


@cli.command()
@with_appcontext
def create_tables():
    """Create database tables without sample data (deprecated - use init-db)."""
    from ..app import db
    from ..models import (  # Import models to ensure they're registered
        SlideItem,
        Slideshow,
    )

    click.echo("⚠️  This command is deprecated. Use 'init-db' instead.")
    db.create_all()
    click.echo("Database tables created successfully.")


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", default=5000, help="Port to bind to.")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
def serve(host, port, debug):
    """Start the development server."""
    from ..app import create_app

    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
@click.argument("name")
@click.option("--description", help="Description of the slideshow.")
@with_appcontext
def create_slideshow(name, description):
    """Create a new slideshow."""
    from ..app import db
    from ..models import Slideshow

    slideshow = Slideshow(name=name, description=description or f"Slideshow: {name}")

    db.session.add(slideshow)
    db.session.commit()

    click.echo(f'Created slideshow "{name}" with ID {slideshow.id}')


def main():
    """Entry point for the CLI when called directly."""
    cli()


if __name__ == "__main__":
    main()
