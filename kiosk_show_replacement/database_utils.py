"""
Database utilities and helpers for the Kiosk.show Replacement application.

This module provides utility functions for database operations including:
- Database initialization and seeding
- Common query helpers
- Health checks and maintenance
- Backup and restore utilities
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .app import db
from .models import Display, Slideshow, SlideshowItem, User


class DatabaseUtils:
    """Utility class for database operations."""
    
    @staticmethod
    def create_all_tables():
        """Create all database tables."""
        try:
            db.create_all()
            current_app.logger.info("Database tables created successfully")
            return True
        except Exception as e:
            current_app.logger.error(f"Error creating database tables: {e}")
            return False
    
    @staticmethod
    def drop_all_tables():
        """Drop all database tables."""
        try:
            db.drop_all()
            current_app.logger.info("Database tables dropped successfully")
            return True
        except Exception as e:
            current_app.logger.error(f"Error dropping database tables: {e}")
            return False
    
    @staticmethod
    def check_database_health() -> Dict[str, any]:
        """
        Check database health and connectivity.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Test basic connectivity
            result = db.session.execute(text("SELECT 1")).scalar()
            if result != 1:
                raise Exception("Basic connectivity test failed")
            
            # Check table existence
            tables = ['users', 'displays', 'slideshows', 'slideshow_items']
            table_status = {}
            
            for table in tables:
                try:
                    count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    table_status[table] = {
                        'exists': True,
                        'record_count': count_result
                    }
                except Exception as e:
                    table_status[table] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            return {
                'status': 'healthy',
                'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown'),
                'tables': table_status,
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def create_admin_user(username: str = "admin", password: str = "admin", email: Optional[str] = None) -> Optional[User]:
        """
        Create an admin user account.
        
        Args:
            username: Admin username
            password: Admin password
            email: Admin email (optional)
            
        Returns:
            Created User object or None if creation failed
        """
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                current_app.logger.warning(f"Admin user '{username}' already exists")
                return existing_user
            
            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                is_active=True,
                is_admin=True
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            current_app.logger.info(f"Admin user '{username}' created successfully")
            return admin_user
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin user - integrity constraint: {e}")
            return None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin user: {e}")
            return None
    
    @staticmethod
    def create_sample_data(user: Optional[User] = None) -> bool:
        """
        Create sample data for development and testing.
        
        Args:
            user: User to associate with sample data (if None, creates admin user)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create or get admin user
            if user is None:
                user = DatabaseUtils.create_admin_user()
                if user is None:
                    return False
            
            # Create sample slideshows
            slideshow1 = Slideshow(
                name="Welcome Slideshow",
                description="A sample welcome slideshow for new displays",
                is_default=True,
                default_item_duration=10,
                transition_type="fade",
                owner=user,
                created_by=user
            )
            
            slideshow2 = Slideshow(
                name="Company Info",
                description="Company information and announcements",
                default_item_duration=15,
                transition_type="slide",
                owner=user,
                created_by=user
            )
            
            db.session.add_all([slideshow1, slideshow2])
            db.session.flush()  # Get IDs for relationships
            
            # Create sample slideshow items for slideshow1
            items1 = [
                SlideshowItem(
                    slideshow=slideshow1,
                    title="Welcome",
                    content_type="text",
                    content_text="Welcome to our Kiosk Display System!",
                    order_index=0,
                    created_by=user
                ),
                SlideshowItem(
                    slideshow=slideshow1,
                    title="Sample Image",
                    content_type="image",
                    content_url="https://picsum.photos/1920/1080?random=1",
                    order_index=1,
                    created_by=user
                ),
                SlideshowItem(
                    slideshow=slideshow1,
                    title="Web Content",
                    content_type="url",
                    content_url="https://www.example.com",
                    display_duration=20,
                    order_index=2,
                    created_by=user
                )
            ]
            
            # Create sample slideshow items for slideshow2
            items2 = [
                SlideshowItem(
                    slideshow=slideshow2,
                    title="Company Overview",
                    content_type="text",
                    content_text="We are committed to excellence in digital signage solutions.",
                    order_index=0,
                    created_by=user
                ),
                SlideshowItem(
                    slideshow=slideshow2,
                    title="Random Image 1",
                    content_type="image",
                    content_url="https://picsum.photos/1920/1080?random=2",
                    order_index=1,
                    created_by=user
                ),
                SlideshowItem(
                    slideshow=slideshow2,
                    title="Random Image 2",
                    content_type="image",
                    content_url="https://picsum.photos/1920/1080?random=3",
                    order_index=2,
                    created_by=user
                )
            ]
            
            db.session.add_all(items1 + items2)
            
            # Create sample displays
            displays = [
                Display(
                    name="Lobby Display",
                    description="Main lobby information display",
                    resolution_width=1920,
                    resolution_height=1080,
                    location="Main Lobby",
                    current_slideshow=slideshow1,
                    owner=user,
                    created_by=user
                ),
                Display(
                    name="Conference Room A",
                    description="Conference room display",
                    resolution_width=1366,
                    resolution_height=768,
                    location="Conference Room A",
                    current_slideshow=slideshow2,
                    owner=user,
                    created_by=user
                ),
                Display(
                    name="Break Room Display",
                    description="Employee break room display",
                    resolution_width=1920,
                    resolution_height=1080,
                    location="Employee Break Room",
                    current_slideshow=slideshow1,
                    owner=user,
                    created_by=user
                )
            ]
            
            db.session.add_all(displays)
            db.session.commit()
            
            current_app.logger.info("Sample data created successfully")
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating sample data: {e}")
            return False


class QueryHelpers:
    """Helper functions for common database queries."""
    
    @staticmethod
    def get_active_slideshows(user: Optional[User] = None) -> List[Slideshow]:
        """Get all active slideshows, optionally filtered by user."""
        query = Slideshow.query.filter_by(is_active=True)
        if user:
            query = query.filter_by(owner=user)
        return query.order_by(Slideshow.name).all()
    
    @staticmethod
    def get_default_slideshow(user: Optional[User] = None) -> Optional[Slideshow]:
        """Get the default slideshow, optionally for a specific user."""
        query = Slideshow.query.filter_by(is_default=True, is_active=True)
        if user:
            query = query.filter_by(owner=user)
        return query.first()
    
    @staticmethod
    def get_online_displays(user: Optional[User] = None) -> List[Display]:
        """Get all online displays, optionally filtered by user."""
        query = Display.query.filter_by(is_active=True)
        if user:
            query = query.filter_by(owner=user)
        
        displays = query.all()
        return [d for d in displays if d.is_online]
    
    @staticmethod
    def get_displays_without_slideshow(user: Optional[User] = None) -> List[Display]:
        """Get displays that don't have an assigned slideshow."""
        query = Display.query.filter_by(is_active=True, current_slideshow_id=None)
        if user:
            query = query.filter_by(owner=user)
        return query.all()
    
    @staticmethod
    def get_slideshow_with_items(slideshow_id: int, user: Optional[User] = None) -> Optional[Slideshow]:
        """Get a slideshow with its items loaded."""
        query = Slideshow.query.filter_by(id=slideshow_id)
        if user:
            query = query.filter_by(owner=user)
        
        slideshow = query.first()
        if slideshow:
            # Ensure items are loaded
            slideshow.items
        return slideshow
    
    @staticmethod
    def search_slideshows(search_term: str, user: Optional[User] = None) -> List[Slideshow]:
        """Search slideshows by name or description."""
        search_pattern = f"%{search_term}%"
        query = Slideshow.query.filter(
            (Slideshow.name.ilike(search_pattern) | 
             Slideshow.description.ilike(search_pattern)) &
            (Slideshow.is_active == True)
        )
        if user:
            query = query.filter_by(owner=user)
        return query.order_by(Slideshow.name).all()
    
    @staticmethod
    def get_user_statistics(user: User) -> Dict[str, int]:
        """Get statistics for a user's content."""
        return {
            'total_slideshows': Slideshow.query.filter_by(owner=user).count(),
            'active_slideshows': Slideshow.query.filter_by(owner=user, is_active=True).count(),
            'total_displays': Display.query.filter_by(owner=user).count(),
            'active_displays': Display.query.filter_by(owner=user, is_active=True).count(),
            'online_displays': len(QueryHelpers.get_online_displays(user)),
        }


class BackupUtils:
    """Utilities for database backup and restore operations."""
    
    @staticmethod
    def create_sqlite_backup(backup_path: str) -> bool:
        """
        Create a backup of SQLite database.
        
        Args:
            backup_path: Path where backup file should be created
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if not db_url.startswith('sqlite:'):
                current_app.logger.error("Backup currently only supports SQLite databases")
                return False
            
            # Extract database file path from URL
            db_path = db_url.replace('sqlite:///', '').replace('sqlite:///', '')
            if not os.path.exists(db_path):
                current_app.logger.error(f"Database file not found: {db_path}")
                return False
            
            # Create backup directory if it doesn't exist
            backup_dir = os.path.dirname(backup_path)
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
            
            # Copy database file
            with sqlite3.connect(db_path) as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)
            
            current_app.logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error creating database backup: {e}")
            return False
    
    @staticmethod
    def restore_sqlite_backup(backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                current_app.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if not db_url.startswith('sqlite:'):
                current_app.logger.error("Restore currently only supports SQLite databases")
                return False
            
            # Extract database file path from URL
            db_path = db_url.replace('sqlite:///', '').replace('sqlite:///', '')
            
            # Close all database connections
            db.session.close()
            
            # Copy backup to database location
            with sqlite3.connect(backup_path) as backup_conn:
                with sqlite3.connect(db_path) as target_conn:
                    backup_conn.backup(target_conn)
            
            current_app.logger.info(f"Database restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error restoring database backup: {e}")
            return False
