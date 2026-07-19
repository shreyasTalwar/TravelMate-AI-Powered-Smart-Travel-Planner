import os
import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine
from app import create_app
from extensions import db

# Load environment variables
load_dotenv()

db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/travelmate')

print("Connecting to MySQL to check/create database...")
try:
    # Extract connection parameters from URL
    # Format: mysql+pymysql://user:pass@host:port/dbname
    # We want to connect to host:port first without db name to ensure DB exists
    import urllib.parse
    conn_part = db_url.split("://")[1]
    user_pass, host_db = conn_part.split("@")
    user, password = user_pass.split(":")
    user = urllib.parse.unquote(user)
    password = urllib.parse.unquote(password)
    
    if "/" in host_db:
        host_port, db_name = host_db.split("/")
    else:
        host_port = host_db
        db_name = "travelmate"
        
    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 3306

    print(f"Server Host: {host}, Port: {port}, User: {user}")
    
    # Establish raw connection to MySQL server
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password
    )
    
    with connection.cursor() as cursor:
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"Database '{db_name}' checked/created successfully!")
        
    connection.close()

    # Now, run Flask app context db.create_all() to verify SQLAlchemy models
    print("Initializing Flask App and generating tables...")
    app = create_app()
    with app.app_context():
        db.create_all()
        print("SQLAlchemy database tables created successfully!")
        print("Verify DB Succeeded!")
        
except Exception as e:
    print(f"Error during DB verification/creation: {str(e)}")
    print("\nPlease verify your DATABASE_URL in .env matches your MySQL server details.")
