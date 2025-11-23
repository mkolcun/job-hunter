#!/usr/bin/env python3
"""
Schema Processor

Loads, validates, and processes extraction schemas for job scraping.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class SchemaProcessor:
    """Process and validate extraction schemas."""

    def __init__(self, schema_path: str = "config/extraction_schema.json"):
        """
        Initialize schema processor.

        Args:
            schema_path: Path to schema JSON file
        """
        self.schema_path = schema_path
        self.schema: Optional[Dict] = None
        self.all_fields: Dict[str, Dict] = {}
        self.validation_errors: List[str] = []

    def load(self) -> bool:
        """
        Load schema from file.

        Returns:
            True if loaded successfully
        """
        try:
            with open(self.schema_path, 'r') as f:
                self.schema = json.load(f)

            # Compile all fields
            self._compile_fields()

            # Validate schema
            if not self._validate():
                print("⚠️  Schema validation warnings:")
                for error in self.validation_errors:
                    print(f"  - {error}")
                return False

            return True

        except FileNotFoundError:
            print(f"❌ Schema file not found: {self.schema_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in schema: {e}")
            return False

    def _compile_fields(self) -> None:
        """Compile all fields from all priority levels."""
        extraction_schema = self.schema.get("extraction_schema", {})

        for priority in ["required", "high_priority", "medium_priority", "optional", "custom_fields"]:
            if priority in extraction_schema:
                self.all_fields.update(extraction_schema[priority])

    def _validate(self) -> bool:
        """
        Validate schema structure and configuration.

        Returns:
            True if valid (warnings may exist)
        """
        is_valid = True
        extraction_schema = self.schema.get("extraction_schema", {})

        # Check required section exists
        if "required" not in extraction_schema:
            self.validation_errors.append("Missing 'required' section")
            is_valid = False

        # Check at least 3 required fields
        required_count = len(extraction_schema.get("required", {}))
        if required_count < 3:
            self.validation_errors.append(
                f"Only {required_count} required fields (recommended: 3+)"
            )

        # Validate each field
        for field_name, field_config in self.all_fields.items():
            # Check type
            if "type" not in field_config:
                self.validation_errors.append(f"Field '{field_name}' missing 'type'")
                is_valid = False

            # Check aliases
            if "aliases" not in field_config or not field_config["aliases"]:
                self.validation_errors.append(
                    f"Field '{field_name}' has no aliases (recommended)"
                )

            # Check confidence threshold
            conf = field_config.get("min_confidence", 0)
            if conf < 0 or conf > 100:
                self.validation_errors.append(
                    f"Field '{field_name}' invalid confidence: {conf} (must be 0-100)"
                )
                is_valid = False

        return is_valid

    def get_field_config(self, field_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific field.

        Args:
            field_name: Name of field

        Returns:
            Field configuration dict
        """
        return self.all_fields.get(field_name)

    def get_all_fields(self) -> Dict[str, Dict]:
        """Get all fields from all priority levels."""
        return self.all_fields

    def get_required_fields(self) -> List[str]:
        """Get list of required field names."""
        extraction_schema = self.schema.get("extraction_schema", {})
        return list(extraction_schema.get("required", {}).keys())

    def get_field_aliases(self, field_name: str) -> List[str]:
        """
        Get all aliases for a field.

        Args:
            field_name: Name of field

        Returns:
            List of aliases
        """
        field_config = self.get_field_config(field_name)
        if field_config:
            return field_config.get("aliases", [field_name])
        return [field_name]

    def get_extraction_settings(self) -> Dict:
        """Get extraction settings from schema."""
        return self.schema.get("extraction_settings", {})

    def get_field_count(self) -> int:
        """Get total number of fields in schema."""
        return len(self.all_fields)

    def export_summary(self) -> str:
        """
        Export human-readable schema summary.

        Returns:
            Formatted summary string
        """
        lines = ["Extraction Schema Summary", "=" * 50, ""]

        extraction_schema = self.schema.get("extraction_schema", {})

        # Required fields
        required = extraction_schema.get("required", {})
        lines.append(f"Required Fields ({len(required)}):")
        for name in required.keys():
            lines.append(f"  - {name}")
        lines.append("")

        # High priority
        high = extraction_schema.get("high_priority", {})
        if high:
            lines.append(f"High Priority ({len(high)}):")
            for name in high.keys():
                lines.append(f"  - {name}")
            lines.append("")

        # Optional
        optional = extraction_schema.get("optional", {})
        if optional:
            lines.append(f"Optional Fields ({len(optional)}):")
            for name in optional.keys():
                lines.append(f"  - {name}")
            lines.append("")

        # Settings
        settings = self.get_extraction_settings()
        lines.append("Settings:")
        for key, value in settings.items():
            lines.append(f"  {key}: {value}")

        return "\n".join(lines)


# JSON I/O Interface for Agent Calls
if __name__ == "__main__":
    import json
    import sys

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        action = input_data.get("action", "load")

        schema_path = input_data.get("schema_path", "config/extraction_schema.json")
        processor = SchemaProcessor(schema_path)

        if action == "load":
            # Load and validate schema
            if processor.load():
                result = {
                    "success": True,
                    "schema": processor.schema,
                    "field_count": processor.get_field_count(),
                    "required_fields": processor.get_required_fields()
                }
            else:
                result = {
                    "success": False,
                    "error": "Schema validation failed",
                    "validation_errors": processor.validation_errors
                }

        elif action == "get_summary":
            # Get schema summary
            if processor.load():
                result = {
                    "success": True,
                    "summary": processor.export_summary(),
                    "field_count": processor.get_field_count()
                }
            else:
                result = {
                    "success": False,
                    "error": "Failed to load schema"
                }

        elif action == "get_field_config":
            # Get configuration for specific field
            field_name = input_data.get("field_name")
            if processor.load():
                field_config = processor.get_field_config(field_name)
                if field_config:
                    result = {
                        "success": True,
                        "field_config": field_config,
                        "aliases": processor.get_field_aliases(field_name)
                    }
                else:
                    result = {
                        "success": False,
                        "error": f"Field '{field_name}' not found in schema"
                    }
            else:
                result = {
                    "success": False,
                    "error": "Failed to load schema"
                }

        else:
            result = {"success": False, "error": f"Unknown action: {action}"}

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)
