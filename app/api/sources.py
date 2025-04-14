import json
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.sources import Source
from app.models.attributes import Attribute
from app.schemas.sources import SourceCreate, SourceUpdate, SourceOut
from app import db
from pydantic import ValidationError
from uuid import UUID
from urllib.parse import urlparse

sources_bp = Blueprint("sources", __name__)

def validate_url(url):
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def prepare_source_for_output(source):
    """Chuyển đổi selectors từ chuỗi JSON thành dictionary"""
    source_dict = {
        'id': str(source.id),
        'name': source.name,
        'url': source.url,
        'description': source.description,
        'selectors': json.loads(source.selectors),  # Parse chuỗi JSON
        'is_active': source.is_active
    }
    return source_dict

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
                    "name": {"type": "string", "example": "Test Source"},
                    "url": {"type": "string", "example": "https://example.com"},
                    "description": {"type": "string", "example": "A test source"},
                    "selectors": {
                        "type": "object",
                        "example": {"title": "h1", "price": ".price"}
                    },
                    "is_active": {"type": "boolean", "example": True}
                },
                "required": ["name", "url", "selectors"]
            }
        }
    ],
    "responses": {
        201: {"description": "Source created", "schema": SourceOut.schema()},
        400: {"description": "Invalid input"}
    }
})
def create_source():
    """Create a new source"""
    try:
        data = SourceCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    # Validate URL
    if not validate_url(data.url):
        return jsonify({"error": "Invalid URL"}), 400

    # Chuyển selectors thành JSON để lưu
    source_data = data.dict()
    source_data['selectors'] = json.dumps(source_data['selectors'])

    source = Source(**source_data)
    db.session.add(source)
    db.session.commit()

    # Chuẩn bị dữ liệu để trả về
    source_dict = prepare_source_for_output(source)
    return jsonify(SourceOut(**source_dict).dict()), 201

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
        200: {"description": "Source details", "schema": SourceOut.schema()},
        400: {"description": "Invalid source_id"},
        404: {"description": "Source not found"}
    }
})
def get_source(source_id):
    """Get a source by ID"""
    try:
        UUID(source_id)
    except ValueError:
        return jsonify({"error": "Invalid source_id"}), 400

    source = Source.query.filter_by(id=source_id).first()
    if not source:
        return jsonify({"error": "Source not found"}), 404

    # Chuẩn bị dữ liệu để trả về
    source_dict = prepare_source_for_output(source)
    return jsonify(SourceOut(**source_dict).dict()), 200

@sources_bp.route("/sources", methods=["GET"])
@swag_from({
    "tags": ["Sources"],
    "responses": {
        200: {
            "description": "List of sources",
            "schema": {"type": "array", "items": SourceOut.schema()}
        }
    }
})
def list_sources():
    """List all sources"""
    sources = Source.query.all()
    result = []
    for source in sources:
        source_dict = prepare_source_for_output(source)
        result.append(SourceOut(**source_dict).dict())
    return jsonify(result), 200

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
                    "name": {"type": "string", "example": "Updated Source"},
                    "url": {"type": "string", "example": "https://updated.com"},
                    "description": {"type": "string", "example": "Updated description"},
                    "selectors": {
                        "type": "object",
                        "example": {"title": "h1.updated", "price": ".price.updated"}
                    },
                    "is_active": {"type": "boolean", "example": False}
                }
            }
        }
    ],
    "responses": {
        200: {"description": "Source updated", "schema": SourceOut.schema()},
        400: {"description": "Invalid input"},
        404: {"description": "Source not found"}
    }
})
def update_source(source_id):
    """Update a source"""
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

    # Validate URL nếu được cập nhật
    if data.url and not validate_url(data.url):
        return jsonify({"error": "Invalid URL"}), 400

    # Chuyển selectors thành JSON nếu được cập nhật
    update_data = data.dict(exclude_unset=True)
    if 'selectors' in update_data:
        update_data['selectors'] = json.dumps(update_data['selectors'])

    for key, value in update_data.items():
        setattr(source, key, value)

    db.session.commit()

    # Chuẩn bị dữ liệu để trả về
    source_dict = prepare_source_for_output(source)
    return jsonify(SourceOut(**source_dict).dict()), 200

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
        404: {"description": "Source not found"},
        409: {"description": "Cannot delete source with associated attributes"}
    }
})
def delete_source(source_id):
    """Delete a source"""
    try:
        UUID(source_id)
    except ValueError:
        return jsonify({"error": "Invalid source_id"}), 400

    source = Source.query.filter_by(id=source_id).first()
    if not source:
        return jsonify({"error": "Source not found"}), 404

    # Kiểm tra nếu có attributes liên kết
    if Attribute.query.filter_by(source_id=source_id).first():
        return jsonify({"error": "Cannot delete source with associated attributes"}), 409

    db.session.delete(source)
    db.session.commit()
    return "", 204