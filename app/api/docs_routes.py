from __future__ import annotations

from flask import Blueprint, jsonify, request

bp = Blueprint("docs", __name__)


@bp.get("/openapi.json")
def openapi_spec():
    base_url = request.host_url.rstrip("/")
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "AI Visibility Intelligence API",
            "version": "1.0.0",
            "description": "Flask API for profile onboarding, multi-agent query discovery/scoring, and recommendations.",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/api/v1/profiles": {
                "post": {
                    "summary": "Create business profile",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateProfileRequest"}
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "Profile created"},
                        "400": {"description": "Validation error"},
                    },
                }
            },
            "/api/v1/profiles/{profile_uuid}": {
                "get": {
                    "summary": "Get profile with stats",
                    "parameters": [
                        {
                            "name": "profile_uuid",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Profile details"}, "404": {"description": "Not found"}},
                }
            },
            "/api/v1/profiles/{profile_uuid}/run": {
                "post": {
                    "summary": "Run multi-agent pipeline",
                    "parameters": [
                        {
                            "name": "profile_uuid",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Pipeline run completed"}},
                }
            },
            "/api/v1/profiles/{profile_uuid}/queries": {
                "get": {
                    "summary": "List discovered queries",
                    "parameters": [
                        {"name": "profile_uuid", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "min_score", "in": "query", "required": False, "schema": {"type": "number"}},
                        {
                            "name": "status",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["visible", "not_visible"]},
                        },
                        {"name": "page", "in": "query", "required": False, "schema": {"type": "integer", "default": 1}},
                        {
                            "name": "per_page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 20},
                        },
                    ],
                    "responses": {"200": {"description": "Query list"}},
                }
            },
            "/api/v1/profiles/{profile_uuid}/recommendations": {
                "get": {
                    "summary": "List recommendations",
                    "parameters": [
                        {
                            "name": "profile_uuid",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Recommendation list"}},
                }
            },
            "/api/v1/queries/{query_uuid}/recheck": {
                "post": {
                    "summary": "Re-run scoring for one query",
                    "parameters": [
                        {"name": "query_uuid", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "Updated query scoring"}},
                }
            },
        },
        "components": {
            "schemas": {
                "CreateProfileRequest": {
                    "type": "object",
                    "required": ["name", "domain"],
                    "properties": {
                        "name": {"type": "string"},
                        "domain": {"type": "string"},
                        "industry": {"type": "string"},
                        "description": {"type": "string"},
                        "competitors": {"type": "array", "items": {"type": "string"}},
                    },
                }
            }
        },
    }
    return jsonify(spec)


@bp.get("/docs")
def swagger_ui():
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>AI Visibility API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui'
      });
    </script>
  </body>
</html>
"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}

