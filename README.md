# Live Translate

Live Translate is a cutting-edge tool that provides real-time, simultaneous
translation across various languages. It leverages the power of Deepgram for
accurate transcription and Google Translate for seamless translation from any
source language to any target language.

## Features

- **Real-time Translation**: Translates spoken language into another language as it happens.
- **Wide Language Support**: Offers the flexibility to translate between a multitude of language pairs.
- **Audio Input Support**: Listens to live audio input from the microphone for immediate transcription and translation.
- **Deepgram Integration**: Utilizes Deepgram for accurate, AI-powered speech recognition.
- **Google Translate**: Leverages Google Translate's robust language model to provide translations.

## Prerequisites

Before you begin, ensure you have the following:

- Python version 3.11 or higher.
- Microphone access on your device.
- API keys for both Deepgram and Google Translate services.

## Advanced Language Models (LLM)

The translation quality can be significantly enhanced with the use of advanced
Large Language Models (LLM). However, current LLMs may not provide the speed
required to match the real-time transcription rate. Future updates may include
optimizations for faster LLM integration.

## License

Live Translate is open-sourced under the MIT license. For more details, see the LICENSE file.

## Demo

```
python -m livetranslate.main -s pl-PL -t en-US
```

![Demo of the livetranslate](https://github.com/afiodorov/livetranslate/raw/main/demo.gif)
