# Live translate

Idea is to watch something Russian with my Brazilian girlfriend and project
live translation on a screen.

For now it is listening to the microphone, transcribes it using Deepgram and
translates it using Google Translate (much faster than any LLM).

Works ok, see demo:

# Demo

```
python -m livetranslate.main -s ja-JP -t en-US
```

![Demo of the livetranslate](https://github.com/afiodorov/livetranslate/raw/main/demo.gif)
