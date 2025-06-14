"""
Command-line interface for kiosk-show-replacement.

This module provides the main CLI commands for the application including
database management, server startup, and other administrative tasks.
"""

import click
from flask.cli import with_appcontext


@click.group()
def cli():
    """Kiosk Show Replacement CLI commands."""
    pass


@cli.command()
@with_appcontext
def init_db():
    """Initialize the database with all required tables."""
    from ..app import db
    from ..models import Slideshow, SlideItem  # Import models to ensure they're registered
    
    db.create_all()
    click.echo('Database initialized successfully.')


@cli.command()
@click.option('--sample-data', '-s', is_flag=True, help='Include sample slideshow data')
@with_appcontext
def setup_db(sample_data):
    """Set up the database with tables and optional sample data."""
    from ..app import db
    from ..models import Slideshow, SlideItem
    
    # Create tables
    db.create_all()
    click.echo('✅ Database tables created.')
    
    if sample_data:
        # Check if sample data already exists
        existing = Slideshow.query.filter_by(name="Welcome Demo").first()
        if existing:
            click.echo('⚠️  Sample data already exists.')
            return
        
        # Create sample slideshow
        welcome_slideshow = Slideshow(
            name="Welcome Demo",
            description="A demonstration slideshow showcasing the system"
        )
        db.session.add(welcome_slideshow)
        db.session.flush()
        
        # Add sample slide
        sample_slide = SlideItem(
            slideshow_id=welcome_slideshow.id,
            title='Welcome to Kiosk Show Replacement',
            content_type='text',
            content_text='''<div style="text-align: center; font-family: Arial, sans-serif;">
<h1 style="color: #007bff;">Welcome!</h1>
<p style="font-size: 1.5em;">Kiosk Show Replacement is running successfully.</p>
<p>Create your own slideshows in the management interface.</p>
</div>''',
            display_duration=10,
            order_index=0
        )
        db.session.add(sample_slide)
        db.session.commit()
        
        click.echo('✅ Sample data created.')
    
    click.echo('🎉 Database setup completed!')


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to.')
@click.option('--port', default=5000, help='Port to bind to.')
@click.option('--debug', is_flag=True, help='Enable debug mode.')
def serve(host, port, debug):
    """Start the development server."""
    from ..app import create_app
    
    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
@click.argument('name')
@click.option('--description', help='Description of the slideshow.')
def create_slideshow(name, description):
    """Create a new slideshow."""
    from ..app import db
    from ..models import Slideshow
    
    slideshow = Slideshow(
        name=name,
        description=description or f"Slideshow: {name}"
    )
    
    db.session.add(slideshow)
    db.session.commit()
    
    click.echo(f'Created slideshow "{name}" with ID {slideshow.id}')


def main():
    """Entry point for the CLI when called directly."""
    cli()


if __name__ == '__main__':
    main()