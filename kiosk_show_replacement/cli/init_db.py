#!/usr/bin/env python3
"""
Database initialization script for kiosk-show-replacement.

This script initializes the database tables and optionally adds sample data
for testing and demonstration purposes.
"""

import os
import sys
import click
from pathlib import Path

from ..app import create_app, db
from ..models import Slideshow, SlideItem


def init_database(app, create_sample_data=False):
    """
    Initialize the database with all required tables.
    
    Args:
        app: Flask application instance
        create_sample_data: Whether to create sample data for testing
    """
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully.")
        
        if create_sample_data:
            create_sample_slideshow_data()
        
        print("🎉 Database initialization completed!")


def create_sample_slideshow_data():
    """Create sample slideshow data for testing and demonstration."""
    print("Creating sample data...")
    
    # Check if sample data already exists
    existing_slideshow = Slideshow.query.filter_by(name="Welcome Demo").first()
    if existing_slideshow:
        print("⚠️  Sample data already exists, skipping creation.")
        return
    
    # Create a welcome/demo slideshow
    welcome_slideshow = Slideshow(
        name="Welcome Demo",
        description="A demonstration slideshow showcasing different content types"
    )
    db.session.add(welcome_slideshow)
    db.session.flush()  # Get the ID
    
    # Add sample slides
    sample_slides = [
        {
            'title': 'Welcome to Kiosk Show Replacement',
            'content_type': 'text',
            'content_text': '''<div style="text-align: center; font-family: Arial, sans-serif;">
<h1 style="color: #007bff; font-size: 3em; margin-bottom: 0.5em;">Welcome!</h1>
<h2 style="color: #333; font-size: 2em; margin-bottom: 1em;">Kiosk Show Replacement</h2>
<p style="font-size: 1.5em; color: #666; line-height: 1.6;">
A self-hosted digital signage solution<br>
Built with Flask and modern web technologies
</p>
<p style="font-size: 1.2em; color: #888; margin-top: 2em;">
This is a sample slideshow to demonstrate the system
</p>
</div>''',
            'display_duration': 10,
            'order_index': 0
        },
        {
            'title': 'Features Overview',
            'content_type': 'text',
            'content_text': '''<div style="text-align: center; font-family: Arial, sans-serif; padding: 2em;">
<h2 style="color: #007bff; font-size: 2.5em; margin-bottom: 1em;">Key Features</h2>
<div style="font-size: 1.4em; color: #333; line-height: 2;">
<p>🖥️ Web-based Management Interface</p>
<p>📺 Full-screen Kiosk Display Mode</p>
<p>🎯 Multiple Content Types (Images, Web Pages, Text)</p>
<p>⏱️ Flexible Display Timing</p>
<p>🔄 Real-time Updates</p>
<p>📱 Responsive Design</p>
<p>🛠️ RESTful API</p>
</div>
</div>''',
            'display_duration': 15,
            'order_index': 1
        },
        {
            'title': 'Sample Web Content',
            'content_type': 'url',
            'content_url': 'https://example.com',
            'display_duration': 12,
            'order_index': 2
        },
        {
            'title': 'Getting Started',
            'content_type': 'text',
            'content_text': '''<div style="text-align: center; font-family: Arial, sans-serif; padding: 2em;">
<h2 style="color: #28a745; font-size: 2.5em; margin-bottom: 1em;">Getting Started</h2>
<div style="font-size: 1.3em; color: #333; line-height: 1.8;">
<p style="margin-bottom: 1em;">1. Access the management interface to create your own slideshows</p>
<p style="margin-bottom: 1em;">2. Add content: images, web pages, or custom text</p>
<p style="margin-bottom: 1em;">3. Configure display timing for each slide</p>
<p style="margin-bottom: 1em;">4. Deploy to your kiosk displays</p>
</div>
<p style="font-size: 1.1em; color: #666; margin-top: 2em;">
Press <strong>Escape</strong> to exit this display mode
</p>
</div>''',
            'display_duration': 12,
            'order_index': 3
        }
    ]
    
    for slide_data in sample_slides:
        slide = SlideItem(
            slideshow_id=welcome_slideshow.id,
            **slide_data
        )
        db.session.add(slide)
    
    # Create a simple text-only slideshow
    simple_slideshow = Slideshow(
        name="Simple Announcements",
        description="A simple slideshow for basic text announcements"
    )
    db.session.add(simple_slideshow)
    db.session.flush()
    
    # Add simple slides
    simple_slides = [
        {
            'title': 'Important Notice',
            'content_type': 'text',
            'content_text': '''<div style="text-align: center; font-family: Arial, sans-serif; padding: 3em;">
<h1 style="color: #dc3545; font-size: 3em; margin-bottom: 1em;">NOTICE</h1>
<p style="font-size: 2em; color: #333; line-height: 1.4;">
System maintenance scheduled<br>
for tonight at 11:00 PM
</p>
<p style="font-size: 1.5em; color: #666; margin-top: 2em;">
Expected downtime: 30 minutes
</p>
</div>''',
            'display_duration': 8,
            'order_index': 0
        },
        {
            'title': 'Contact Information',
            'content_type': 'text',
            'content_text': '''<div style="text-align: center; font-family: Arial, sans-serif; padding: 3em;">
<h2 style="color: #007bff; font-size: 2.5em; margin-bottom: 1em;">Need Help?</h2>
<div style="font-size: 1.6em; color: #333; line-height: 1.8;">
<p>📧 support@company.com</p>
<p>📞 (555) 123-4567</p>
<p>🌐 help.company.com</p>
</div>
<p style="font-size: 1.2em; color: #666; margin-top: 2em;">
Available 24/7 for technical support
</p>
</div>''',
            'display_duration': 10,
            'order_index': 1
        }
    ]
    
    for slide_data in simple_slides:
        slide = SlideItem(
            slideshow_id=simple_slideshow.id,
            **slide_data
        )
        db.session.add(slide)
    
    # Commit all sample data
    db.session.commit()
    print("✅ Sample data created successfully.")
    print(f"   - Created '{welcome_slideshow.name}' with {len(sample_slides)} slides")
    print(f"   - Created '{simple_slideshow.name}' with {len(simple_slides)} slides")


@click.command()
@click.option('--sample-data', '-s', is_flag=True, 
              help='Create sample slideshow data for testing and demonstration')
@click.option('--database-url', '-d', 
              help='Database URL (overrides environment variable)')
@click.option('--force', '-f', is_flag=True,
              help='Force initialization even if tables already exist')
def main(sample_data, database_url, force):
    """
    Initialize the kiosk-show-replacement database.
    
    This command creates all necessary database tables and optionally
    adds sample data for testing and demonstration purposes.
    """
    # Set database URL if provided
    if database_url:
        os.environ['DATABASE_URL'] = database_url
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Check if database already exists (basic check)
        if not force:
            try:
                # Use SQLAlchemy inspector to check for tables
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                existing_tables = inspector.get_table_names()
                if existing_tables:
                    click.echo("⚠️  Database tables already exist.")
                    click.echo("   Use --force to reinitialize (this will not drop existing data)")
                    if not sample_data:
                        click.echo("   Use --sample-data to add sample data to existing database")
                        return
            except Exception:
                # Database doesn't exist or can't be queried, proceed with initialization
                pass
        
        # Show configuration
        click.echo("🔧 Database Configuration:")
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
        click.echo(f"   Database URL: {db_url}")
        click.echo(f"   Sample data: {'Yes' if sample_data else 'No'}")
        click.echo("")
        
        # Initialize database
        try:
            init_database(app, create_sample_data=sample_data)
            
            # Show success message with next steps
            click.echo("")
            click.echo("🎉 Initialization completed successfully!")
            click.echo("")
            click.echo("Next steps:")
            click.echo("  1. Start the development server:")
            click.echo("     poetry run python run.py")
            click.echo("  2. Open your browser to: http://localhost:5000")
            if sample_data:
                click.echo("  3. Check out the sample slideshows to see the system in action")
            else:
                click.echo("  3. Create your first slideshow in the management interface")
            
        except Exception as e:
            click.echo(f"❌ Error initializing database: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    main()
