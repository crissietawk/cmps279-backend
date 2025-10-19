"""
Run database migrations
"""
from app.db import get_connection

def run_migration(filename):
    """Execute SQL migration file"""
    try:
        print(f"Running {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Execute the SQL
        cur.execute(sql)
        conn.commit()
        
        print(f"✓ {filename} completed successfully")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error running {filename}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING DATABASE MIGRATIONS")
    print("=" * 70)
    
    # Run migrations in order
    migrations = [
        'migrations/add_auth.sql',
        'migrations/fix_columns.sql'
    ]
    
    for migration in migrations:
        if not run_migration(migration):
            print(f"\n✗ Migration failed: {migration}")
            print("Please fix the error and try again")
            break
    else:
        print("\n" + "=" * 70)
        print("✓ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
