"""Supabase Storage helper.

Supports uploading a local file to Supabase Storage bucket and returning a URL.

This is intentionally safe:
- never raises for missing config/bucket issues; returns None + error text
- uses server-side env vars from backend config (.env)

Expected env vars (set in backend .env or deployment env):
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_STORAGE_BUCKET (e.g. 'exercise-videos')
- SUPABASE_STORAGE_PREFIX (optional, e.g. 'recordings/')

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import os


@dataclass
class UploadResult:
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


def _get_env(name: str) -> Optional[str]:
    val = os.getenv(name)
    return val if val else None


def upload_file_to_supabase_storage(
    *,
    local_path: str,
    object_name: str,
    content_type: str = "video/mp4",
) -> UploadResult:
    """Upload a file to Supabase Storage.

    Returns:
      UploadResult with either url or error.
    """

    supabase_url = _get_env("SUPABASE_URL")
    service_role_key = _get_env("SUPABASE_SERVICE_ROLE_KEY")
    bucket = _get_env("SUPABASE_STORAGE_BUCKET")
    prefix = _get_env("SUPABASE_STORAGE_PREFIX") or ""

    if not supabase_url or not service_role_key:
        return UploadResult(False, None, "Supabase credentials missing (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY).")
    if not bucket:
        return UploadResult(False, None, "Supabase bucket missing (SUPABASE_STORAGE_BUCKET).")

    try:
        from supabase import create_client

        client = create_client(supabase_url, service_role_key)

        # Ensure object path
        object_path = f"{prefix}{object_name}" if prefix else object_name
        object_path = object_path.lstrip("/")

        with open(local_path, "rb") as f:
            data = f.read()

        # Upload; for public read buckets you can use get_public_url
        # For private buckets, app should generate signed URLs client-side/server-side.
        upload_resp = client.storage.from_(bucket).upload(
            path=object_path,
            file=f"{local_path}",
            file_content=data,
            content_type=content_type,
            upsert=True,
        )

        # The python supabase client varies by version; handle response shape defensively.
        # If upload_resp returns dict with 'data'/'error', use those.
        if isinstance(upload_resp, dict):
            err = upload_resp.get("error")
            if err:
                # some versions store error as dict or string
                return UploadResult(False, None, str(err))

        # Try to return a URL. If bucket is public, this will work.
        public_url = client.storage.from_(bucket).get_public_url(object_path)
        return UploadResult(True, public_url, None)

    except Exception as e:
        return UploadResult(False, None, f"Supabase upload failed: {e}")

