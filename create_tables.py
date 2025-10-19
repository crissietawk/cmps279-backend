"""
Script to create all database tables for the Medical Management System
"""
from app.db import get_connection
import sys

def create_tables():
    """Execute the SQL schema to create all tables"""
    
    # Read the SQL file
    try:
        with open('schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
    except FileNotFoundError:
        print("✗ Error: schema.sql file not found")
        print("Please create a schema.sql file with the SQL schema provided")
        return False
    
    conn = None
    cur = None
    
    try:
        print("=" * 70)
        print("CREATING DATABASE TABLES")
        print("=" * 70)
        
        # Connect to database
        conn = get_connection()
        cur = conn.cursor()
        
        # Execute the SQL script
        cur.execute(sql_script)
        conn.commit()
        print("✓ Tables created successfully")
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        
        print(f"✓ Found {len(tables)} tables:")
        for i, (table,) in enumerate(tables, 1):
            print(f"   {i}. {table}")
        
        # Get table details
        print("\n Table Details:")
        print("-" * 70)
        
        expected_tables = [
            'doctors', 'patients', 'operating_rooms', 'surgeries', 
            'notes', 'transcriptions', 'note_analysis', 
            'notifications', 'dashboard_metrics'
        ]
        
        for table in expected_tables:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}';
            """)
            column_count = cur.fetchone()[0]
            
            if column_count > 0:
                print(f"✓ {table:25s} - {column_count} columns")
            else:
                print(f"✗ {table:25s} - NOT FOUND")
        
        # Show record counts (should all be 0 for clean schema)
        print("\n Record Counts (should all be 0):")
        print("-" * 70)
        for table in expected_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"  {table:25s}: {count} records")
            except:
                pass
        
        print("✓ DATABASE SETUP COMPLETE!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating tables: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    
    confirmation = input("Type 'DELETE ALL TABLES' to confirm: ")
    
    if confirmation != "DELETE ALL TABLES":
        print("✗ Cancelled")
        return False
    
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE';
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        
        print(f"\nDropping {len(tables)} tables...")
        
        # Drop tables in reverse order to handle dependencies
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"✓ Dropped: {table}")
        
        # Drop the UUID extension if it exists
        cur.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\" CASCADE;")
        print("✓ Dropped uuid-ossp extension")
        
        conn.commit()
        print("\n✓ All tables dropped successfully")
        print("\nYou can now run: python create_tables.py create")
        return True
        
    except Exception as e:
        print(f"\n✗ Error dropping tables: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def list_tables():
    """List all existing tables with details"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) 
                 FROM information_schema.columns 
                 WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        
        print("=" * 70)
        print(f"DATABASE TABLES ({len(tables)} total)")
        print("=" * 70)
        
        if tables:
            for table_name, column_count in tables:
                # Get record count
                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                record_count = cur.fetchone()[0]
                print(f"• {table_name:30s} {column_count:2d} columns  {record_count:5d} records")
        else:
            print("No tables found in database")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"✗ Error listing tables: {e}")
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def verify_schema():
    """Verify the schema matches expectations"""
    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        print("=" * 70)
        print("SCHEMA VERIFICATION")
        print("=" * 70)
        
        # Check for new fields
        checks = [
            ("surgeries", "participants", "JSONB field for surgery team"),
            ("notes", "note_context", "Context where note was taken"),
            ("notes", "surgery_id", "Should allow NULL values")
        ]
        
        print("\nChecking new/modified fields:")
        print("-" * 70)
        
        for table, column, description in checks:
            cur.execute(f"""
                SELECT 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name = '{column}';
            """)
            
            result = cur.fetchone()
            if result:
                data_type, is_nullable, default = result
                print(f"✓ {table}.{column}")
                print(f"  Type: {data_type}, Nullable: {is_nullable}")
                print(f"  Purpose: {description}")
            else:
                print(f"✗ {table}.{column} - NOT FOUND")
        
        print("\n" + "=" * 70)
        print("✓ SCHEMA VERIFICATION COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"✗ Error verifying schema: {e}")
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            create_tables()
        elif command == "drop":
            drop_all_tables()
        elif command == "list":
            list_tables()
        elif command == "verify":
            verify_schema()
    else:
        # Default: create tables
        create_tables()