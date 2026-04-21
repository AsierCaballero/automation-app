"""Webhook notification service."""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("webhook")


class WebhookService:
    """Handle webhook notifications."""

    def __init__(self) -> None:
        self.enabled = settings.enable_webhooks

    def generate_signature(self, payload: str, secret: Optional[str]) -> Optional[str]:
        """Generate HMAC signature for webhook payload."""
        if not secret:
            return None
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    async def send(
        self,
        url: str,
        event: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        secret: Optional[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: int = 5,
    ) -> Dict[str, Any]:
        """Send webhook notification."""
        if not self.enabled:
            return {"success": False, "error": "Webhooks disabled"}

        payload = json.dumps({
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        })

        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Automation-App/1.0",
        }

        if secret:
            signature = self.generate_signature(payload, secret)
            if signature:
                default_headers["X-Webhook-Signature"] = signature

        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient() as client:
            for attempt in range(1, retry_attempts + 1):
                try:
                    response = await client.post(
                        url,
                        content=payload,
                        headers=default_headers,
                        timeout=timeout,
                    )

                    result = {
                        "success": 200 <= response.status_code < 300,
                        "status_code": response.status_code,
                        "response": response.text[:500] if response.text else None,
                        "attempt": attempt,
                    }

                    if result["success"]:
                        logger.info(f"Webhook sent successfully to {url}")
                        return result
                    else:
                        logger.warning(
                            f"Webhook attempt {attempt}/{retry_attempts} failed: "
                            f"{response.status_code}"
                        )

                except Exception as e:
                    logger.error(f"Webhook attempt {attempt}/{retry_attempts} error: {str(e)}")
                    if attempt < retry_attempts:
                        import asyncio
                        await asyncio.sleep(retry_delay)

            return {
                "success": False,
                "error": f"Failed after {retry_attempts} attempts",
                "attempt": retry_attempts,
            }

    async def notify_task_success(
        self,
        webhook_url: str,
        task_name: str,
        output: Optional[str],
        duration_ms: Optional[int],
        triggered_by: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send task success notification."""
        return await self.send(
            url=webhook_url,
            event="task.success",
            data={
                "task_name": task_name,
                "status": "success",
                "output": output,
                "duration_ms": duration_ms,
                "triggered_by": triggered_by,
            },
            headers=headers,
            secret=secret,
        )

    async def notify_task_failure(
        self,
        webhook_url: str,
        task_name: str,
        error: str,
        duration_ms: Optional[int] = None,
        triggered_by: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send task failure notification."""
        return await self.send(
            url=webhook_url,
            event="task.failed",
            data={
                "task_name": task_name,
                "status": "failed",
                "error": error,
                "duration_ms": duration_ms,
                "triggered_by": triggered_by,
            },
            headers=headers,
            secret=secret,
        )


webhook_service = WebhookService()