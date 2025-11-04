import sqlite3 as db

DATABASE_NAME = "dfs.db"

def get_connection():
    conn = db.connect(DATABASE_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS file_metadata (
            file_hash TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            num_chunks INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS file_chunks (
            file_hash TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_hash TEXT NOT NULL,
            datanode_host TEXT NOT NULL,
            datanode_port INTEGER NOT NULL,
            PRIMARY KEY (file_hash, chunk_index, datanode_host, datanode_port),
            FOREIGN KEY (file_hash) REFERENCES file_metadata(file_hash) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

init_db()

def store_file_metadata(file_hash, file_name, file_size, num_chunks, placements, chunk_hashes=None):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        existing = cur.execute(
            "SELECT file_hash FROM file_metadata WHERE file_hash = ?",
            (file_hash,)
        ).fetchone()
        
        if existing:
            return True
        
        cur.execute("""
            INSERT INTO file_metadata (file_hash, file_name, file_size, num_chunks)
            VALUES (?, ?, ?, ?)
        """, (file_hash, file_name, file_size, num_chunks))
        
        for chunk_id, datanodes in placements.items():
            chunk_index = int(chunk_id.split('_')[1])
            
            chunk_hash = ""
            if chunk_hashes and len(chunk_hashes) >= chunk_index:
                chunk_hash = chunk_hashes[chunk_index - 1]
            
            for datanode in datanodes:
                host, port = datanode.split(':')
                cur.execute("""
                    INSERT INTO file_chunks (file_hash, chunk_index, chunk_hash, datanode_host, datanode_port)
                    VALUES (?, ?, ?, ?, ?)
                """, (file_hash, chunk_index, chunk_hash, host, int(port)))
        
        conn.commit()
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error storing metadata: {e}")
        return False

def get_file_metadata(filename):
    conn = get_connection()
    cur = conn.cursor()
    
    result = cur.execute("""
        SELECT file_hash, file_size, upload_time, num_chunks
        FROM file_metadata
        WHERE file_name = ?
    """, (filename,)).fetchone()
    
    conn.close()
    
    if result:
        return {
            "file_hash": result[0],
            "file_name": result[1],
            "file_size": result[2],
            "upload_time": result[3],
            "num_chunks": result[4]
        }
    return None

def get_chunk_locations(file_hash):
    conn = get_connection()
    cur = conn.cursor()
    
    results = cur.execute("""
        SELECT chunk_index, chunk_hash, datanode_host, datanode_port
        FROM file_chunks
        WHERE file_hash = ?
        ORDER BY chunk_index
    """, (file_hash,)).fetchall()
    
    conn.close()
    
    chunks = {}
    for row in results:
        chunk_idx = row[0]
        if chunk_idx not in chunks:
            chunks[chunk_idx] = {
                "chunk_hash": row[1],
                "datanodes": []
            }
        chunks[chunk_idx]["datanodes"].append(f"{row[2]}:{row[3]}")
    
    return chunks

def list_all_files():
    conn = get_connection()
    cur = conn.cursor()
    
    results = cur.execute("""
        SELECT file_hash, file_name, file_size, upload_time, num_chunks
        FROM file_metadata
        ORDER BY upload_time DESC
    """).fetchall()
    
    conn.close()
    
    return [{
        "file_hash": row[0],
        "file_name": row[1],
        "file_size": row[2],
        "upload_time": row[3],
        "num_chunks": row[4]
    } for row in results]

def delete_file_metadata(file_hash):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM file_metadata WHERE file_hash = ?", (file_hash,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error deleting metadata: {e}")
        return False
