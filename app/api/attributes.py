from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.attributes import Attribute
from app.models.sources import Source
from app.schemas.attributes import AttributeCreate, AttributeUpdate, AttributeOut
from app import db
from pydantic import ValidationError
from uuid import UUID

attributes_bp = Blueprint("attributes", __name__)

@attributes_bp.route("/attributes", methods=["POST"])
@swag_from({
    "tags": ["Attributes"],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "test_keyword"},
                    "source_id": {"type": "string", "example": "123e4567-e89b-12d3-a456-426614174000"},
                    "type": {"type": "string", "example": "test_string"},
                    "description": {"type": "string", "example": "test_description"},                    
                    
                },
                "required": ["keyword", "source_id"]
            }
        }
    ],
    "responses": {
        201: {"description": "Attribute created", "schema": AttributeOut.schema()},
        400: {"description": "Invalid input"},
        404: {"description": "Source not found"}
    }
})
def create_attribute():
    """Create a new attribute"""
    try:
        data = AttributeCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    # Kiểm tra source_id tồn tại
    if not Source.query.filter_by(id=data.source_id).first():
        return jsonify({"error": "Source not found"}), 404

    attribute = Attribute(**data.dict())
    db.session.add(attribute)
    db.session.commit()
    return jsonify(AttributeOut.from_orm(attribute).dict()), 201

@attributes_bp.route("/attributes/<attribute_id>", methods=["GET"])
@swag_from({
    "tags": ["Attributes"],
    "parameters": [
        {
            "name": "attribute_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "UUID of the attribute"
        }
    ],
    "responses": {
        200: {"description": "Attribute details", "schema": AttributeOut.schema()},
        400: {"description": "Invalid attribute_id"},
        404: {"description": "Attribute not found"}
    }
})
def get_attribute(attribute_id):
    """Get an attribute by ID"""
    try:
        UUID(attribute_id)
    except ValueError:
        return jsonify({"error": "Invalid attribute_id"}), 400

    attribute = Attribute.query.filter_by(id=attribute_id).first()
    if not attribute:
        return jsonify({"error": "Attribute not found"}), 404

    return jsonify(AttributeOut.from_orm(attribute).dict()), 200

@attributes_bp.route("/attributes", methods=["GET"])
@swag_from({
    "tags": ["Attributes"],
    "responses": {
        200: {
            "description": "List of attributes",
            "schema": {"type": "array", "items": AttributeOut.schema()}
        }
    }
})
def list_attributes():
    """List all attributes"""
    attributes = Attribute.query.all()
    return jsonify([AttributeOut.from_orm(attr).dict() for attr in attributes]), 200

@attributes_bp.route("/attributes/<attribute_id>", methods=["PUT"])
@swag_from({
    "tags": ["Attributes"],
    "parameters": [
        {
            "name": "attribute_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "UUID of the attribute"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "example": "updated_keyword"},
                    "source_id": {"type": "string", "example": "123e4567-e89b-12d3-a456-426614174000"},
                    "is_active": {"type": "boolean", "example": False}
                }
            }
        }
    ],
    "responses": {
        200: {"description": "Attribute updated", "schema": AttributeOut.schema()},
        400: {"description": "Invalid input"},
        404: {"description": "Attribute or Source not found"}
    }
})
def update_attribute(attribute_id):
    """Update an attribute"""
    try:
        UUID(attribute_id)
    except ValueError:
        return jsonify({"error": "Invalid attribute_id"}), 400

    attribute = Attribute.query.filter_by(id=attribute_id).first()
    if not attribute:
        return jsonify({"error": "Attribute not found"}), 404

    try:
        data = AttributeUpdate(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    # Kiểm tra source_id nếu được cập nhật
    if data.source_id and not Source.query.filter_by(id=data.source_id).first():
        return jsonify({"error": "Source not found"}), 404

    for key, value in data.dict(exclude_unset=True).items():
        setattr(attribute, key, value)

    db.session.commit()
    return jsonify(AttributeOut.from_orm(attribute).dict()), 200

@attributes_bp.route("/attributes/<attribute_id>", methods=["DELETE"])
@swag_from({
    "tags": ["Attributes"],
    "parameters": [
        {
            "name": "attribute_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "UUID of the attribute"
        }
    ],
    "responses": {
        204: {"description": "Attribute deleted"},
        400: {"description": "Invalid attribute_id"},
        404: {"description": "Attribute not found"}
    }
})
def delete_attribute(attribute_id):
    """Delete an attribute"""
    try:
        UUID(attribute_id)
    except ValueError:
        return jsonify({"error": "Invalid attribute_id"}), 400

    attribute = Attribute.query.filter_by(id=attribute_id).first()
    if not attribute:
        return jsonify({"error": "Attribute not found"}), 404

    db.session.delete(attribute)
    db.session.commit()
    return "", 204