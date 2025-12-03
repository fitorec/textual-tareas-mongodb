# db.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo import ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.database import Database

# Cargar configuración desde .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB")

# Inicialización por defecto
client: MongoClient | None = None
db: Database | None = None

if not MONGO_URI or not MONGO_DB_NAME:
    print("FATAL: Faltan variables MONGO_URI o MONGO_DB en el archivo .env")
else:
    try:
        # Establecer la conexión a MongoDB (timeout de 5 segundos)
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # El comando 'server_info()' fuerza la conexión para detectar errores tempranamente
        client.admin.command('serverStatus')
        
        # Crear la base de datos (lazy creation)
        db = client[MONGO_DB_NAME]
        # Obtener la colección
        
        # Configurar índice único sobre el campo 'id'
        # Esto se ejecuta solo si la conexión es exitosa
        db.tareas.create_index(
            [("id", ASCENDING)], 
            unique=True,
            background=True
        )
        
    except ConnectionFailure:
        print(f"ERROR: No se pudo conectar a MongoDB en {MONGO_URI}. Asegúrate de que el servidor esté corriendo.")
        client = None
        db = None
    except OperationFailure as e:
        print(f"ERROR: Fallo en la operación de MongoDB (ej. autenticación, permisos): {e}")
        client = None
        db = None
    except Exception as e:
        print(f"ERROR: Ocurrió un error inesperado durante la inicialización de MongoDB: {e}")
        client = None
        db = None

# Exportar las variables de conexión. Otros módulos deben verificar si 'db' es None.
# Acceso a la colección: if db is not None: collection = db.tareas
