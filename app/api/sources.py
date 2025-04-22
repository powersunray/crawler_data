from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.sources import Source
from app.schemas.sources import SourceCreate, SourceUpdate, SourceOut
from app import db
from pydantic import ValidationError
from uuid import UUID

sources_bp = Blueprint("sources", __name__)

@sources_bp.route("/sources", methods=["POST"])
@swag_from({
    "tags": ["Sources"],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "example": "https://example.com"},
                    "link_selector": {"type": "string", "example": ".link-class"},
                    "threads": {"type": "integer", "example": 4},
                    "description": {"type": "string", "example": "Test source"},
                    "card_information": {"type": "string", "example": "Card info"},
                    "status": {"type": "string", "example": "ACTIVE"}
                },
                "required": ["url", "link_selector", "threads", "description", "card_information"]
            }
        }
    ],
    "responses": {
        201: {"description": "Source created"},
        400: {"description": "Invalid input"}
    }
})
def create_source():
    try:
        data = SourceCreate(**request.get_json())  # Validate dữ liệu đầu vào
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    source = Source(**data.dict())  # Tạo instance từ dữ liệu
    db.session.add(source)
    db.session.commit()

    # Trả về dữ liệu thủ công để tránh lỗi Pydantic
    return jsonify({
        "id": str(source.id),
        "url": source.url,
        "link_selector": source.link_selector,
        "status": source.status,
        "threads": source.threads,
        "description": source.description,
        "card_information": source.card_information
    }), 201

@sources_bp.route("/sources", methods=["GET"])
@swag_from({
    "tags": ["Sources"],
    "responses": {
        200: {
            "description": "List of sources",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "url": {"type": "string"},
                        "link_selector": {"type": "string"},
                        "status": {"type": "string"},
                        "threads": {"type": "integer"},
                        "description": {"type": "string"},
                        "card_information": {"type": "string"}
                    }
                }
            }
        }
    }
})
def list_sources():
    sources = Source.query.all()
    return jsonify([{
        "id": str(source.id),
        "url": source.url,
        "link_selector": source.link_selector,
        "status": source.status,
        "threads": source.threads,
        "description": source.description,
        "card_information": source.card_information
    } for source in sources]), 200

@sources_bp.route("/sources/<source_id>", methods=["GET"])
@swag_from({
    "tags": ["Sources"],
    "parameters": [
        {
            "name": "source_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "UUID of the source"
        }
    ],
    "responses": {
        200: {
            "description": "Source details",
            "schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "url": {"type": "string"},
                    "link_selector": {"type": "string"},
                    "status": {"type": "string"},
                    "threads": {"type": "integer"},
                    "description": {"type": "string"},
                    "card_information": {"type": "string"}
                }
            }
        },
        400: {"description": "Invalid source_id"},
        404: {"description": "Source not found"}
    }
})
def get_source(source_id):
    try:
        UUID(source_id)
    except ValueError:
        return jsonify({"error": "Invalid source_id"}), 400

    source = Source.query.filter_by(id=source_id).first()
    if not source:
        return jsonify({"error": "Source not found"}), 404

    return jsonify({
        "id": str(source.id),
        "url": source.url,
        "link_selector": source.link_selector,
        "status": source.status,
        "threads": source.threads,
        "description": source.description,
        "card_information": source.card_information
    }), 200

@sources_bp.route("/sources/<source_id>", methods=["PUT"])
@swag_from({
    "tags": ["Sources"],
    "parameters": [
        {
            "name": "source_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "UUID of the source"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "link_selector": {"type": "string"},
                    "threads": {"type": "integer"},
                    "description": {"type": "string"},
                    "card_information": {"type": "string"},
                    "status": {"type": "string"}
                }
            }
        }
    ],
    "responses": {
        200: {"description": "Source updated"},
        400: {"description": "Invalid input"},
        404: {"description": "Source not found"}
    }
})
def update_source(source_id):
    try:
        UUID(source_id)
    except ValueError:
        return jsonify({"error": "Invalid source_id"}), 400

    source = Source.query.filter_by(id=source_id).first()
    if not source:
        return jsonify({"error": "Source not found"}), 404

    try:
        data = SourceUpdate(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    for key, value in data.dict(exclude_unset=True).items():
        setattr(source, key, value)
    db.session.commit()

    return jsonify({
        "id": str(source.id),
        "url": source.url,
        "link_selector": source.link_selector,
        "status": source.status,
        "threads": source.threads,
        "description": source.description,
        "card_information": source.card_information
    }), 200

@sources_bp.route("/sources/<source_id>", methods=["DELETE"])
@swag_from({
    "tags": ["Sources"],
    "parameters": [
        {
            "name": "source_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "UUID of the source"
        }
    ],
    "responses": {
        204: {"description": "Source deleted"},
        400: {"description": "Invalid source_id"},
        404: {"description": "Source not found"}
    }
})
def delete_source(source_id):
    try:
        UUID(source_id)
    except ValueError:
        return jsonify({"error": "Invalid source_id"}), 400

    source = Source.query.filter_by(id=source_id).first()
    if not source:
        return jsonify({"error": "Source not found"}), 404

    db.session.delete(source)
    db.session.commit()
    return "", 204