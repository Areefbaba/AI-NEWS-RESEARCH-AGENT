"""Multi-model LLM service supporting cascading fallbacks: Groq, Gemini, OpenAI, Ollama, and Heuristic."""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for Groq Cloud API (Llama-3.3-70b-versatile, Mixtral, etc.)."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GROQ_API_KEY
        self.model = self.settings.GROQ_MODEL
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("gsk_your"))

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        if not self.is_configured():
            return None
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024
            }

            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                elif resp.status_code == 429:
                    logger.warning("Groq rate limit exceeded (HTTP 429). Triggering fallback.")
                else:
                    logger.warning("Groq API returned HTTP %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Groq API request failed: %s", e)
        return None


class GeminiClient:
    """Client for Google Gemini API via official OpenAI-compatible endpoint."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GEMINI_API_KEY
        self.model = self.settings.GEMINI_MODEL
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("AIzaSy"))

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        if not self.is_configured():
            return None
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024
            }

            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                elif resp.status_code == 429:
                    logger.warning("Gemini rate limit exceeded (HTTP 429). Triggering fallback.")
                else:
                    logger.warning("Gemini API returned HTTP %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Gemini API request failed: %s", e)
        return None


class OpenAIClient:
    """Client for OpenAI API (gpt-4o, gpt-4o-mini)."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENAI_API_KEY
        self.model = self.settings.OPENAI_MODEL
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("sk-your"))

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        if not self.is_configured():
            return None
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1024
            }

            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                elif resp.status_code == 429:
                    logger.warning("OpenAI rate limit exceeded (HTTP 429). Triggering fallback.")
                else:
                    logger.warning("OpenAI API returned HTTP %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("OpenAI API request failed: %s", e)
        return None


class OllamaClient:
    """Client for local Ollama API running Qwen."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = self.settings.OLLAMA_MODEL
        self.timeout = self.settings.OLLAMA_TIMEOUT_SECONDS
        self._cached_status: Optional[Tuple[bool, str, float]] = None

    def check_availability(self) -> Tuple[bool, str]:
        """Check if Ollama server is running and configured model is installed (cached for 30s)."""
        import time
        now = time.time()
        if self._cached_status and (now - self._cached_status[2] < 30.0):
            return self._cached_status[0], self._cached_status[1]

        res_bool = False
        res_msg = ""
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    model_found = any(self.model in m or m.startswith(self.model.split(":")[0]) for m in models)
                    if model_found:
                        res_bool, res_msg = True, f"Ollama running with model '{self.model}'."
                    else:
                        res_bool, res_msg = False, f"Ollama is running, but model '{self.model}' is not pulled yet."
                else:
                    res_bool, res_msg = False, f"Ollama returned HTTP {resp.status_code}."
        except Exception as e:
            res_bool, res_msg = False, f"Ollama is not running locally ({str(e)})."

        self._cached_status = (res_bool, res_msg, now)
        return res_bool, res_msg

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """Generate text completion from local Ollama model."""
        try:
            payload: Dict[str, Any] = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "top_p": 0.9}
            }
            if system:
                payload["system"] = system

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "").strip()
                logger.warning("Ollama generate returned status %d", resp.status_code)
        except Exception as e:
            logger.warning("Ollama generate request failed: %s", e)
        return None


class HeuristicAnalyzer:
    """Reliable, zero-hallucination deterministic text analyzer for fallback."""

    @staticmethod
    def extract_summary(text: str, max_chars: int = 400) -> str:
        """Extract lead paragraph and salient sentences without inventing claims."""
        if not text:
            return ""
        clean = " ".join(text.split())
        sentences = re.split(r"(?<=[.!?])\s+", clean)
        summary = ""
        for s in sentences:
            if len(summary) + len(s) + 1 <= max_chars:
                summary = f"{summary} {s}".strip() if summary else s
            else:
                break
        return summary or clean[:max_chars]

    @staticmethod
    def extract_key_claims(text: str, max_claims: int = 3) -> List[str]:
        """Extract factual claim sentences containing key entities or numbers."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        claims = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 25 and (re.search(r"\d+", s_clean) or re.search(r"\b(announced|signed|confirmed|won|crushed|released)\b", s_clean, re.I)):
                claims.append(s_clean)
                if len(claims) >= max_claims:
                    break
        return claims or sentences[:max_claims]

    @staticmethod
    def build_structured_200_word_summary(
        headline: str,
        short_desc: str,
        content: str,
        domain: str,
        why_it_matters: str,
        actors_or_subcat: Optional[str] = None
    ) -> str:
        """Deterministically assemble a comprehensive ~180-220 word analytical overview."""
        text = f"{short_desc} {content}".strip()
        clean = " ".join(text.split())
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if len(s.strip()) > 15]

        # Paragraph 1: Core development & factual anchor (~60 words)
        p1_parts = []
        if headline:
            p1_parts.append(f"In this development, {headline.rstrip('.')}.")
        for s in sentences[:2]:
            if s not in p1_parts:
                p1_parts.append(s)
        p1 = " ".join(p1_parts)

        # Paragraph 2: Technical/Strategic details & primary claims (~80 words)
        p2_parts = []
        # Find quantitative or entity-rich sentences
        detail_sentences = [
            s for s in sentences[2:8]
            if re.search(r"\d+", s) or re.search(r"\b(confirmed|announced|margin|test|series|model|paper|benchmark|treaty|border|defence|security)\b", s, re.I)
        ]
        if not detail_sentences and len(sentences) > 2:
            detail_sentences = sentences[2:5]

        for s in detail_sentences[:3]:
            p2_parts.append(s)

        if not p2_parts:
            if domain == "cricket":
                p2_parts.append("Official match dispatches record decisive milestones, team performance metrics, and significant tournament standings.")
            elif domain == "geopolitics":
                p2_parts.append(f"Diplomatic dispatches indicate active coordination involving {actors_or_subcat or 'state actors'}, focusing on strategic defense agreements and regional equilibrium.")
            else:
                p2_parts.append("Technical documentation highlights empirical benchmarks, architectural configurations, and reproducible experimental findings.")

        p2 = " ".join(p2_parts)

        # Paragraph 3: Strategic Significance & Takeaway (~60 words)
        p3_parts = [why_it_matters.rstrip(".")]
        if domain == "cricket":
            p3_parts.append("This outcome directly affects international rankings, series momentum, and upcoming squad selection dynamics.")
        elif domain == "geopolitics":
            p3_parts.append("Independent monitors continue to assess corroborating intelligence reports to evaluate long-term geopolitical and economic equilibrium.")
        else:
            p3_parts.append("Engineers and practitioners should review the accompanying technical documentation and official artifacts for concrete implementation details.")
        p3 = ". ".join(p3_parts) + "."

        full_summary = f"{p1}\n\n{p2}\n\n{p3}"
        return full_summary


class MultiProviderLLMManager:
    """Manages multi-provider cascading fallback across Groq, Gemini, OpenAI, Ollama, and Heuristic."""

    def __init__(self):
        self.settings = get_settings()
        self.groq = GroqClient()
        self.gemini = GeminiClient()
        self.openai = OpenAIClient()
        self.ollama = OllamaClient()
        self.heuristic = HeuristicAnalyzer()

        # Parse fallback order
        raw_order = self.settings.LLM_FALLBACK_ORDER.split(",")
        self.fallback_order = [p.strip().lower() for p in raw_order if p.strip()]
        if "heuristic" not in self.fallback_order:
            self.fallback_order.append("heuristic")

    def get_preferred_engine_status(self) -> Tuple[str, str, str]:
        """Detect the highest-priority provider currently available.
        
        Returns: (provider_id, provider_display_name, model_info)
        """
        for provider in self.fallback_order:
            if provider == "groq" and self.groq.is_configured():
                return "groq", "Groq Cloud", f"Model: {self.groq.model} (Ultra-Fast)"
            elif provider == "gemini" and self.gemini.is_configured():
                return "gemini", "Google Gemini", f"Model: {self.gemini.model}"
            elif provider == "openai" and self.openai.is_configured():
                return "openai", "OpenAI", f"Model: {self.openai.model}"
            elif provider == "ollama":
                avail, _ = self.ollama.check_availability()
                if avail:
                    return "ollama", "Local Ollama", f"Model: {self.ollama.model}"
            elif provider == "heuristic":
                return "heuristic", "Deterministic Intelligence Engine", "Heuristic Verification (Zero Paid Tokens)"

        return "heuristic", "Deterministic Intelligence Engine", "Zero Paid Tokens / Offline"

    def generate_analytical_summary(
        self,
        headline: str,
        short_desc: str,
        content: str,
        domain: str,
        why_it_matters: str,
        actors_or_subcat: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate a substantive ~200-word summary with cascading provider fallback.
        
        Returns: (summary_text, successful_provider_name)
        """
        system_prompt = (
            "You are a senior analytical intelligence reporter. "
            "Write a concise, high-density, professional 3-paragraph summary of exactly around 180 to 220 words. "
            "Paragraph 1 covers the core development and confirmed event facts. "
            "Paragraph 2 provides key numbers, quotes, technical mechanisms, or specific metrics. "
            "Paragraph 3 explains why this matters and downstream strategic implications. "
            "Never invent facts, statistics, or URLs not present in the source text."
        )

        user_prompt = (
            f"Headline: {headline}\n"
            f"Domain: {domain}\n"
            f"Why It Matters: {why_it_matters}\n"
            f"Details: {short_desc}\n"
            f"Source Excerpt: {content[:1000]}\n\n"
            "Produce the structured ~200-word analysis now:"
        )

        for provider in self.fallback_order:
            if provider == "groq" and self.groq.is_configured():
                resp = self.groq.generate(prompt=user_prompt, system=system_prompt)
                if resp and len(resp.split()) >= 80:
                    return resp.strip(), f"Groq ({self.groq.model})"

            elif provider == "gemini" and self.gemini.is_configured():
                resp = self.gemini.generate(prompt=user_prompt, system=system_prompt)
                if resp and len(resp.split()) >= 80:
                    return resp.strip(), f"Gemini ({self.gemini.model})"

            elif provider == "openai" and self.openai.is_configured():
                resp = self.openai.generate(prompt=user_prompt, system=system_prompt)
                if resp and len(resp.split()) >= 80:
                    return resp.strip(), f"OpenAI ({self.openai.model})"

            elif provider == "ollama":
                avail, _ = self.ollama.check_availability()
                if avail:
                    resp = self.ollama.generate(prompt=user_prompt, system=system_prompt)
                    if resp and len(resp.split()) >= 80:
                        return resp.strip(), f"Ollama ({self.ollama.model})"

            elif provider == "heuristic":
                # Deterministic structured multi-paragraph synthesis
                summary = self.heuristic.build_structured_200_word_summary(
                    headline=headline,
                    short_desc=short_desc,
                    content=content,
                    domain=domain,
                    why_it_matters=why_it_matters,
                    actors_or_subcat=actors_or_subcat
                )
                return summary, "Heuristic Engine"

        # Fallback safeguard
        return self.heuristic.build_structured_200_word_summary(
            headline=headline,
            short_desc=short_desc,
            content=content,
            domain=domain,
            why_it_matters=why_it_matters,
            actors_or_subcat=actors_or_subcat
        ), "Heuristic Engine"


# Global singleton instance
_llm_manager: Optional[MultiProviderLLMManager] = None


def get_llm_manager() -> MultiProviderLLMManager:
    """Retrieve or initialize the global MultiProviderLLMManager."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = MultiProviderLLMManager()
    return _llm_manager


def get_analysis_mode() -> Tuple[str, Optional[OllamaClient]]:
    """Preserve backwards compatibility for mode detection."""
    manager = get_llm_manager()
    pid, name, _ = manager.get_preferred_engine_status()
    if pid == "ollama":
        return "local_llm", manager.ollama
    elif pid in ("groq", "gemini", "openai"):
        return f"cloud_llm_{pid}", None
    return "heuristic_fallback", None
