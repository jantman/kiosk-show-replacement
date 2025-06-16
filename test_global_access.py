#!/usr/bin/env python3
"""
Quick test script to verify global access implementation.
This script demonstrates that the global access model is working correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kiosk_show_replacement.app import create_app
from kiosk_show_replacement.models import db, User, Slideshow, Display
from kiosk_show_replacement.database_utils import QueryHelpers


def test_global_access():
    """Test that global access model is working correctly."""
    print("Testing global access implementation...")
    
    # Create app and context
    app = create_app("testing")
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create two test users
        user1 = User(username="user1", email="user1@test.com", is_admin=True)
        user1.set_password("password1")
        
        user2 = User(username="user2", email="user2@test.com", is_admin=True)
        user2.set_password("password2")
        
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # User1 creates a slideshow
        slideshow1 = Slideshow(
            name="User1 Slideshow",
            description="Created by user1",
            owner_id=user1.id,
            created_by_id=user1.id,
            is_active=True
        )
        
        # User2 creates a slideshow  
        slideshow2 = Slideshow(
            name="User2 Slideshow", 
            description="Created by user2",
            owner_id=user2.id,
            created_by_id=user2.id,
            is_active=True
        )
        
        db.session.add_all([slideshow1, slideshow2])
        db.session.commit()
        
        # User1 creates a display
        display1 = Display(
            name="Display1",
            owner_id=user1.id,
            is_active=True
        )
        
        # User2 creates a display
        display2 = Display(
            name="Display2", 
            owner_id=user2.id,
            is_active=True
        )
        
        db.session.add_all([display1, display2])
        db.session.commit()
        
        print("\n=== Testing Global Access Model ===")
        
        # Test 1: QueryHelpers.get_active_slideshows should return ALL slideshows
        print("\n1. Testing get_active_slideshows:")
        all_slideshows_user1 = QueryHelpers.get_active_slideshows(user1)
        all_slideshows_user2 = QueryHelpers.get_active_slideshows(user2)
        all_slideshows_none = QueryHelpers.get_active_slideshows(None)
        
        print(f"   User1 sees {len(all_slideshows_user1)} slideshows")
        print(f"   User2 sees {len(all_slideshows_user2)} slideshows")  
        print(f"   No user filter sees {len(all_slideshows_none)} slideshows")
        
        # Should all be 2 (global access)
        assert len(all_slideshows_user1) == 2, f"Expected 2, got {len(all_slideshows_user1)}"
        assert len(all_slideshows_user2) == 2, f"Expected 2, got {len(all_slideshows_user2)}"
        assert len(all_slideshows_none) == 2, f"Expected 2, got {len(all_slideshows_none)}"
        print("   ✓ All users can see all slideshows")
        
        # Test 2: Direct database queries should return all records
        print("\n2. Testing direct Slideshow queries:")
        total_slideshows = Slideshow.query.count()
        active_slideshows = Slideshow.query.filter_by(is_active=True).count()
        
        print(f"   Total slideshows in database: {total_slideshows}")
        print(f"   Active slideshows in database: {active_slideshows}")
        assert total_slideshows == 2
        assert active_slideshows == 2
        print("   ✓ Database queries return all records")
        
        # Test 3: User statistics should show system totals (global access)
        print("\n3. Testing user statistics:")
        user1_stats = QueryHelpers.get_user_statistics(user1)
        user2_stats = QueryHelpers.get_user_statistics(user2)
        
        print(f"   User1 stats: {user1_stats}")
        print(f"   User2 stats: {user2_stats}")
        
        # Both users should see the same totals (global access)
        assert user1_stats['total_slideshows'] == 2
        assert user2_stats['total_slideshows'] == 2
        assert user1_stats['active_slideshows'] == 2
        assert user2_stats['active_slideshows'] == 2
        assert user1_stats['total_displays'] == 2
        assert user2_stats['total_displays'] == 2
        print("   ✓ User statistics show system totals (global access)")
        
        # Test 4: Online displays
        print("\n4. Testing online displays:")
        online_displays_user1 = QueryHelpers.get_online_displays(user1)
        online_displays_user2 = QueryHelpers.get_online_displays(user2)
        online_displays_none = QueryHelpers.get_online_displays(None)
        
        print(f"   User1 sees {len(online_displays_user1)} online displays")
        print(f"   User2 sees {len(online_displays_user2)} online displays")
        print(f"   No user filter sees {len(online_displays_none)} online displays")
        
        # All should see the same (global access)
        assert len(online_displays_user1) == len(online_displays_user2)
        assert len(online_displays_user1) == len(online_displays_none)
        print("   ✓ All users see the same online displays")
        
        print("\n=== Global Access Model Test PASSED ===")
        print("✅ All authenticated users can see and access all slideshows and displays")
        print("✅ User filtering is disabled - implementing true global access")
        print("✅ This is appropriate for a single-tenant digital signage system")
        

if __name__ == "__main__":
    test_global_access()
