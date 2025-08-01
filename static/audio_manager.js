/**
 * Audio Manager for lazy loading and caching audio files
 * Optimizes performance by loading audio files only when needed
 */
class AudioManager {
    constructor() {
        this.audioCache = new Map();
        this.loadingPromises = new Map();
        this.manifest = null;
        this.baseUrl = '/audio';
    }

    /**
     * Initialize the audio manager with manifest data
     */
    async initialize() {
        try {
            const response = await fetch('/audio/manifest.json');
            this.manifest = await response.json();
            console.log('🎵 Audio manifest loaded:', this.manifest);
        } catch (error) {
            console.warn('⚠️ Could not load audio manifest:', error);
        }
    }

    /**
     * Get audio file with lazy loading
     */
    async getAudio(category, filename) {
        const cacheKey = `${category}/${filename}`;
        
        // Return cached audio if available
        if (this.audioCache.has(cacheKey)) {
            return this.audioCache.get(cacheKey);
        }

        // Return existing loading promise if already loading
        if (this.loadingPromises.has(cacheKey)) {
            return this.loadingPromises.get(cacheKey);
        }

        // Create new loading promise
        const loadingPromise = this.loadAudioFile(category, filename);
        this.loadingPromises.set(cacheKey, loadingPromise);

        try {
            const audio = await loadingPromise;
            this.audioCache.set(cacheKey, audio);
            this.loadingPromises.delete(cacheKey);
            return audio;
        } catch (error) {
            this.loadingPromises.delete(cacheKey);
            throw error;
        }
    }

    /**
     * Load audio file from server
     */
    async loadAudioFile(category, filename) {
        // Try new path first, fallback to legacy path
        const newUrl = `${this.baseUrl}/${category}/${filename}`;
        const legacyUrl = `/static/audio_files/${filename}`;
        
        return new Promise((resolve, reject) => {
            const audio = new Audio();
            
            audio.addEventListener('canplaythrough', () => {
                resolve(audio);
            }, { once: true });
            
            audio.addEventListener('error', (error) => {
                // Try legacy path if new path fails
                if (audio.src === newUrl) {
                    console.log(`🔄 Retrying with legacy path: ${legacyUrl}`);
                    audio.src = legacyUrl;
                    audio.load();
                } else {
                    reject(new Error(`Failed to load audio: ${newUrl} and ${legacyUrl}`));
                }
            }, { once: true });
            
            audio.src = newUrl;
            audio.load();
        });
    }

    /**
     * Play audio file
     */
    async playAudio(category, filename) {
        try {
            const audio = await this.getAudio(category, filename);
            await audio.play();
            return true;
        } catch (error) {
            console.error('❌ Error playing audio:', error);
            return false;
        }
    }

    /**
     * Preload specific audio files
     */
    async preloadAudios(audioList) {
        const promises = audioList.map(({ category, filename }) => 
            this.getAudio(category, filename)
        );
        
        try {
            await Promise.all(promises);
            console.log(`✅ Preloaded ${audioList.length} audio files`);
        } catch (error) {
            console.warn('⚠️ Some audio files failed to preload:', error);
        }
    }

    /**
     * Preload conversation audio files
     */
    async preloadConversation(conversationId) {
        if (!this.manifest || !this.manifest.conversations[conversationId]) {
            return;
        }

        const conversation = this.manifest.conversations[conversationId];
        const audioList = Object.keys(conversation.files).map(filename => ({
            category: 'conversations',
            filename: filename
        }));

        await this.preloadAudios(audioList);
    }

    /**
     * Clear cache to free memory
     */
    clearCache() {
        this.audioCache.clear();
        console.log('🗑️ Audio cache cleared');
    }

    /**
     * Get cache statistics
     */
    getCacheStats() {
        return {
            cachedFiles: this.audioCache.size,
            loadingFiles: this.loadingPromises.size,
            totalFiles: this.manifest ? this.manifest.total_files : 0
        };
    }

    /**
     * Get conversation audio files info
     */
    getConversationInfo(conversationId) {
        if (!this.manifest || !this.manifest.conversations[conversationId]) {
            return null;
        }

        return this.manifest.conversations[conversationId];
    }
}

// Global audio manager instance
window.audioManager = new AudioManager();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.audioManager.initialize();
});

// Enhanced play functions for backward compatibility
window.playSentenceAudio = async function(audioFile) {
    // Determine category from filename
    let category = 'conversations';
    if (audioFile.includes('_HSK')) {
        category = 'hsk_characters';
    } else if (audioFile.startsWith('story_')) {
        category = 'stories';
    }
    
    return await window.audioManager.playAudio(category, audioFile);
};

window.playConversationAudio = async function(audioFile) {
    return await window.audioManager.playAudio('conversations', audioFile);
};

window.playStoryAudio = async function(audioFile) {
    return await window.audioManager.playAudio('stories', audioFile);
}; 