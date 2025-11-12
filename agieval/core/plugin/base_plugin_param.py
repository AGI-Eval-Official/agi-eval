from pydantic import BaseModel, Field, model_validator
from typing import get_type_hints
import base64
import json
import inspect


class BasePluginParam(BaseModel):
    benchmark_id: str = Field(default="", description="Dataset ID")
    work_dir: str = Field(default="result/tmp", description="Cache directory, stores temporary data, evaluation results, etc.")

    model_config = {
        "arbitrary_types_allowed": True,  # Allow arbitrary types
        "coerce_numbers_to_str": True,    # Force numbers to strings
        "extra": "ignore",                # Ignore extra fields
    }    
    
    @model_validator(mode='before')
    @classmethod
    def decode_base64_fields(cls, data):
        if not isinstance(data, dict):
            return data
            
        # Get all field types of the class
        type_hints = get_type_hints(cls)
        processed_data = data.copy()
        
        for field_name, field_type in type_hints.items():
            # Check if field is in input
            if field_name not in processed_data:
                continue
            # Check if field type is a subclass of BaseModel
            if not inspect.isclass(field_type) or not issubclass(field_type, BaseModel):
                continue

            value = processed_data[field_name]
            # If value is a string, try base64 decoding
            if isinstance(value, str):
                try:
                    # base64 decode
                    decoded_bytes = base64.b64decode(value)
                    # Parse JSON
                    decoded_dict = json.loads(decoded_bytes.decode('utf-8'))
                    # Replace original value
                    processed_data[field_name] = decoded_dict
                except Exception as e:
                    print(f"Error decoding base64 for field {field_name}: {e}")
        
        return processed_data

class BaseStagePluginParam(BasePluginParam):
    use_cache: bool = Field(default=True, description="Whether to use cache")

class BaseStepPluginParam(BasePluginParam):
    pass