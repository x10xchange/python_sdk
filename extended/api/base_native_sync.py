"""
Base native sync API client for Extended Exchange SDK.

MIRRORS Pacifica's BaseAPIClient architecture exactly.
Uses requests.Session() for native synchronous operation.
"""

import requests
import time
import logging
from typing import Dict, Optional, Any, List
from urllib.parse import urljoin

from extended.auth_sync import SimpleSyncAuth
from extended.config_sync import SimpleSyncConfig

# Simple exception class to avoid async dependencies
class ExtendedAPIError(Exception):
    def __init__(self, status_code: int, message: str, data=None):
        self.status_code = status_code
        self.message = message
        self.data = data
        super().__init__(message)

logger = logging.getLogger(__name__)


class BaseNativeSyncClient:
    """
    Base native sync HTTP client - EXACT MIRROR of Pacifica's BaseAPIClient.

    Uses requests.Session() for native sync HTTP operations,
    eliminating all async/event loop dependencies.
    """

    def __init__(
        self,
        auth: Optional[SimpleSyncAuth] = None,
        config: Optional[SimpleSyncConfig] = None,
        timeout: int = 30
    ):
        """
        Initialize base API client.

        Args:
            auth: SimpleSyncAuth instance with credentials
            config: SimpleSyncConfig configuration
            timeout: Request timeout in seconds
        """
        self.auth = auth
        self.config = config
        self.timeout = timeout

        # Native sync session - SAME AS PACIFICA
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        authenticated: bool = False,
        additional_headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an API request - EXACT COPY of Pacifica's _request method.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            authenticated: Whether request needs authentication
            additional_headers: Additional headers

        Returns:
            API response data

        Raises:
            ExtendedAPIError: On API errors
        """
        # Fix URL construction: ensure proper path joining
        if endpoint.startswith('/'):
            url = self.config.api_base_url + endpoint
        else:
            url = f"{self.config.api_base_url}/{endpoint}"

        headers = {}
        if authenticated and self.auth:
            headers["X-Api-Key"] = self.auth.api_key

        if additional_headers:
            headers.update(additional_headers)

        logger.debug(f"{method} {url} params={params}")

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.timeout
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("msg", response.text)
                except:
                    message = response.text
                raise ExtendedAPIError(response.status_code, message)

            result = response.json()

            # Check for API-level errors in response
            if not result.get("success", True):
                raise ExtendedAPIError(
                    response.status_code,
                    result.get("msg", "Request failed"),
                    result
                )

            return result

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise ExtendedAPIError(500, str(e))

    def get(self, endpoint: str, params: Optional[Dict] = None, authenticated: bool = False) -> Dict:
        """GET request"""
        return self._request("GET", endpoint, params=params, authenticated=authenticated)

    def post(self, endpoint: str, data: Optional[Dict] = None, authenticated: bool = True, headers: Optional[Dict] = None) -> Dict:
        """POST request with optional headers"""
        return self._request("POST", endpoint, data=data, authenticated=authenticated, additional_headers=headers)

    def delete(self, endpoint: str, params: Optional[Dict] = None, authenticated: bool = True) -> Dict:
        """DELETE request"""
        return self._request("DELETE", endpoint, params=params, authenticated=authenticated)

    def patch(self, endpoint: str, data: Optional[Dict] = None, authenticated: bool = True) -> Dict:
        """PATCH request"""
        return self._request("PATCH", endpoint, data=data, authenticated=authenticated)

    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()