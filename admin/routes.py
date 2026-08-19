import json
from datetime import datetime, timezone
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from i18n import translate
from werkzeug.security import check_password_hash

from .auth import csrf_token, current_admin, login_required, validate_csrf
from security import client_ip, enforce_admin_login_rate_limit
from .forms import missing_article_fields, missing_tool_fields, parse_json_payload
from .services import safe_next_url, validate_import_payload
from repositories.admin import (
    get_dashboard_overview, get_admin_by_username, get_recent_audit_logs, get_traffic_overview, log_action,
    recent_failed_attempts, record_login_attempt,
)
from repositories.collaborations import list_inquiries, set_inquiry_status
from repositories.users import list_users, set_user_active, set_user_identity_badges, user_account_counts
from repositories.article_writer import get_article_for_admin, list_admin_articles, save_article
from repositories.taxonomy_writer import add_category, add_tag, list_taxonomies
from repositories.tool_writer import archive_tool, get_tool_for_admin, list_admin_tools, save_tool
from services.rating_service import evaluate_rating
from services.image_service import enrich_tool_branding
from validators.image_validator import validate_tool_branding

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
        username = request.form.get("username", "").strip()[:120]
        password = request.form.get("password", "")[:512]
        enforce_admin_login_rate_limit(username)
        ip_address = client_ip()
        if recent_failed_attempts(username) >= 5:
            flash(translate("flash.too_many_attempts"), "error")
            return render_template("admin/login.html"), 429
        admin = get_admin_by_username(username)
        valid = bool(admin and check_password_hash(admin["password_hash"], password))
        record_login_attempt(username, ip_address, valid)
        if valid:
            session.clear()
            session["admin_user_id"] = admin["id"]
            session["last_admin_activity"] = int(datetime.now(timezone.utc).timestamp())
            session.permanent = True
            log_action(admin["id"], "login", "admin", admin["id"], "Administrator signed in")
            return redirect(safe_next_url(request.args.get("next")) or url_for("admin.dashboard"))
        current_app.logger.warning("admin_login_failed username=%r ip=%s", username, ip_address)
        flash(translate("flash.invalid_login"), "error")
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
    overview = get_dashboard_overview()
    return render_template(
        "admin/dashboard.html", logs=get_recent_audit_logs(8), traffic=get_traffic_overview(), active_admin="dashboard", **overview
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
        return (translate("flash.tool_not_found"), 404)
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
            parsed["is_featured"] = request.form.get("is_featured") == "1"
            parsed["is_sponsored"] = request.form.get("is_sponsored") == "1"
            parsed["featured_until"] = request.form.get("featured_until", "").strip() or None
            parsed["sponsor_plan"] = request.form.get("sponsor_plan", "").strip()[:80] or None
            parsed["affiliate_url"] = request.form.get("affiliate_url", "").strip()[:500] or None
            affiliate = urlsplit(parsed["affiliate_url"]) if parsed["affiliate_url"] else None
            if affiliate and (affiliate.scheme not in {"http", "https"} or not affiliate.netloc):
                flash("Affiliate URL must use http:// or https://.", "error")
                payload = parsed
                return render_template("admin/tool_form.html", record=record, payload_json=json.dumps(payload, ensure_ascii=False, indent=2), monetization=payload, status=status, missing=missing_tool_fields(payload), active_admin="tools"), 400
            if parsed["featured_until"]:
                try:
                    datetime.fromisoformat(parsed["featured_until"])
                except ValueError:
                    flash("Featured Until must be a valid date.", "error")
                    payload = parsed
                    return render_template("admin/tool_form.html", record=record, payload_json=json.dumps(payload, ensure_ascii=False, indent=2), monetization=payload, status=status, missing=missing_tool_fields(payload), active_admin="tools"), 400
            missing = missing_tool_fields(parsed)
            if status == "published" and missing:
                flash(translate("flash.cannot_publish", fields=", ".join(missing)), "error")
            else:
                before = record["payload"] if record else None
                saved_id = save_tool(parsed, status=status, tool_id=tool_id)
                admin = current_admin()
                log_action(admin["id"], "update" if tool_id else "create", "tool", saved_id,
                           f"{status.title()} tool {parsed.get('name')}", before, parsed)
                flash(translate("flash.tool_saved"), "success")
                return redirect(url_for("admin.tool_form", tool_id=saved_id))
        payload = parsed or payload
    return render_template(
        "admin/tool_form.html", record=record, payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
        status=(record["status"] if record else "draft"), monetization=payload, missing=missing_tool_fields(payload), active_admin="tools"
    )


@admin_bp.post("/tools/<int:tool_id>/archive")
@login_required
def tool_archive(tool_id):
    validate_csrf()
    record = get_tool_for_admin(tool_id)
    if not record:
        return (translate("flash.tool_not_found"), 404)
    archive_tool(tool_id)
    admin = current_admin()
    log_action(admin["id"], "archive", "tool", tool_id, f"Archived {record['name']}", record["payload"], None)
    flash(translate("flash.tool_archived"), "success")
    return redirect(url_for("admin.tools"))


@admin_bp.route("/tools/<int:tool_id>/preview")
@login_required
def tool_preview(tool_id):
    record = get_tool_for_admin(tool_id)
    if not record:
        return (translate("flash.tool_not_found"), 404)
    return render_template("admin/preview.html", title=record["name"], payload=record["payload"], entity_type="Tool")


@admin_bp.route("/ratings")
@login_required
def ratings():
    rows = []
    for item in list_admin_tools():
        record = get_tool_for_admin(item["id"])
        rating = (record["payload"].get("rating_v103") or {}) if record else {}
        result = evaluate_rating(rating, record["payload"].get("category", "")) if rating else None
        rows.append({"id": item["id"], "name": item["name"], "slug": item["slug"], "status": rating.get("status", "unreviewed"), "score": result.overall_score if result else None, "coverage": round((result.coverage if result else 0) * 100, 1), "confidence": result.confidence_level if result else "insufficient"})
    counts = {"published": sum(1 for row in rows if row["score"] is not None), "pending": sum(1 for row in rows if row["score"] is None), "low_confidence": sum(1 for row in rows if row["confidence"] in {"low", "insufficient"})}
    return render_template("admin/ratings.html", ratings=rows, counts=counts, active_admin="ratings")


@admin_bp.route("/ratings/<int:tool_id>", methods=["GET", "POST"])
@login_required
def rating_form(tool_id):
    record = get_tool_for_admin(tool_id)
    if not record:
        return (translate("flash.tool_not_found"), 404)
    rating = record["payload"].get("rating_v103") or {}
    if request.method == "POST":
        validate_csrf()
        parsed, error = parse_json_payload(request.form.get("rating_json"))
        if error:
            flash(error, "error")
        elif not isinstance(parsed, dict):
            flash(translate("rating.invalid_payload"), "error")
        else:
            admin = current_admin()
            parsed.pop("overall_score", None)
            parsed.pop("calculated_score", None)
            parsed["reviewed_by"] = admin["id"]
            approved_raw = request.form.get("approved_by", "").strip()
            parsed["approved_by"] = int(approved_raw) if approved_raw.isdigit() else None
            result = evaluate_rating(parsed, record["payload"].get("category", ""))
            parsed["confidence_score"] = result.confidence_score
            parsed["confidence_level"] = result.confidence_level
            parsed["overall_score"] = result.overall_score
            parsed["status"] = "published" if result.publishable else "editor_review"
            payload = dict(record["payload"]); before = payload.get("rating_v103")
            payload["rating_v103"] = parsed
            payload["rating"] = result.overall_score / 2 if result.overall_score is not None else 0
            payload["rating_source"] = "atlasfind_v103" if result.publishable else "not-rated"
            save_tool(payload, status=record["status"], tool_id=tool_id)
            log_action(admin["id"], "rating_update", "tool", tool_id, f"Rating workflow updated for {record['name']}", before, parsed)
            if result.publishable:
                flash(translate("rating.saved_published"), "success")
            else:
                flash(translate("rating.saved_with_errors", errors="; ".join(result.errors) or translate("rating.not_approved")), "error")
            return redirect(url_for("admin.rating_form", tool_id=tool_id))
        rating = parsed or rating
    result = evaluate_rating(rating, record["payload"].get("category", "")) if rating else None
    return render_template("admin/rating_form.html", record=record, rating_json=json.dumps(rating, ensure_ascii=False, indent=2), result=result, active_admin="ratings")


@admin_bp.route("/images")
@login_required
def images():
    rows = []
    counts = {"verified": 0, "missing": 0, "pending": 0, "broken": 0, "fallback": 0}
    for item in list_admin_tools():
        record = get_tool_for_admin(item["id"])
        if not record:
            continue
        payload = enrich_tool_branding(record["payload"])
        branding = payload.get("branding") or {}
        logo = branding.get("logo") or {}
        status = logo.get("status", "missing")
        validation = validate_tool_branding(payload)
        if status in counts:
            counts[status] += 1
        if payload.get("image_is_fallback"):
            counts["fallback"] += 1
        rows.append({
            "id": item["id"], "name": item["name"], "slug": item["slug"],
            "status": status, "icon_url": payload.get("icon_url"),
            "source_type": logo.get("source_type") or "—",
            "resolution": f"{logo.get('width')}×{logo.get('height')}" if logo.get("width") and logo.get("height") else "—",
            "verified_at": logo.get("verified_at") or "—",
            "warnings": len(validation.warnings), "errors": len(validation.errors),
        })
    return render_template("admin/images.html", images=rows, counts=counts, active_admin="images")


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
        return (translate("flash.article_not_found"), 404)
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
                flash(translate("flash.cannot_publish", fields=", ".join(missing)), "error")
            else:
                before = record["payload"] if record else None
                saved_id = save_article(parsed, status=status, article_id=article_id)
                admin = current_admin()
                log_action(admin["id"], "update" if article_id else "create", "article", saved_id,
                           f"{status.title()} article {parsed.get('title')}", before, parsed)
                flash(translate("flash.article_saved"), "success")
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
            flash(translate("flash.taxonomy_saved", kind=kind.title()), "success")
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
            flash(translate("flash.invalid_json", error=exc), "error")
            value = None
        if value is not None:
            tools, errors = validate_import_payload(value)
            if errors:
                flash(translate("flash.import_failed", errors=" | ".join(errors[:8])), "error")
            elif request.form.get("confirm") == "1":
                ids = [save_tool(tool, status="draft") for tool in tools]
                admin = current_admin()
                log_action(admin["id"], "import", "tool", None, f"Imported {len(ids)} tools as drafts")
                flash(translate("flash.imported_drafts", count=len(ids)), "success")
                return redirect(url_for("admin.tools"))
            else:
                preview = tools
    return render_template("admin/import.html", preview=preview, active_admin="import")


@admin_bp.route("/audit")
@login_required
def audit():
    return render_template("admin/audit_log.html", logs=get_recent_audit_logs(200), active_admin="audit")


@admin_bp.route("/collaborations", methods=["GET", "POST"])
@login_required
def collaborations():
    if request.method == "POST":
        validate_csrf()
        inquiry_id = request.form.get("inquiry_id", "")
        status = request.form.get("status", "")
        if inquiry_id.isdigit() and set_inquiry_status(int(inquiry_id), status):
            admin = current_admin()
            log_action(admin["id"], "update", "collaboration", inquiry_id, f"Collaboration marked {status}")
            flash("İş birliği talebi güncellendi.", "success")
        return redirect(url_for("admin.collaborations"))
    return render_template("admin/collaborations.html", inquiries=list_inquiries(), active_admin="collaborations")


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if request.method == "POST":
        validate_csrf()
        user_id = request.form.get("user_id", "")
        action = request.form.get("action", "")
        if user_id.isdigit() and action in {"disable", "enable"} and set_user_active(int(user_id), action == "enable"):
            admin = current_admin()
            log_action(admin["id"], action, "user", user_id, f"User account {action}d")
            flash("Kullanıcı hesabı güncellendi.", "success")
        elif user_id.isdigit() and action == "identity":
            custom_rank = request.form.get("custom_rank", "").strip()[:40]
            staff_badge = request.form.get("staff_badge", "").strip()[:40]
            if set_user_identity_badges(int(user_id), custom_rank, staff_badge):
                admin = current_admin()
                log_action(admin["id"], "update_identity", "user", user_id, "User rank and staff badge updated")
                flash("Kullanıcı rütbesi ve rozeti güncellendi.", "success")
        return redirect(url_for("admin.users", q=request.form.get("q", ""), status=request.form.get("status", "all")))
    search = request.args.get("q", "").strip()[:120]
    status = request.args.get("status", "all")
    if status not in {"all", "verified", "unverified", "disabled"}:
        status = "all"
    return render_template("admin/users.html", users=list_users(search, status), counts=user_account_counts(), search=search, status=status, active_admin="users")
