import { GoogleGenAI, Type } from "@google/genai";
import { AnalysisResult, HistorySession } from "../types";
import { getCachedAudio, cacheAudio, generateCacheKey } from "./audioCache";

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY });

// Helper to convert Blob to Base64
const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      // Handle both data URI with scheme and raw base64
      const base64 = result.includes(',') ? result.split(',')[1] : result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

// Helper to add WAV header to raw PCM data
// Gemini TTS returns raw PCM: 24kHz, 1 channel, 16-bit
const addWavHeader = (pcmData: Uint8Array, sampleRate: number = 24000, numChannels: number = 1): ArrayBuffer => {
  const headerLength = 44;
  const dataLength = pcmData.length;
  const buffer = new ArrayBuffer(headerLength + dataLength);
  const view = new DataView(buffer);

  // RIFF identifier
  writeString(view, 0, 'RIFF');
  // RIFF chunk length
  view.setUint32(4, 36 + dataLength, true);
  // RIFF type
  writeString(view, 8, 'WAVE');
  // format chunk identifier
  writeString(view, 12, 'fmt ');
  // format chunk length
  view.setUint32(16, 16, true);
  // sample format (raw)
  view.setUint16(20, 1, true);
  // channel count
  view.setUint16(22, numChannels, true);
  // sample rate
  view.setUint32(24, sampleRate, true);
  // byte rate (sample rate * block align)
  view.setUint32(28, sampleRate * numChannels * 2, true);
  // block align (channel count * bytes per sample)
  view.setUint16(32, numChannels * 2, true);
  // bits per sample
  view.setUint16(34, 16, true);
  // data chunk identifier
  writeString(view, 36, 'data');
  // data chunk length
  view.setUint32(40, dataLength, true);

  // write the PCM data
  const uint8View = new Uint8Array(buffer);
  uint8View.set(pcmData, 44);

  return buffer;
};

const writeString = (view: DataView, offset: number, string: string) => {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
};

export const generateChallenge = async (history: HistorySession[] = []): Promise<string> => {
  try {
    // Adaptive Learning Logic
    let contextPrompt = "";

    if (history.length > 0) {
      // Extract unique problem words from the last 10 sessions
      const recentProblems = new Set<string>();
      history.slice(0, 10).forEach(session => {
        session.result.problemWords.forEach(w => recentProblems.add(w));
      });

      const problemList = Array.from(recentProblems).slice(0, 15); // Limit to 15 words

      if (problemList.length > 0) {
        contextPrompt = `
          The user has recently struggled with pronunciation of these words: ${problemList.join(', ')}. 
          Please generate a sentence that incorporates some of these words or similar phonemic patterns (like 'th', 'r', 'l', 'v/w') to help them practice.
          The sentence should be natural but challenging.
        `;
      }
    }

    if (!contextPrompt) {
      contextPrompt = "Generate a difficult sentence or tongue twister for American English pronunciation practice. It should focus on common problem areas like 'R', 'TH', 'V vs W', or 'Schwa'.";
    }

    // Switched to 2.5-flash for speed
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `${contextPrompt} Return ONLY the sentence text.`,
    });
    return response.text.trim();
  } catch (error) {
    console.error("Error generating challenge:", error);
    return "Usually, Silas's stubborn vision is to sift seven silky seashells beside the station.";
  }
};

export const analyzePronunciation = async (audioBlob: Blob, referenceText: string, mimeType: string): Promise<AnalysisResult> => {
  try {
    const base64Audio = await blobToBase64(audioBlob);

    const schema = {
      type: Type.OBJECT,
      properties: {
        overallScore: { type: Type.INTEGER, description: "0-100 score based on clarity and accent." },
        phonemeAccuracy: { type: Type.INTEGER, description: "0-100 score on specific sounds." },
        flowRhythmScore: { type: Type.INTEGER, description: "0-100 score on intonation and linking." },
        coachNotes: { type: Type.STRING, description: "A paragraph explaining major habits to unlearn (e.g., 'You are turning 'zh' into 'r'')." },
        specificFixes: {
          type: Type.ARRAY,
          items: { type: Type.STRING },
          description: "List of 3-4 specific technical instructions to fix the mouth position."
        },
        problemWords: {
          type: Type.ARRAY,
          items: { type: Type.STRING },
          description: "List of individual words that were mispronounced."
        },
        wordBreakdown: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              word: { type: Type.STRING },
              isCorrect: { type: Type.BOOLEAN },
              phoneticReceived: { type: Type.STRING, description: "Approximation of what the user said." },
              phoneticExpected: { type: Type.STRING, description: "Correct IPA or phonetic spelling." },
              explanation: { type: Type.STRING, description: "Brief error description." }
            },
            required: ["word", "isCorrect"]
          }
        }
      },
      required: ["overallScore", "wordBreakdown", "coachNotes", "specificFixes"]
    };

    // Switched to gemini-2.5-flash for significantly faster inference
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: {
        parts: [
          {
            inlineData: {
              mimeType: mimeType, // Pass the actual MIME type of the recording
              data: base64Audio
            }
          },
          {
            text: `Act as a strict American Dialect Coach. Analyze this audio recording of a student reading the following text: "${referenceText}". 
            
            CRITICAL INSTRUCTION: Your response MUST include a 'wordBreakdown' entry for EVERY SINGLE WORD in the reference text, in the exact order they appear. Do not skip any words.
            
            1. Compare the audio strictly against the text.
            2. Identify mispronunciations, rhythm issues, and stress errors.
            3. Return a JSON response matching the schema provided.`
          }
        ]
      },
      config: {
        responseMimeType: "application/json",
        responseSchema: schema
      }
    });

    if (!response.text) throw new Error("No response from Gemini");

    return JSON.parse(response.text) as AnalysisResult;

  } catch (error) {
    console.error("Analysis failed:", error);
    // Return dummy data if API fails to avoid app crash
    return {
      overallScore: 0,
      phonemeAccuracy: 0,
      flowRhythmScore: 0,
      coachNotes: "We couldn't process your audio clearly. Please ensure your microphone is working and try again.",
      specificFixes: ["Try recording in a quieter environment."],
      problemWords: [],
      wordBreakdown: referenceText.split(' ').map(w => ({ word: w, isCorrect: true }))
    };
  }
};

// Switched default voice to Puck for potentially better clarity on short words
export const generateTTS = async (text: string, voiceName: 'Kore' | 'Puck' | 'Fenrir' | 'Charon' = 'Puck'): Promise<string | null> => {
  const cacheKey = generateCacheKey(text, voiceName);
  const cached = getCachedAudio(cacheKey);
  if (cached) return cached;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-preview-tts',
      contents: { parts: [{ text }] },
      config: {
        responseModalities: ['AUDIO'],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName }
          }
        }
      }
    });

    const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (!base64Audio) return null;

    // Convert Base64 to Uint8Array
    const binaryString = atob(base64Audio);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // Wrap raw PCM in WAV header so standard players can play it
    const wavBuffer = addWavHeader(bytes, 24000, 1);
    const blob = new Blob([wavBuffer], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);

    // Save to cache
    cacheAudio(cacheKey, url);

    return url;

  } catch (error) {
    console.error("TTS generation failed:", error);
    return null;
  }
};