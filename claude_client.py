#!/usr/bin/env python3
"""
Claude CLI Client for Time Record Classification
Uses the `claude -p` command for classification - no API key required,
leverages the existing Claude Code session authentication.
"""

import logging
import asyncio
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for classification via the `claude` CLI command"""

    def __init__(self, model: str = None):
        """
        Initialize Claude CLI client.

        Args:
            model: Optional model override (e.g. 'claude-sonnet-4-6').
                   Defaults to whatever the CLI uses by default.
        """
        self.model = model
        logger.info(f"Claude CLI client initialized (model override: {model or 'default'})")

    async def classify(self, prompt: str) -> Optional[str]:
        """
        Send a classification prompt to Claude via the CLI.

        Args:
            prompt: The full classification prompt

        Returns:
            Classification string or None on failure
        """
        try:
            logger.info("Sending classification request via claude CLI")

            cmd = ["claude", "-p", prompt]
            if self.model:
                cmd.extend(["--model", self.model])

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            )

            if result.returncode == 0:
                classification = result.stdout.strip()
                logger.info(f"Claude CLI result: {classification}")
                return classification
            else:
                logger.error(f"Claude CLI exited with code {result.returncode}: {result.stderr.strip()}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Claude CLI request timed out after 60s")
            return None
        except FileNotFoundError:
            logger.error("'claude' command not found. Run this script inside a Claude Code session.")
            return None
        except Exception as e:
            logger.error(f"Claude CLI classification failed: {e}")
            return None

    async def test_connection(self) -> bool:
        """Verify that the claude CLI is reachable."""
        try:
            logger.info("Testing Claude CLI connection...")
            cmd = ["claude", "-p", "Reply with exactly one word: OK"]
            if self.model:
                cmd.extend(["--model", self.model])

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            )

            if result.returncode == 0:
                logger.info(f"Claude CLI connection OK: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Claude CLI test failed: {result.stderr.strip()}")
                return False

        except FileNotFoundError:
            logger.error("'claude' command not found")
            return False
        except Exception as e:
            logger.error(f"Claude CLI test failed: {e}")
            return False
