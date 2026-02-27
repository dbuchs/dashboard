try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

BUILT_IN_SCHEMAS = {
    "math": {
        "type": "object",
        "properties": {
            "lesson_number": {"type": ["string", "number"]},
            "correct": {"type": "number"},
            "total": {"type": "number"},
            "notes": {"type": "string"},
        },
    },
    "reading": {
        "type": "object",
        "properties": {
            "book_title": {"type": "string"},
            "pages_from": {"type": "number"},
            "pages_to": {"type": "number"},
            "student_summary": {"type": "string"},
            "teacher_corrections": {"type": "string"},
            "grade": {"type": "string"},
            "notes": {"type": "string"},
        },
    },
    "latin": {
        "type": "object",
        "properties": {
            "minutes_translating": {"type": "number"},
            "minutes_vocab": {"type": "number"},
            "minutes_grammar": {"type": "number"},
            "notes": {"type": "string"},
        },
    },
    "generic": {
        "type": "object",
        "properties": {
            "notes": {"type": "string"},
        },
    },
}


def validate_annotation(annotation, schema):
    """Returns list of error strings, or empty list if valid."""
    if not HAS_JSONSCHEMA:
        return []
    try:
        jsonschema.validate(annotation, schema)
        return []
    except jsonschema.ValidationError as e:
        return [e.message]
    except jsonschema.SchemaError as e:
        return [f"Schema error: {e.message}"]
