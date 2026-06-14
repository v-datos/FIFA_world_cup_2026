"""
BigQuery Helper Functions for FIFA Dashboard
Provides utility functions for BigQuery queries and connections
"""

import streamlit as st
import pandas as pd
import google.auth
from google.oauth2 import service_account
from google.cloud import bigquery
from typing import Optional, List, Tuple
import re


# BigQuery Configuration
BIGQUERY_TABLE = "midyear-castle-328020.fifa_data.events"


def execute_query(client: bigquery.Client, query: str, query_params: Optional[List] = None) -> pd.DataFrame:
    """
    Convenience wrapper for run_query that automatically handles params_hash.
    Use this function instead of calling run_query directly.

    Args:
        client: BigQuery client
        query: SQL query string
        query_params: Optional list of BigQuery query parameters

    Returns:
        pandas.DataFrame with query results

    Example:
        params = [bigquery.ScalarQueryParameter("team", "STRING", "Argentina")]
        df = execute_query(client, "SELECT * FROM events WHERE team = @team", params)
    """
    params_hash = _params_to_hashable(query_params)
    return run_query(client, query, query_params, params_hash)


@st.cache_resource
def get_bigquery_client():
    """Create and cache BigQuery client using Application Default Credentials or Streamlit secrets."""
    try:
        # First, try Application Default Credentials (e.g., on Cloud Run)
        try:
            credentials, project_id = google.auth.default()
            if not project_id:
                project_id = "midyear-castle-328020"
            return bigquery.Client(credentials=credentials, project=project_id)
        except google.auth.exceptions.DefaultCredentialsError:
            # Fall back to Streamlit secrets (for local development)
            creds_info = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(creds_info)
            return bigquery.Client(credentials=credentials, project=credentials.project_id)
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {str(e)}")
        return None

def _params_to_hashable(params: Optional[List]) -> Optional[str]:
    """
    Convert BigQuery parameter objects to a hashable string representation.
    This allows Streamlit to properly cache queries with different parameter values.

    Args:
        params: List of BigQuery query parameters

    Returns:
        String representation of parameters for cache key, or None
    """
    if not params:
        return None

    # Convert each parameter to a string: "name:type:value"
    param_strings = []
    for p in params:
        if hasattr(p, 'name') and hasattr(p, 'value'):
            # Handle both ScalarQueryParameter and ArrayQueryParameter
            if isinstance(p.value, list):
                value_str = f"[{','.join(str(v) for v in p.value)}]"
            else:
                value_str = str(p.value)
            param_strings.append(f"{p.name}:{p.type_}:{value_str}")

    return "|".join(sorted(param_strings))  # Sort for consistency

def _qualify_events_table(sql: str) -> str:
    """Qualify unqualified references to the events table in SQL.

    Replaces occurrences like:
      - FROM events
      - JOIN events
      - CROSS JOIN events
    with the fully-qualified BigQuery table path in BIGQUERY_TABLE.

    Already-qualified references (with backticks) are left untouched.
    Case-insensitive and preserves preceding keywords.
    """
    def _sub(pattern: str, s: str) -> str:
        return re.sub(pattern, lambda m: f"{m.group(1)}`{BIGQUERY_TABLE}`", s, flags=re.IGNORECASE)

    # Replace any form of "FROM events" (with whitespace variations)
    sql = _sub(r"(\bfrom\s+)events\b", sql)
    # Replace any form of "JOIN events" including CROSS/LEFT/RIGHT/INNER joins
    sql = _sub(r"(\bjoin\s+)events\b", sql)
    return sql


@st.cache_data(ttl=600)
def run_query(_client: bigquery.Client, query: str, _query_params: Optional[List] = None,
              params_hash: Optional[str] = None) -> pd.DataFrame:
    """
    Execute BigQuery query and return results as DataFrame.

    Args:
        _client: BigQuery client (prefixed with _ to exclude from cache key)
        query: SQL query string (included in cache key)
        _query_params: Optional list of BigQuery query parameters for parameterized queries
                      (prefixed with _ because objects aren't hashable)
                      Example: [bigquery.ScalarQueryParameter("team", "STRING", "Argentina")]
        params_hash: Hashable string representation of query params (for cache key)
                    Generated automatically by _params_to_hashable()

    Returns:
        pandas.DataFrame with query results

    Note:
        Don't pass params_hash manually - it's computed automatically from _query_params.
        The params_hash ensures the cache differentiates between queries with different
        parameter values.
    """
    if _client is None:
        return pd.DataFrame()

    try:
        # Qualify any unqualified references to the events table
        query = _qualify_events_table(query)

        # Execute with or without parameters
        if _query_params:
            job_config = bigquery.QueryJobConfig(query_parameters=_query_params)
            query_job = _client.query(query, job_config=job_config)
        else:
            query_job = _client.query(query)

        df = query_job.to_dataframe()
        return df
    except Exception as e:
        st.error(f"BigQuery Error: {str(e)}")
        st.code(query)
        if _query_params:
            st.write("Query Parameters:", _query_params)
        return pd.DataFrame()


def fig_to_png_bytes(fig) -> bytes:
    """
    Helper to serialize a Matplotlib figure into PNG bytes.
    This allows Streamlit to cache visualization outputs using @st.cache_data.
    """
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100, facecolor=fig.get_facecolor())
    buf.seek(0)
    val = buf.getvalue()
    buf.close()
    return val


