# Gemini Speech Generation (TTS)

The Gemini API can transform text input into single speaker or multi-speaker
audio using Gemini text-to-speech (TTS) generation capabilities.
Text-to-speech (TTS) generation is *controllable*,
meaning you can use natural language to structure interactions and guide the
*style*, *accent*, *pace*, and *tone* of the audio.

The TTS capability differs from speech generation provided through the
Live API, which is designed for interactive,
unstructured audio, and multimodal inputs and outputs. While the Live API excels
in dynamic conversational contexts, TTS through the Gemini API
is tailored for scenarios that require exact text recitation with fine-grained
control over style and sound, such as podcast or audiobook generation.

This guide shows you how to generate single-speaker and multi-speaker audio from
text.

> **Preview:** Gemini text-to-speech (TTS) is in Preview.

## Before you begin

Ensure you use a Gemini 2.5 model variant with Gemini text-to-speech (TTS)
capabilities, as listed in the Supported models section. For optimal
results, consider which model best fits your specific use case.

> **Note:** TTS models accept text-only inputs and produce audio-only outputs. For a complete list of restrictions specific to TTS models, review the Limitations section.

## Single-speaker TTS

To convert text to single-speaker audio, set the response modality to "audio",
and pass a `SpeechConfig` object with `VoiceConfig` set.
You'll need to choose a voice name from the prebuilt output voices.

This example saves the output audio from the model in a wave file:

### Python

```python
from google import genai
from google.genai import types
import wave

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client()

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents="Say cheerfully: Have a wonderful day!",
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
               voice_name='Kore',
            )
         )
      ),
   )
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name='out.wav'
wave_file(file_name, data) # Saves the file to current directory
```

### JavaScript

```javascript
import {GoogleGenAI} from '@google/genai';
import wav from 'wav';

async function saveWaveFile(
   filename,
   pcmData,
   channels = 1,
   rate = 24000,
   sampleWidth = 2,
) {
   return new Promise((resolve, reject) => {
      const writer = new wav.FileWriter(filename, {
            channels,
            sampleRate: rate,
            bitDepth: sampleWidth * 8,
      });

      writer.on('finish', resolve);
      writer.on('error', reject);

      writer.write(pcmData);
      writer.end();
   });
}

async function main() {
   const ai = new GoogleGenAI({});

   const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-preview-tts",
      contents: [{ parts: [{ text: 'Say cheerfully: Have a wonderful day!' }] }],
      config: {
            responseModalities: ['AUDIO'],
            speechConfig: {
               voiceConfig: {
                  prebuiltVoiceConfig: { voiceName: 'Kore' },
               },
            },
      },
   });

   const data = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
   const audioBuffer = Buffer.from(data, 'base64');

   const fileName = 'out.wav';
   await saveWaveFile(fileName, audioBuffer);
}
await main();
```

## Multi-speaker TTS

For multi-speaker audio, you'll need a `MultiSpeakerVoiceConfig` object with
each speaker (up to 2) configured as a `SpeakerVoiceConfig`.
You'll need to define each `speaker` with the same names used in the prompt:

### Python

```python
from google import genai
from google.genai import types
import wave

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client()

prompt = """TTS the following conversation between Joe and Jane:
         Joe: How's it going today Jane?
         Jane: Not too bad, how about you?"""

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=prompt,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
               types.SpeakerVoiceConfig(
                  speaker='Joe',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                     )
                  )
               ),
               types.SpeakerVoiceConfig(
                  speaker='Jane',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                     )
                  )
               ),
            ]
         )
      )
   )
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name='out.wav'
wave_file(file_name, data) # Saves the file to current directory
```

### JavaScript

```javascript
import {GoogleGenAI} from '@google/genai';
import wav from 'wav';

async function saveWaveFile(
   filename,
   pcmData,
   channels = 1,
   rate = 24000,
   sampleWidth = 2,
) {
   return new Promise((resolve, reject) => {
      const writer = new wav.FileWriter(filename, {
            channels,
            sampleRate: rate,
            bitDepth: sampleWidth * 8,
      });

      writer.on('finish', resolve);
      writer.on('error', reject);

      writer.write(pcmData);
      writer.end();
   });
}

async function main() {
   const ai = new GoogleGenAI({});

   const prompt = `TTS the following conversation between Joe and Jane:
         Joe: How's it going today Jane?
         Jane: Not too bad, how about you?`;

   const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-preview-tts",
      contents: [{ parts: [{ text: prompt }] }],
      config: {
            responseModalities: ['AUDIO'],
            speechConfig: {
               multiSpeakerVoiceConfig: {
                  speakerVoiceConfigs: [
                        {
                           speaker: 'Joe',
                           voiceConfig: {
                              prebuiltVoiceConfig: { voiceName: 'Kore' }
                           }
                        },
                        {
                           speaker: 'Jane',
                           voiceConfig: {
                              prebuiltVoiceConfig: { voiceName: 'Puck' }
                           }
                        }
                  ]
               }
            }
      }
   });

   const data = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
   const audioBuffer = Buffer.from(data, 'base64');

   const fileName = 'out.wav';
   await saveWaveFile(fileName, audioBuffer);
}

await main();
```

## Controlling speech style with prompts

You can control style, tone, accent, and pace using natural language prompts
for both single- and multi-speaker TTS.

For example, in a single-speaker prompt, you can say:

```
Say in an spooky whisper:
"By the pricking of my thumbs...
Something wicked this way comes"
```

In a multi-speaker prompt, provide the model with each speaker's name and
corresponding transcript. You can also provide guidance for each speaker
individually:

```
Make Speaker1 sound tired and bored, and Speaker2 sound excited and happy:

Speaker1: So... what's on the agenda today?
Speaker2: You're never going to guess!
```

## Generating a prompt to convert to audio

The TTS models only output audio, but you can use other models to generate a
transcript first, then pass that transcript to the TTS model to read aloud.

### Python

```python
from google import genai
from google.genai import types

client = genai.Client()

transcript = client.models.generate_content(
   model="gemini-2.5-flash",
   contents="""Generate a short transcript around 100 words that reads
            like it was clipped from a podcast by excited herpetologists.
            The hosts names are Dr. Anya and Liam.""").text

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=transcript,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
               types.SpeakerVoiceConfig(
                  speaker='Dr. Anya',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                     )
                  )
               ),
               types.SpeakerVoiceConfig(
                  speaker='Liam',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                     )
                  )
               ),
            ]
         )
      )
   )
)

# ...Code to stream or save the output
```

## Voice options

TTS models support the following 30 voice options in the `voice_name` field:

| Voice | Style | Voice | Style | Voice | Style |
|---|---|---|---|---|---|
| **Zephyr** | Bright | **Puck** | Upbeat | **Charon** | Informative |
| **Kore** | Firm | **Fenrir** | Excitable | **Leda** | Youthful |
| **Orus** | Firm | **Aoede** | Breezy | **Callirrhoe** | Easy-going |
| **Autonoe** | Bright | **Enceladus** | Breathy | **Iapetus** | Clear |
| **Umbriel** | Easy-going | **Algieba** | Smooth | **Despina** | Smooth |
| **Erinome** | Clear | **Algenib** | Gravelly | **Rasalgethi** | Informative |
| **Laomedeia** | Upbeat | **Achernar** | Soft | **Alnilam** | Firm |
| **Schedar** | Even | **Gacrux** | Mature | **Pulcherrima** | Forward |
| **Achird** | Friendly | **Zubenelgenubi** | Casual | **Vindemiatrix** | Gentle |
| **Sadachbia** | Lively | **Sadaltager** | Knowledgeable | **Sulafat** | Warm |

## Supported languages

The TTS models detect the input language automatically. Supported languages include:
Arabic, Bangla, Dutch, English, French, German, Hindi, Indonesian, Italian, Japanese, Korean, Marathi, Polish, Portuguese, Romanian, Russian, Spanish, Tamil, Telugu, Thai, Turkish, Ukrainian, Vietnamese, and many more (70+ languages total).

## Supported models

| Model | Single speaker | Multispeaker |
|---|---|---|
| Gemini 2.5 Flash Preview TTS | Yes | Yes |
| Gemini 2.5 Pro Preview TTS | Yes | Yes |

## Limitations

- TTS models can only receive text inputs and generate audio outputs.
- A TTS session has a context window limit of 32k tokens.
- Review Languages section for language support.

## Prompting guide

The Gemini Native Audio Generation TTS model differentiates itself from
traditional TTS models by using a large language model that knows not only
*what to say*, but also *how to say it*.

### Prompting structure

A robust prompt ideally includes the following elements:

- **Audio Profile** - Establishes a persona for the voice, defining a character identity, archetype and any other characteristics like age, background etc.
- **Scene** - Sets the stage. Describes both the physical environment and the "vibe".
- **Director's Notes** - Performance guidance where you can break down which instructions are important for your virtual talent to take note of. Examples are style, breathing, pacing, articulation and accent.
- **Sample context** - Gives the model a contextual starting point.
- **Transcript** - The text that the model will speak out.

### Example full prompt

```
# AUDIO PROFILE: Jaz R.
## "The Morning Hype"

## THE SCENE: The London Studio
It is 10:00 PM in a glass-walled studio overlooking the moonlit London skyline,
but inside, it is blindingly bright. The red "ON AIR" tally light is blazing.
Jaz is standing up, not sitting, bouncing on the balls of their heels to the
rhythm of a thumping backing track.

### DIRECTOR'S NOTES
Style:
* The "Vocal Smile": You must hear the grin in the audio.
* Dynamics: High projection without shouting.

Pace: Speaks at an energetic pace, keeping up with the fast music.

Accent: Jaz is from Brixton, London

### SAMPLE CONTEXT
Jaz is the industry standard for Top 40 radio, high-octane event promos.

#### TRANSCRIPT
Yes, massive vibes in the studio! You are locked in and it is absolutely
popping off in London right now.
```

### Detailed Prompting Strategies

- **Style:** Sets the tone and Style of the generated speech. Be descriptive.
- **Accent:** Describe the desired accent. The more specific, the better.
- **Pacing:** Overall pacing and pace variation throughout the piece.
