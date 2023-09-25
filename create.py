import sqlite3

# Connect to the SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect("chathistory.db")

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Define the SQL command to create the chat_history table
create_table_sql = """
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY,
    role TEXT,
    content TEXT,
    time TEXT
)
"""

# Execute the SQL command to create the table
cursor.execute(create_table_sql)

# Commit the changes and close the database connection
conn.commit()
conn.close()

print("chathistory.db created successfully")