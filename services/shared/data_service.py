
from typing import List, Tuple, Optional, Any, Dict, Type, TypeVar
from shared.models import User, Plant, Component, Alert, Intervention, PlantRegistration

ModelType = TypeVar('ModelType')


class DataService:
    """Service to handle data transformation between models and database."""

    # Mapping of model classes to their tuple unpacking methods
    MODEL_MAP = {
        'User': User,
        'Plant': Plant,
        'Component': Component,
        'Alert': Alert,
        'Intervention': Intervention,
        'PlantRegistration': PlantRegistration,
    }

    @staticmethod
    def tuple_to_model(row: Tuple, model_class: Type[ModelType]) -> Optional[ModelType]:
        """Convert database tuple to model instance."""
        if not row:
            return None
        return model_class.from_tuple(row)

    @staticmethod
    def tuples_to_models(rows: List[Tuple], model_class: Type[ModelType]) -> List[ModelType]:
        """Convert multiple database tuples to model instances."""
        return [DataService.tuple_to_model(row, model_class) for row in rows if row]

    @staticmethod
    def model_to_dict(model: Any) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        if hasattr(model, 'to_dict'):
            return model.to_dict()
        return model.__dict__

    @staticmethod
    def dict_to_model(data: Dict[str, Any], model_class: Type[ModelType]) -> Optional[ModelType]:
        """Convert dictionary to model instance."""
        if not data:
            return None
        return model_class.from_dict(data)

    @staticmethod
    def models_to_dicts(models: List[Any]) -> List[Dict[str, Any]]:
        """Convert multiple models to dictionaries."""
        return [DataService.model_to_dict(m) for m in models if m]

    @staticmethod
    def get_model_fields(model_class: Type[ModelType]) -> List[str]:
        """Get list of field names for a model."""
        if hasattr(model_class, '__dataclass_fields__'):
            return list(model_class.__dataclass_fields__.keys())
        return []

    @staticmethod
    def extract_insert_values(model: Any, exclude_fields: Optional[List[str]] = None) -> Tuple[List[str], Tuple]:
        """
        Extract field names and values from model for INSERT operation.
        Excludes None values and specified fields (typically 'id' for auto-increment).
        """
        exclude_fields = exclude_fields or ['id']
        data = DataService.model_to_dict(model)
        
        fields = []
        values = []
        for key, value in data.items():
            if key not in exclude_fields and value is not None:
                fields.append(key)
                values.append(value)
        
        return fields, tuple(values)

    @staticmethod
    def extract_update_values(model: Any, exclude_fields: Optional[List[str]] = None) -> Tuple[List[str], Tuple]:
        """
        Extract field names and values from model for UPDATE operation.
        Excludes specified fields (typically 'id').
        """
        exclude_fields = exclude_fields or ['id', 'created_at']
        data = DataService.model_to_dict(model)
        
        fields = []
        values = []
        for key, value in data.items():
            if key not in exclude_fields and value is not None:
                fields.append(key)
                values.append(value)
        
        return fields, tuple(values)

    @staticmethod
    def build_filter_clause(filters: Dict[str, Any]) -> Tuple[str, Tuple]:
        """
        Build WHERE clause from filter dictionary.
        Returns (where_clause, values_tuple)
        """
        if not filters:
            return "", ()
        
        clauses = []
        values = []
        for key, value in filters.items():
            if value is not None:
                clauses.append(f"{key} = %s")
                values.append(value)
        
        where_clause = "WHERE " + " AND ".join(clauses) if clauses else ""
        return where_clause, tuple(values)
