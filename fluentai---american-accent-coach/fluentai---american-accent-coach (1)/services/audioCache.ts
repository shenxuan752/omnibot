
// Simple in-memory cache for audio URLs
const audioCache = new Map<string, string>();

export const getCachedAudio = (key: string): string | undefined => {
  return audioCache.get(key);
};

export const cacheAudio = (key: string, url: string): void => {
  // If cache gets too big, clear it to prevent memory leaks (simple LRU-ish approach)
  if (audioCache.size > 100) {
    const firstKey = audioCache.keys().next().value;
    if (firstKey) audioCache.delete(firstKey);
  }
  audioCache.set(key, url);
};

export const generateCacheKey = (text: string, voice: string): string => {
  return `${text.toLowerCase()}-${voice}`;
};
