from flask import Blueprint, render_template, request, redirect, url_for
from app.models.attributes import Attribute
from app.models.sources import Source
from app import db
from uuid import UUID

web_bp = Blueprint('web', __name__, template_folder='../templates')

# Routes cho attributes
@web_bp.route('/attributes', methods=['GET'])
def list_attributes():
    attributes = Attribute.query.all()
    return render_template('attributes.html', attributes=attributes)

@web_bp.route('/attributes/add', methods=['GET', 'POST'])
def add_attribute():
    if request.method == 'POST':
        keyword = request.form['keyword']
        source_id = request.form['source_id']
        is_active = 'is_active' in request.form
        try:
            UUID(source_id)  # Validate source_id là UUID
        except ValueError:
            return "Invalid Source ID", 400
        new_attribute = Attribute(keyword=keyword, source_id=source_id, is_active=is_active)
        db.session.add(new_attribute)
        db.session.commit()
        return redirect(url_for('web.list_attributes'))
    return render_template('add_attribute.html')

@web_bp.route('/attributes/edit/<id>', methods=['GET', 'POST'])
def edit_attribute(id):
    attribute = Attribute.query.get_or_404(id)
    if request.method == 'POST':
        attribute.keyword = request.form['keyword']
        attribute.source_id = request.form['source_id']
        attribute.is_active = 'is_active' in request.form
        try:
            UUID(attribute.source_id)  # Validate source_id là UUID
        except ValueError:
            return "Invalid Source ID", 400
        db.session.commit()
        return redirect(url_for('web.list_attributes'))
    return render_template('edit_attribute.html', attribute=attribute)

@web_bp.route('/attributes/delete/<id>', methods=['GET'])
def delete_attribute(id):
    attribute = Attribute.query.get_or_404(id)
    db.session.delete(attribute)
    db.session.commit()
    return redirect(url_for('web.list_attributes'))

# Routes cho sources
@web_bp.route('/sources', methods=['GET'])
def list_sources():
    sources = Source.query.all()
    return render_template('sources.html', sources=sources)

@web_bp.route('/sources/add', methods=['GET', 'POST'])
def add_source():
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        description = request.form['description']
        selectors = request.form['selectors']
        is_active = 'is_active' in request.form
        new_source = Source(name=name, url=url, description=description, selectors=selectors, is_active=is_active)
        db.session.add(new_source)
        db.session.commit()
        return redirect(url_for('web.list_sources'))
    return render_template('add_source.html')

@web_bp.route('/sources/edit/<id>', methods=['GET', 'POST'])
def edit_source(id):
    source = Source.query.get_or_404(id)
    if request.method == 'POST':
        source.name = request.form['name']
        source.url = request.form['url']
        source.description = request.form['description']
        source.selectors = request.form['selectors']
        source.is_active = 'is_active' in request.form
        db.session.commit()
        return redirect(url_for('web.list_sources'))
    return render_template('edit_source.html', source=source)

@web_bp.route('/sources/delete/<id>', methods=['GET'])
def delete_source(id):
    source = Source.query.get_or_404(id)
    db.session.delete(source)
    db.session.commit()
    return redirect(url_for('web.list_sources'))