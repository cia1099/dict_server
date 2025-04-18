from pydantic import BaseModel


class Text2SpeechIn(BaseModel):
    text: str
    lang: str
    name: str = "Ava"
    gender: str | None = None

    _voicers = {
        "Ava": {
            "en-US": "en-US-AvaMultilingualNeural",
            "en-GB": "en-GB-AdaMultilingualNeural",
            "en-AU": "en-AU-AnnetteNeural",
            "en-CA": "en-CA-ClaraNeural",
            "en-IN": "en-IN-AashiNeural",
        },
        "Nova": {
            "en-US": "en-US-NovaTurboMultilingualNeural",
            "en-GB": "en-GB-OliviaNeural",
            "en-AU": "en-AU-NatashaNeural",
            "en-CA": "fr-CA-SylvieNeural",
            "en-IN": "en-IN-NeerjaNeural",
        },
        "Emma": {
            "en-US": "en-US-EmmaMultilingualNeural",
            "en-GB": "en-GB-BellaNeural",
            "en-AU": "en-AU-ElsieNeural",
            "en-CA": "en-US-EmmaMultilingualNeural",
            "en-IN": "en-IN-AashiNeural",
        },
        "Brandon": {
            "en-US": "en-US-BrandonMultilingualNeural",
            "en-GB": "en-GB-RyanNeural",
            "en-AU": "en-AU-KenNeural",
            "en-CA": "en-US-BrandonMultilingualNeural",
            "en-IN": "gu-IN-NiranjanNeural",
        },
        "Adam": {
            "en-US": "en-US-AdamMultilingualNeural",
            "en-GB": "en-GB-AlfieNeural",
            "en-AU": "en-AU-TimNeural",
            "en-CA": "en-CA-LiamNeural",
            "en-IN": "hi-IN-ArjunNeural",
        },
        "Christopher": {
            "en-US": "en-US-ChristopherMultilingualNeural",
            "en-GB": "en-GB-ThomasNeural",
            "en-AU": "en-AU-WilliamNeural",
            "en-CA": "en-US-ChristopherMultilingualNeural",
            "en-IN": "en-IN-KunalNeural",
        },
    }

    def get_voice(self):
        return self._voicers.get(self.name, {}).get(
            self.lang, "en-US-AvaMultilingualNeural"
        )
