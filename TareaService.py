# TareaService.py
from db import db
from pymongo.collection import Collection

class TareaService:
    """Capa de servicio para manipular la colección 'tareas' en MongoDB."""

    _collection: Collection | None = db.tareas if db is not None else None

    # ----------------------------------------------------------------------
    # LISTAR
    # ----------------------------------------------------------------------
    @classmethod
    def list(cls) -> list[dict]:
        """Devuelve todas las tareas usando aggregate() con sort y project."""
        if cls._collection is None:
            return []

        pipeline = [
            {"$project": {"_id": 0}},     # Ocultar _id
            {"$sort": {"id": 1}},         # Ordenar por id ascendente
        ]

        return list(cls._collection.aggregate(pipeline))


    # ----------------------------------------------------------------------
    # NEXT ID
    # ----------------------------------------------------------------------
    @classmethod
    def next_id(cls) -> int:
        """Obtiene el siguiente ID incremental usando aggregate()."""
        if cls._collection is None:
            return 1

        pipeline = [
            {"$sort": {"id": -1}},        # Orden descendente
            {"$limit": 1},                # Solo el máximo
            {"$project": {"id": 1}},      # Obtener solo id
        ]

        result = list(cls._collection.aggregate(pipeline))
        max_id = result[0]["id"] if result else 0
        return max_id + 1


    # ----------------------------------------------------------------------
    # INSERTAR
    # ----------------------------------------------------------------------
    @classmethod
    def insert(cls, tarea_dict: dict) -> dict:
        """Inserta una tarea y la devuelve usando aggregate()."""
        if cls._collection is None:
            return {}

        tarea_dict["id"] = cls.next_id()
        cls._collection.insert_one(tarea_dict)

        return cls.get(tarea_dict["id"]) or {}


    # ----------------------------------------------------------------------
    # OBTENER UNA TAREA
    # ----------------------------------------------------------------------
    @classmethod
    def get(cls, id_value: int) -> dict | None:
        """Obtiene una tarea por id usando aggregate()."""
        if cls._collection is None:
            return None

        pipeline = [
            {"$match": {"id": id_value}},   # Filtrar por ID
            {"$project": {"_id": 0}},       # Ocultar _id
            {"$limit": 1},
        ]

        result = list(cls._collection.aggregate(pipeline))
        return result[0] if result else None


    # ----------------------------------------------------------------------
    # ACTUALIZAR
    # ----------------------------------------------------------------------
    @classmethod
    def update(cls, id_value: int, tarea_updates: dict) -> dict | None:
        """Actualiza una tarea por id."""
        if cls._collection is None:
            return None

        # No permitir modificar el ID
        tarea_updates.pop("id", None)

        result = cls._collection.update_one(
            {"id": id_value},
            {"$set": tarea_updates}
        )

        return cls.get(id_value) if result.modified_count > 0 else None


    # ----------------------------------------------------------------------
    # ELIMINAR
    # ----------------------------------------------------------------------
    @classmethod
    def delete(cls, id_value: int) -> bool:
        """Elimina una tarea por id."""
        if cls._collection is None:
            return False

        result = cls._collection.delete_one({"id": id_value})
        return result.deleted_count > 0
