"""
Create MySQL Database Script
Creates the nst_prep_db database if it doesn't exist
"""

import pymysql
import sys

def create_database():
    """Create the database for NST Prep application"""
    try:
        # Connect to MySQL server (without specifying database)
        print("🔌 Connecting to MySQL server...")
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # XAMPP default has no password
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✅ Connected to MySQL server!")
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            print("🏗️  Creating database 'nst_prep_db'...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS nst_prep_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'nst_prep_db' created successfully!")
            
            # Show all databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("\n📊 Available databases:")
            for db in databases:
                db_name = db['Database']
                if db_name == 'nst_prep_db':
                    print(f"   ✓ {db_name} (NST Prep Database)")
                else:
                    print(f"   - {db_name}")
        
        connection.close()
        print("\n🎉 Database setup complete!")
        print("\n📝 Next steps:")
        print("   1. Run: python init_db.py")
        print("   2. This will create all tables and seed sample data")
        
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ Error: {e}")
        print("\n⚠️  Troubleshooting:")
        print("   1. Make sure XAMPP is running")
        print("   2. Start MySQL from XAMPP Control Panel")
        print("   3. Check if MySQL is running on port 3306")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
