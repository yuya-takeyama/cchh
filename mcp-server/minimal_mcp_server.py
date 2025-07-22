#!/usr/bin/env python3
"""
最小限のMCPサーバー実装
全てのリクエストを自動承認する検証用実装
"""

import json
import logging
import os
import sys
from typing import Any

# ログ設定
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.log")

# ファイルとコンソール両方にログを出力
file_handler = logging.FileHandler(log_path)
console_handler = logging.StreamHandler(sys.stderr)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[file_handler, console_handler]
)


class MinimalMCPServer:
    """最小限のMCPサーバー実装"""

    def __init__(self):
        self.server_info = {
            "name": "minimal-mcp-server",
            "version": "0.1.0",
            "capabilities": {"tools": {"supported": True, "permissions": True}},
        }
        logging.info("MCP Server initialized")

    def read_message(self) -> dict[str, Any] | None:
        """標準入力からJSON-RPCメッセージを読み取る"""
        try:
            line = sys.stdin.readline()
            if not line:
                return None

            message = json.loads(line.strip())
            logging.debug(f"Received message: {message}")
            return message
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading message: {e}")
            return None

    def send_message(self, message: dict[str, Any]):
        """標準出力にJSON-RPCメッセージを送信"""
        try:
            json_str = json.dumps(message)
            sys.stdout.write(json_str + "\n")
            sys.stdout.flush()
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def handle_initialize(self, request_id: Any) -> dict[str, Any]:
        """初期化リクエストを処理"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "serverInfo": self.server_info,
                "capabilities": self.server_info["capabilities"],
            },
        }

    def handle_permission_request(
        self, request_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        """権限リクエストを処理（全て承認）"""
        logging.info(f"Permission request: {params}")

        # Custom Permission Prompt Tool のレスポンス形式
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "behavior": "allow",  # 常に承認
                "message": "Auto-approved by minimal MCP server",
            },
        }

    def handle_request(self, message: dict[str, Any]):
        """JSON-RPCリクエストを処理"""
        if "method" not in message:
            logging.error("No method in message")
            return

        method = message["method"]
        request_id = message.get("id")
        params = message.get("params", {})

        logging.info(f"Handling method: {method}")

        # メソッドに応じた処理
        if method == "initialize":
            response = self.handle_initialize(request_id)
        elif method == "tools/permission" or method == "permission":
            response = self.handle_permission_request(request_id, params)
        else:
            # 未知のメソッド
            logging.warning(f"Unknown method: {method}")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "Method not found"},
            }

        if request_id is not None:
            self.send_message(response)

    def run(self):
        """サーバーのメインループ"""
        logging.info("MCP Server starting...")

        while True:
            message = self.read_message()
            if message is None:
                logging.info("No more messages, shutting down")
                break

            try:
                self.handle_request(message)
            except Exception as e:
                logging.error(f"Error handling request: {e}")
                # エラーレスポンスを送信
                if "id" in message:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": str(e),
                        },
                    }
                    self.send_message(error_response)


def main():
    """メインエントリーポイント"""
    server = MinimalMCPServer()
    try:
        server.run()
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
