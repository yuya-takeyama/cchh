"""HTTP server for handling approval requests."""

import asyncio
import json
from typing import Any, Dict, Optional

from aiohttp import web

from .slack_integration import SlackIntegration


class ApprovalServer:
    """HTTP server for remote approval."""

    def __init__(self, port: int = 8080, timeout_seconds: int = 300):
        """Initialize approval server.

        Args:
            port: Port to listen on
            timeout_seconds: Timeout for approval requests (default: 5 minutes)
        """
        self.port = port
        self.timeout_seconds = timeout_seconds
        self.pending_approvals: Dict[str, asyncio.Future] = {}
        self.approval_details: Dict[str, dict] = {}
        self.session_mapping: Dict[str, str] = {}  # request_id -> session_id
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.slack = SlackIntegration()

    async def create_approval_request(
        self, request_id: str, details: dict, session_id: str = ""
    ) -> dict[str, Any]:
        """Create approval request and wait for response.

        Args:
            request_id: Unique request ID
            details: Request details (tool_name, input, etc.)
            session_id: Claude session ID

        Returns:
            Dict with behavior: "allow" or "deny"
        """
        # Create future for this request
        future = asyncio.Future()
        self.pending_approvals[request_id] = future
        self.approval_details[request_id] = details
        if session_id:
            self.session_mapping[request_id] = session_id

        # Set up timeout
        asyncio.create_task(self._timeout_handler(request_id))

        # Wait for approval or timeout
        try:
            result = await future
            return result
        finally:
            # Clean up
            self.pending_approvals.pop(request_id, None)
            self.approval_details.pop(request_id, None)
            self.session_mapping.pop(request_id, None)

    async def _timeout_handler(self, request_id: str):
        """Handle timeout for approval request."""
        await asyncio.sleep(self.timeout_seconds)
        if request_id in self.pending_approvals:
            future = self.pending_approvals[request_id]
            if not future.done():
                # Timeout - auto deny
                future.set_result({"behavior": "deny", "message": "Request timed out after 5 minutes"})
                
                # Send Slack notification for timeout
                session_id = self.session_mapping.get(request_id)
                if session_id and self.slack.is_configured:
                    asyncio.create_task(
                        asyncio.to_thread(
                            self.slack.send_approval_result,
                            session_id,
                            request_id,
                            "denied (timeout)",
                        )
                    )

    async def handle_pending(self, request: web.Request) -> web.Response:
        """Handle GET /pending - list pending approval requests."""
        pending_list = []
        for request_id, details in self.approval_details.items():
            pending_list.append(
                {
                    "request_id": request_id,
                    "tool_name": details.get("tool_name"),
                    "input": details.get("input"),
                    "tool_use_id": details.get("tool_use_id"),
                }
            )
        return web.json_response({"pending": pending_list})

    async def handle_approve(self, request: web.Request) -> web.Response:
        """Handle POST /approve - approve a request."""
        try:
            data = await request.json()
            request_id = data.get("request_id")

            if not request_id:
                return web.json_response(
                    {"error": "Missing request_id"}, status=400
                )

            if request_id not in self.pending_approvals:
                return web.json_response(
                    {"error": "Request not found or already processed"}, status=404
                )

            future = self.pending_approvals[request_id]
            if not future.done():
                # Get the original input from approval details
                details = self.approval_details.get(request_id, {})
                input_data = details.get("input", {})
                future.set_result({"behavior": "allow", "updatedInput": input_data})

            # Send Slack notification
            session_id = self.session_mapping.get(request_id)
            if session_id and self.slack.is_configured:
                asyncio.create_task(
                    asyncio.to_thread(
                        self.slack.send_approval_result,
                        session_id,
                        request_id,
                        "approved",
                    )
                )

            return web.json_response({"status": "approved"})

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_deny(self, request: web.Request) -> web.Response:
        """Handle POST /deny - deny a request."""
        try:
            data = await request.json()
            request_id = data.get("request_id")

            if not request_id:
                return web.json_response(
                    {"error": "Missing request_id"}, status=400
                )

            if request_id not in self.pending_approvals:
                return web.json_response(
                    {"error": "Request not found or already processed"}, status=404
                )

            future = self.pending_approvals[request_id]
            if not future.done():
                future.set_result({"behavior": "deny", "message": "Request denied by user"})

            # Send Slack notification
            session_id = self.session_mapping.get(request_id)
            if session_id and self.slack.is_configured:
                asyncio.create_task(
                    asyncio.to_thread(
                        self.slack.send_approval_result,
                        session_id,
                        request_id,
                        "denied",
                    )
                )

            return web.json_response({"status": "denied"})

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def start(self):
        """Start the HTTP server."""
        self.app = web.Application()
        self.app.router.add_get("/pending", self.handle_pending)
        self.app.router.add_post("/approve", self.handle_approve)
        self.app.router.add_post("/deny", self.handle_deny)

        # Add health check endpoint
        self.app.router.add_get(
            "/health", lambda _: web.json_response({"status": "ok"})
        )

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "localhost", self.port)
        await site.start()

    async def stop(self):
        """Stop the HTTP server."""
        if self.runner:
            await self.runner.cleanup()