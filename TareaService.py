# TareaService.py
from db import db
from pymongo.collection import Collection

class TareaService:
    """Capa de servicio para manipular la colección 'tareas' en MongoDB."""
    
    # Inicialización condicional del objeto Collection. 
    # Usamos 'is not None' para evitar el NotImplementedError de PyMongo.
    _collection: Collection | None = db.tareas if db is not None else None

    @classmethod
    def list(cls) -> list[dict]:
        """Devuelve todas las tareas ordenadas por ID (int)."""
        if cls._collection is None: return [] 
        # Excluir el campo '_id' de MongoDB para simplicidad
        return list(cls._collection.find({}, {"_id": 0}).sort("id", 1))

    @classmethod
    def next_id(cls) -> int:
        """Calcula el próximo ID incremental."""
        # ⚠️ Verificación explícita
        if cls._collection is None: return 1 
        # Busca el máximo ID existente
        last_tarea = cls._collection.find_one(
            sort=[("id", -1)], 
            projection={"id": 1}
        )
        # Si no hay tareas, el siguiente ID es 1, si no, es max_id + 1
        max_id = last_tarea.get("id", 0) if last_tarea else 0
        return max_id + 1

    @classmethod
    def insert(cls, tarea_dict: dict) -> dict:
        """Inserta una tarea con un ID auto-generado."""
        # ⚠️ Verificación explícita
        if cls._collection is None: return {} 
        # Asigna el nuevo ID incremental
        tarea_dict["id"] = cls.next_id()
        
        # El campo 'id' es el RowKey en Textual, lo guardamos como int
        result = cls._collection.insert_one(tarea_dict)
        
        # Devuelve la tarea insertada (sin el _id)
        inserted_tarea = cls.get(tarea_dict["id"])
        return inserted_tarea if inserted_tarea else {}

    @classmethod
    def get(cls, id_value: int) -> dict | None:
        """Obtiene una tarea por su campo 'id' (int)."""
        # ⚠️ Verificación explícita
        if cls._collection is None: return None
        # Excluir el campo '_id' de MongoDB
        tarea = cls._collection.find_one({"id": id_value}, {"_id": 0})
        return tarea

    @classmethod
    def update(cls, id_value: int, tarea_updates: dict) -> dict | None:
        """Actualiza una tarea por su campo 'id' (int). No permite modificar el campo 'id'."""
        # ⚠️ Verificación explícita
        if cls._collection is None: return None
        # Asegurarse de que el 'id' no se pueda modificar
        if "id" in tarea_updates:
            del tarea_updates["id"]
        
        # Actualiza la tarea
        result = cls._collection.update_one(
            {"id": id_value},
            {"$set": tarea_updates}
        )
        
        # Devuelve la tarea actualizada
        return cls.get(id_value) if result.modified_count > 0 else None

    @classmethod
    def delete(cls, id_value: int) -> bool:
        """Elimina la tarea del ID dado."""
        # ⚠️ Verificación explícita
        if cls._collection is None: return False
        result = cls._collection.delete_one({"id": id_value})
        return result.deleted_count > 0