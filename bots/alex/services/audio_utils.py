import base64
import audioop

def mulaw_to_pcm16(mulaw_data_base64):
    """
    Convert mulaw audio to 16-bit PCM.
    Twilio sends mulaw at 8kHz, Gemini expects PCM at 16kHz.
    """
    # Decode base64
    mulaw_bytes = base64.b64decode(mulaw_data_base64)
    
    # Convert mulaw to linear PCM (16-bit)
    pcm_bytes = audioop.ulaw2lin(mulaw_bytes, 2)  # 2 = 16-bit samples
    
    # Resample from 8kHz to 16kHz (Gemini's native rate)
    pcm_16khz = audioop.ratecv(pcm_bytes, 2, 1, 8000, 16000, None)[0]
    
    # Encode back to base64
    return base64.b64encode(pcm_16khz).decode('utf-8')

def pcm16_to_mulaw(pcm_data_base64, from_rate=24000, to_rate=8000):
    """
    Convert 16-bit PCM to mulaw.
    Gemini outputs PCM at 24kHz, Twilio expects mulaw at 8kHz.
    """
    # Decode base64
    pcm_bytes = base64.b64decode(pcm_data_base64)
    
    # Resample from 24kHz (Gemini output) to 8kHz (Twilio input)
    pcm_8khz = audioop.ratecv(pcm_bytes, 2, 1, from_rate, to_rate, None)[0]
    
    # Convert linear PCM to mulaw
    mulaw_bytes = audioop.lin2ulaw(pcm_8khz, 2)
    
    # Encode back to base64
    return base64.b64encode(mulaw_bytes).decode('utf-8')
