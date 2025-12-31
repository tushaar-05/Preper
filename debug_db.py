import os
from dotenv import load_dotenv
import pymysql

def debug_db():
    print("🔍 Diagnosing Database Connection...")
    
    # 1. Check for .env file
    if not os.path.exists('.env'):
        print("❌ .env file not found in the current directory.")
        return
    
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("⚠️  DATABASE_URL not found in .env file.")
        print("💡 Defaulting to: mysql+pymysql://root@localhost/nst_prep_db")
        user = 'root'
        password = ''
        host = 'localhost'
        port = 3306
        db_name = 'nst_prep_db'
    else:
        print(f"✅ DATABASE_URL found: {db_url.split('@')[0]}@...") # Mask password
        try:
            # Simple parsing for mysql+pymysql://user:pass@host:port/db
            connection_part = db_url.split('://')[1]
            auth_host, db_name = connection_part.split('/')
            
            if '@' in auth_host:
                creds, host_port = auth_host.split('@')
            else:
                creds = auth_host
                host_port = 'localhost'
            
            creds_parts = creds.split(':')
            user = creds_parts[0]
            password = creds_parts[1] if len(creds_parts) > 1 else ''
            
            if ':' in host_port:
                host, port_str = host_port.split(':')
                port = int(port_str)
            else:
                host = host_port
                port = 3306
        except Exception as e:
            print(f"❌ Correctly parsing DATABASE_URL failed: {e}")
            return

    # 2. Test Connection
    print(f"\n📡 Attempting to connect to '{db_name}' on '{host}:{port}' as '{user}'...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name
        )
        print("✅ Connection successful!")
        conn.close()
    except pymysql.err.OperationalError as e:
        print(f"❌ Connection FAILED: {e}")
        errorCode = e.args[0]
        
        if errorCode == 1045:
            print("\n💡 SOLUTION: Access Denied. Please check your username and password in .env.")
        elif errorCode == 1049:
            print(f"\n💡 SOLUTION: Database '{db_name}' does not exist.")
        elif errorCode == 2003:
            print("\n💡 SOLUTION: Could not connect to MySQL server. Is it running or is the host/port correct?")
        else:
            print(f"\n💡 SOLUTION: Please check your database credentials in the .env file.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    debug_db()
