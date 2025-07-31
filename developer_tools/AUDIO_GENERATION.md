# Audio Generation Options

This project provides multiple options for generating high-quality Chinese audio files for dictation exercises.

## Current Options

### 1. Google Text-to-Speech (Recommended for beginners)
**File**: `generate_audios_google.py`

**Pros**:
- Easy to set up
- High-quality neural voices
- Good free tier
- Reliable service

**Setup**:
1. Install: `pip install google-cloud-texttospeech`
2. Set up Google Cloud credentials:
   - Option A: `gcloud auth application-default login`
   - Option B: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Run: `python generate_audios_google.py`

**Voices Available**:
- `cmn-CN-Wavenet-A`: Female (Neural) - **Recommended**
- `cmn-CN-Wavenet-B`: Male (Neural)
- `cmn-CN-Wavenet-C`: Female (Neural)
- `cmn-CN-Wavenet-D`: Male (Neural)
- Standard voices also available

### 2. Azure Cognitive Services (Best quality)
**File**: `generate_audios_azure.py`

**Pros**:
- Highest quality neural voices
- Very natural sounding
- Multiple voice personalities
- Excellent Chinese pronunciation

**Setup**:
1. Install: `pip install azure-cognitiveservices-speech`
2. Get Azure Speech Service key from Azure Portal
3. Set environment variables:
   - `AZURE_SPEECH_KEY`: Your Azure key
   - `AZURE_SPEECH_REGION`: Your region (e.g., 'eastus')
4. Run: `python generate_audios_azure.py`

**Voices Available**:
- `zh-CN-XiaoxiaoNeural`: Xiaoxiao (Female, Young) - **Recommended**
- `zh-CN-YunxiNeural`: Yunxi (Male, Young)
- `zh-CN-YunyangNeural`: Yunyang (Male, News)
- `zh-CN-XiaochenNeural`: Xiaochen (Female, Friendly)
- And many more...

### 3. Google Translate TTS (Current - Basic)
**File**: `generate_audios.py`

**Pros**:
- No setup required
- Free
- Works immediately

**Cons**:
- Lower quality
- Less natural sounding
- Limited voice options

**Setup**:
1. Install: `pip install gTTS`
2. Run: `python generate_audios.py`

## Voice Selection

Both scripts will prompt you to choose a voice when you run them. You can:

1. **Accept the default** (recommended for first use)
2. **Choose a different voice** from the list
3. **Test different voices** by running the script multiple times

## Recommendations

### For Learning Chinese:
- **Start with Google Cloud TTS** - Easy setup, good quality
- **Upgrade to Azure** when you want the best possible quality

### Voice Recommendations:
- **Female voices** are often clearer for learning
- **Neural voices** sound more natural than standard voices
- **Young voices** are typically easier to understand

## Cost Considerations

- **Google Cloud**: ~$4 per 1 million characters (very affordable)
- **Azure**: ~$16 per 1 million characters (higher quality, higher cost)
- **gTTS**: Free (but lower quality)

## File Structure

Generated audio files are saved to `static/audio_files/` with the naming convention:
- `{sentence_id}_{difficulty}.mp3`

Example: `1_HSK1.mp3`, `42_HSK2.mp3`

## Troubleshooting

### Google Cloud Issues:
- Make sure you're authenticated: `gcloud auth application-default login`
- Check your billing is enabled in Google Cloud Console

### Azure Issues:
- Verify your Speech Service key is correct
- Check your region matches your service location
- Ensure your subscription has Speech Service enabled

### General Issues:
- Check your internet connection
- Verify the `sentences.json` file exists
- Make sure you have write permissions to `static/audio_files/` 