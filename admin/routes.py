import json
from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .auth import csrf_token, current_admin, login_required, validate_csrf
from .forms import missing_article_fields, missing_tool_fields, parse_json_payload
from .services import safe_next_url, validate_import_payload
from repositories.admin import (
    dashboard_counts, get_admin_by_username, get_recent_audit_logs, log_action,
    recent_failed_attempts, record_login_attempt,
)
from repositories.article_writer import get_article_for_admin, list_admin_articles, save_article
from repositories.taxonomy_writer import add_category, add_tag, list_taxonomies
from repositories.tool_writer import archive_tool, get_tool_for_admin, list_admin_tools, save_tool

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates")


@admin_bp.app_context_processor
def admin_context():
    return {"admin_user": current_admin(), "csrf_token": csrf_token}


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_admin():
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr or "")[:120]
        if recent_failed_attempts(username) >= 5:
            flash("Too many failed attempts. Try again in 15 minutes.", "error")
            return render_template("admin/login.html"), 429
        admin = get_admin_by_username(username)
        valid = bool(admin and check_password_hash(admin["password_hash"], password))
        record_login_attempt(username, ip_address, valid)
        if valid:
            session.clear()
            session["admin_user_id"] = admin["id"]
            session.permanent = True
            log_action(admin["id"], "login", "admin", admin["id"], "Administrator signed in")
            return redirect(safe_next_url(request.args.get("next")) or url_for("admin.dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html")


@admin_bp.post("/logout")
@login_required
def logout():
    validate_csrf()
    admin = current_admin()
    if admin:
        log_action(admin["id"], "logout", "admin", admin["id"], "Administrator signed out")
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("")
@login_required
def dashboard():
    return render_template(
        "admin/dashboard.html", counts=dashboard_counts(), logs=get_recent_audit_logs(12), active_admin="dashboard"
    )


@admin_bp.route("/tools")
@login_required
def tools():
    return render_template("admin/tools.html", tools=list_admin_tools(), active_admin="tools")


@admin_bp.route("/tools/new", methods=["GET", "POST"])
@admin_bp.route("/tools/<int:tool_id>/edit", methods=["GET", "POST"])
@login_required
def tool_form(tool_id=None):
    record = get_tool_for_admin(tool_id) if tool_id else None
    if tool_id and not record:
        return ("Tool not found", 404)
    payload = record["payload"] if record else {
        "name": "", "slug": "", "description": "", "category": "Uncategorized",
        "pricing_type": "free", "platforms": ["web"], "languages": ["en"],
        "tags": [], "collections": [], "pros": [], "cons": [], "target_users": [],
    }
    if request.method == "POST":
        validate_csrf()
        parsed, error = parse_json_payload(request.form.get("payload_json"))
        status = request.form.get("status", "draft")
        if error:
            flash(error, "error")
        else:
            missing = missing_tool_fields(parsed)
            if status == "published" and missing:
                flash("Cannot publish. Missing: " + ", ".join(missing), "error")
            else:
                before = record["payload"] if record else None
                saved_id = save_tool(parsed, status=status, tool_id=tool_id)
                admin = current_admin()
                log_action(admin["id"], "update" if tool_id else "create", "tool", saved_id,
                           f"{status.title()} tool {parsed.get('name')}", before, parsed)
                flash("Tool saved.", "success")
                return redirect(url_for("admin.tool_form", tool_id=saved_id))
        payload = parsed or payload
    return render_template(
        "admin/tool_form.html", record=record, payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
        status=(record["status"] if record else "draft"), missing=missing_tool_fields(payload), active_admin="tools"
    )


@admin_bp.post("/tools/<int:tool_id>/archive")
@login_required
def tool_archive(tool_id):
    validate_csrf()
    record = get_tool_for_admin(tool_id)
    if not record:
        return ("Tool not found", 404)
    archive_tool(tool_id)
    admin = current_admin()
    log_action(admin["id"], "archive", "tool", tool_id, f"Archived {record['name']}", record["payload"], None)
    flash("Tool archived.", "success")
    return redirect(url_for("admin.tools"))


@admin_bp.route("/tools/<int:tool_id>/preview")
@login_required
def tool_preview(tool_id):
    record = get_tool_for_admin(tool_id)
    if not record:
        return ("Tool not found", 404)
    return render_template("admin/preview.html", title=record["name"], payload=record["payload"], entity_type="Tool")


@admin_bp.route("/articles")
@login_required
def articles():
    return render_template("admin/articles.html", articles=list_admin_articles(), active_admin="articles")


@admin_bp.route("/articles/new", methods=["GET", "POST"])
@admin_bp.route("/articles/<int:article_id>/edit", methods=["GET", "POST"])
@login_required
def article_form(article_id=None):
    record = get_article_for_admin(article_id) if article_id else None
    if article_id and not record:
        return ("Article not found", 404)
    payload = record["payload"] if record else {
        "title": "", "slug": "", "description": "", "content_type": "guide",
        "category": "uncategorized", "author": "AtlasFind Editors", "sections": [], "faq": [],
        "related_tool_slugs": [], "related_article_slugs": [],
    }
    if request.method == "POST":
        validate_csrf()
        parsed, error = parse_json_payload(request.form.get("payload_json"))
        status = request.form.get("status", "draft")
        if error:
            flash(error, "error")
        else:
            missing = missing_article_fields(parsed)
            if status == "published" and missing:
                flash("Cannot publish. Missing: " + ", ".join(missing), "error")
            else:
                before = record["payload"] if record else None
                saved_id = save_article(parsed, status=status, article_id=article_id)
                admin = current_admin()
                log_action(admin["id"], "update" if article_id else "create", "article", saved_id,
                           f"{status.title()} article {parsed.get('title')}", before, parsed)
                flash("Article saved.", "success")
                return redirect(url_for("admin.article_form", article_id=saved_id))
        payload = parsed or payload
    return render_template(
        "admin/article_form.html", record=record, payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
        status=(record["status"] if record else "draft"), missing=missing_article_fields(payload), active_admin="articles"
    )


@admin_bp.route("/taxonomy", methods=["GET", "POST"])
@login_required
def taxonomy():
    if request.method == "POST":
        validate_csrf()
        kind = request.form.get("kind")
        name = request.form.get("name", "").strip()
        if name:
            add_category(name) if kind == "category" else add_tag(name)
            admin = current_admin()
            log_action(admin["id"], "create", kind, name, f"Created {kind}: {name}")
            flash(f"{kind.title()} saved.", "success")
    categories, tags = list_taxonomies()
    return render_template("admin/taxonomy.html", categories=categories, tags=tags, active_admin="taxonomy")


@admin_bp.route("/import", methods=["GET", "POST"])
@login_required
def import_tools():
    preview = None
    if request.method == "POST":
        validate_csrf()
        raw = request.form.get("payload_json", "")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            flash(f"Invalid JSON: {exc}", "error")
            value = None
        if value is not None:
            tools, errors = validate_import_payload(value)
            if errors:
                flash("Import validation failed: " + " | ".join(errors[:8]), "error")
            elif request.form.get("confirm") == "1":
                ids = [save_tool(tool, status="draft") for tool in tools]
                admin = current_admin()
                log_action(admin["id"], "import", "tool", None, f"Imported {len(ids)} tools as drafts")
                flash(f"Imported {len(ids)} tools as drafts.", "success")
                return redirect(url_for("admin.tools"))
            else:
                preview = tools
    return render_template("admin/import.html", preview=preview, active_admin="import")


@admin_bp.route("/audit")
@login_required
def audit():
    return render_template("admin/audit_log.html", logs=get_recent_audit_logs(200), active_admin="audit")
