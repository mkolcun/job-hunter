#!/usr/bin/env python3
"""
Rate Limiting Hook

Prevents overwhelming target websites by enforcing rate limits on web requests.
Tracks request history and implements exponential backoff when limits are reached.
"""
import json
import sys
import time
import os
from pathlib import Path


# Configuration
RATE_LIMIT_FILE = Path.home() / ".claude" / "scraper_rate_limit.json"
MIN_DELAY_SECONDS = 2  # Minimum delay between requests
MAX_REQUESTS_PER_MINUTE = 20  # Maximum requests in a 60-second window
BACKOFF_MULTIPLIER = 2  # Multiplier for exponential backoff


def load_request_history():
    """Load request history from file."""
    if RATE_LIMIT_FILE.exists():
        try:
            with open(RATE_LIMIT_FILE, 'r') as f:
                data = json.load(f)
                return data.get('requests', []), data.get('backoff_until', 0)
        except (json.JSONDecodeError, IOError):
            return [], 0
    return [], 0


def save_request_history(requests, backoff_until=0):
    """Save request history to file."""
    RATE_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RATE_LIMIT_FILE, 'w') as f:
        json.dump({
            'requests': requests,
            'backoff_until': backoff_until,
            'last_updated': time.time()
        }, f)


def check_rate_limit():
    """
    Check if we're exceeding rate limits.

    Returns:
        tuple: (allowed: bool, wait_time: float)
    """
    now = time.time()

    # Load request history and backoff status
    requests, backoff_until = load_request_history()

    # Check if we're in backoff period
    if backoff_until > now:
        wait_time = backoff_until - now
        print(f"⏸️  In backoff period. Waiting {wait_time:.1f} seconds...",
              file=sys.stderr)
        return False, wait_time

    # Remove requests older than 1 minute
    requests = [t for t in requests if now - t < 60]

    # Check if we've hit the rate limit
    if len(requests) >= MAX_REQUESTS_PER_MINUTE:
        oldest = min(requests)
        wait_time = 60 - (now - oldest)
        print(f"⏸️  Rate limit reached ({len(requests)}/{MAX_REQUESTS_PER_MINUTE} requests/min).",
              file=sys.stderr)
        print(f"   Waiting {wait_time:.1f} seconds...", file=sys.stderr)

        # Set backoff period
        backoff_until = now + wait_time
        save_request_history(requests, backoff_until)
        return False, wait_time

    # Check minimum delay since last request
    if requests:
        last_request = max(requests)
        time_since_last = now - last_request

        if time_since_last < MIN_DELAY_SECONDS:
            wait_time = MIN_DELAY_SECONDS - time_since_last
            print(f"⏱️  Enforcing minimum delay: {wait_time:.1f}s", file=sys.stderr)
            time.sleep(wait_time)
            now = time.time()

    # Record this request
    requests.append(now)
    save_request_history(requests)

    return True, 0


def is_web_request(tool_name, tool_input):
    """
    Determine if this is a web scraping request that should be rate limited.

    Args:
        tool_name: Name of the tool being called
        tool_input: Input parameters to the tool

    Returns:
        bool: True if this is a web request
    """
    # Check if it's a WebFetch call
    if tool_name == 'WebFetch':
        return True

    # Check if it's a Bash command with web requests
    if tool_name == 'Bash':
        command = tool_input.get('command', '')

        # Check for common web request commands
        web_commands = ['curl', 'wget', 'http', 'https']
        if any(cmd in command.lower() for cmd in web_commands):
            return True

    return False


# Main execution
if __name__ == "__main__":
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        # Check if this is a web request
        if is_web_request(tool_name, tool_input):
            # Check rate limit
            allowed, wait_time = check_rate_limit()

            if not allowed:
                # Block the request (exit code 2)
                print(f"\n⛔ Request blocked by rate limiter", file=sys.stderr)
                print(f"   Retry after: {wait_time:.1f} seconds\n", file=sys.stderr)
                sys.exit(2)  # Exit code 2 blocks the tool call

            # Request allowed
            print(f"✓ Request allowed (rate: {len(load_request_history()[0])}/{MAX_REQUESTS_PER_MINUTE} req/min)",
                  file=sys.stderr)

        # Allow the request
        sys.exit(0)

    except json.JSONDecodeError as e:
        # On JSON error, allow the request (fail open)
        print(f"⚠️  Rate limiter JSON error: {e}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        # On any error, allow the request (fail open to avoid blocking legitimate requests)
        print(f"⚠️  Rate limiter error: {e}", file=sys.stderr)
        sys.exit(0)
