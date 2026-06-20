# DEC027 - Switch from Anthropic Claude to Google Vertex AI Gemini for Preview Generation

Date: 2026-06-20

## Status

Approved.

## Context

The match preview pipeline (`generate_match_headlines.py`) previously used the Anthropic Claude API (`claude-haiku-4-5`) to generate tactical headlines and insights. However, using the Anthropic API requires configuring a billing API key (`ANTHROPIC_API_KEY`), implying extra costs for the user.

Since the workspace environment is already authenticated to Google Cloud and has access to multiple GCP projects (with `statsbomb-db` and the Vertex AI API enabled), we want to utilize Google's Vertex AI Gemini models (`gemini-2.5-flash`) via the ambient Application Default Credentials (ADC) instead.

## Decision

- **Use Vertex AI Gemini**: Update `generate_match_headlines.py` to call Google's Vertex AI `gemini-2.5-flash` model under the `statsbomb-db` project and `us-central1` region.
- **Remove Anthropic Dependency**: Remove the `anthropic` library from `requirements.txt` and replace it with `google-cloud-aiplatform`.
- **Remove API Key Check**: Remove the requirement for the `ANTHROPIC_API_KEY` environment variable so the pipeline runs out-of-the-box using local ambient Google Cloud credentials.

## Consequences

- Zero additional API billing costs for the user.
- Seamless execution on local machines and Cloud Run instances utilizing ambient GCP credentials.
- Dependencies are simplified, and unused external packages are removed.
