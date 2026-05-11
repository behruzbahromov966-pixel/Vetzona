from __future__ import annotations

from google import genai


class GeminiService:
    def __init__(self, api_key: str, model_name: str) -> None:
        self.is_ready = bool(api_key)
        self._model_name = model_name
        self._client: genai.Client | None = None
        if self.is_ready:
            self._client = genai.Client(api_key=api_key)

    async def ask(self, prompt: str) -> str:
        if not self.is_ready or self._client is None:
            return "Gemini API kaliti sozlanmagan. Admin bilan bog'laning."

        user_q = (prompt or "").strip()
        if len(user_q) > 8000:
            user_q = user_q[:8000] + "\n[…matn qisqartirildi]"

        scoped_prompt = (
            "You are a veterinary and livestock assistant for Uzbek users.\n"
            "Allowed topics: veterinary medicine, animal diseases, animal feeding, breeding, "
            "farm management, livestock care, poultry care, pet care.\n"
            "If user asks anything outside these topics, respond with exactly: OFF_TOPIC\n"
            "Answer in Uzbek language. Keep answers practical and clear.\n\n"
            f"User question: {user_q}"
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=scoped_prompt,
            )
        except Exception:
            return "Kechirasiz, AI hozir javob bera olmadi. Keyinroq urinib ko'ring."

        text = (response.text or "").strip()
        if not text:
            return "Kechirasiz, AI hozir javob bera olmadi. Keyinroq urinib ko'ring."
        if text == "OFF_TOPIC":
            return (
                "Kechirasiz, men faqat veterinariya va chorvachilik bo'yicha "
                "savollarga javob bera olaman."
            )
        return text
