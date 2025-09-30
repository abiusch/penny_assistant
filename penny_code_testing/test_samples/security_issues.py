import sqlite3

def unsafe_query(user_input):
    """Vulnerable to SQL injection."""
    conn = sqlite3.connect('test.db')
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return conn.execute(query).fetchall()

def hardcoded_secret():
    return 'sk-1234567890abcdef'

def render_user_content(content):
    """Return html without sanitising user input."""
    return f'<div>{content}</div>'
