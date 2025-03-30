# Live Translate

Live Translate is a cutting-edge tool that provides real-time, simultaneous
translation across various languages. It leverages the power of Deepgram for
accurate transcription and DeepL for seamless translation from any
source language to any target language.

## Features

- **Real-time Translation**: Translates spoken language into another language as it happens.
- **Wide Language Support**: Offers the flexibility to translate between a multitude of language pairs.
- **Audio Input Support**: Listens to live audio input from the microphone for immediate transcription and translation.
- **Deepgram Integration**: Utilizes Deepgram for accurate, AI-powered speech recognition.
- **DeepL**: Leverages DeepL robust language model to provide translations.

## Prerequisites

Before you begin, ensure you have the following:

- Python version 3.11 or higher.
- Microphone access on your device.
- API keys for both Deepgram and DeepL services.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/afiodorov/livetranslate.git
   cd livetranslate
   ```

2. Install dependencies using uv:
   ```bash
   make install
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

3. Set up your environment variables:
   
   Copy the example environment file and add your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Then edit the `.env` file and add your API keys:
   ```
   DEEPL_API_KEY=your_deepl_api_key_here
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   USE_DEEPL_PRO=false
   ```

## Advanced Language Models (LLM)

The translation quality can be significantly enhanced with the use of advanced
Large Language Models (LLM). However, current LLMs may not provide the speed
required to match the real-time transcription rate. Future updates may include
optimizations for faster LLM integration.

## License

Live Translate is open-sourced under the MIT license. For more details, see the LICENSE file.

## Usage

Run the application with source and target languages:

```bash
# Using Python directly
python -m livetranslate.main -s pl-PL -t en-US

# Or using the make command
make run
```

### Command Line Options

- `-s, --source`: Source language (default: ru-RU)
- `-t, --target`: Target language (default: same as source)
- `-f, --fullscreen`: Launch application in fullscreen mode

### Example

```bash
# Translate from Polish to English
python -m livetranslate.main -s pl-PL -t en-US

# Use fullscreen mode
python -m livetranslate.main -s ja-JP -t en-US -f
```

## Demo

![Demo of the livetranslate](https://github.com/afiodorov/livetranslate/raw/main/demo.gif)
