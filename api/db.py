import os
import sys
from mysql.connector import pooling

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

connection_pool = None


def initialize_pool():
    """Initialize the MySQL connection pool"""
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="pocketurl_pool",
                pool_size=5,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
        except Exception as e:
            print(f"[db error] initialize_pool(): {e}", file=sys.stderr)
            raise
    return connection_pool


def get_db():
    """Get a connection from the pool"""
    try:
        pool = initialize_pool()
        return pool.get_connection()
    except Exception as e:
        print(f"[db error] get_db: {e}", file=sys.stderr)
        raise


def create_short_url(long_url, shortener):
    """Create a short URL for a given long URL"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("INSERT INTO urls (long_url) VALUES (%s)", (long_url,))
        conn.commit()

        # Get the primary key of the inserted row
        counter = cursor.lastrowid
        short_url = shortener(counter)

        # Update the row with the short URL
        cursor.execute(
            "UPDATE urls SET short_url = %s WHERE counter = %s", (short_url, counter)
        )
        conn.commit()

        return short_url
    except Exception as e:
        conn.rollback()
        print(f"[db error] create_short_url(): {e}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()


def get_long_url(short_url, invshortener):
    """Get the original URL from a short URL code"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # Decode the short URL to get the primary key counter
        counter = invshortener(short_url)
        if counter is None:
            return None, None

        cursor.execute("SELECT long_url, hits FROM urls WHERE counter = %s", (counter,))
        row = cursor.fetchone()

        if row is None:
            return None, None

        long_url, hits = row["long_url"], row["hits"]

        cursor.execute("UPDATE urls SET hits = hits + 1 WHERE counter = %s", (counter,))
        conn.commit()

        return long_url, hits + 1
    except Exception as e:
        conn.rollback()
        print(f"[db error] get_long_url: {e}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()


def get_hits(short_url, invshortener):
    """Get the number of hits for a short URL"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        counter = invshortener(short_url)
        if counter is None:
            return None

        cursor.execute("SELECT hits FROM urls WHERE counter = %s", (counter,))
        row = cursor.fetchone()

        if row is None:
            return None

        hits = row["hits"]
        return hits
    except Exception as e:
        print(f"[db error] get_hits(): {e}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()


def check_db_connection():
    """Check if the database connection is working"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[db error] check_db_connection(): {e}", file=sys.stderr)
        return False
