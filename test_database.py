from database import get_connection

try:
    connection = get_connection()

    print("Successfully connected to SQL Server!")

    connection.close()

except Exception as e:
    print("Database connection failed:")
    print(e)