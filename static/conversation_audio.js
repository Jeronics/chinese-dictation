// Global state for conversation audio
let conversationAudioState = {
    isPlaying: false,
    currentIndex: 0
};

// Play individual sentence audio
function playSentenceAudio(audioFile) {
    if (!audioFile || audioFile === 'None') {
        console.error('No audio file provided');
        return;
    }
    
    // Stop any currently playing audio
    if (window.currentAudio) {
        window.currentAudio.pause();
        clearActiveStates();
    }
    
    // Use audio manager for lazy loading
    if (window.audioManager) {
        // Determine category from filename
        let category = 'conversations';
        if (audioFile.includes('_HSK')) {
            category = 'hsk_characters';
        } else if (audioFile.startsWith('story_')) {
            category = 'stories';
        }
        
        window.audioManager.playAudio(category, audioFile).then(success => {
            if (success) {
                // Find and highlight the corresponding input and play button
                const speakerCircles = document.querySelectorAll('.speaker-circle');
                speakerCircles.forEach(circle => {
                    const onclickAttr = circle.getAttribute('onclick');
                    if (onclickAttr && onclickAttr.includes(audioFile)) {
                        highlightActiveElements(circle);
                    }
                });
            }
        });
    } else {
        // Fallback to direct audio loading with multiple path attempts
        const audioPaths = [
            `/static/audio_files/conversations/${audioFile}`,
            `/static/audio_files/hsk_characters/${audioFile}`,
            `/static/audio_files/stories/${audioFile}`,
            `/audio/conversations/${audioFile}`,
            `/audio/hsk_characters/${audioFile}`,
            `/audio/stories/${audioFile}`
        ];
        
        let currentPathIndex = 0;
        
        function tryNextPath() {
            if (currentPathIndex >= audioPaths.length) {
                console.error('All audio paths failed for:', audioFile);
                clearActiveStates();
                return;
            }
            
            const currentPath = audioPaths[currentPathIndex];
            console.log(`🎵 Trying audio path: ${currentPath}`);
            
            window.currentAudio = new Audio(currentPath);
            
            // Find and highlight the corresponding input and play button
            const speakerCircles = document.querySelectorAll('.speaker-circle');
            speakerCircles.forEach(circle => {
                const onclickAttr = circle.getAttribute('onclick');
                if (onclickAttr && onclickAttr.includes(audioFile)) {
                    highlightActiveElements(circle);
                }
            });
            
            window.currentAudio.addEventListener('ended', () => {
                clearActiveStates();
            });
            
            window.currentAudio.addEventListener('error', () => {
                console.warn(`❌ Failed to load: ${currentPath}`);
                currentPathIndex++;
                tryNextPath();
            });
            
            window.currentAudio.play().catch(error => {
                console.error('Error playing sentence audio:', error);
                currentPathIndex++;
                tryNextPath();
            });
        }
        
        tryNextPath();
    }
}

// Play conversation audio - all sentences in sequence
function playFullConversationAudio() {
    // Get all audio files from the conversation
    const speakerCircles = document.querySelectorAll('.speaker-circle');
    const audioFiles = [];
    
    speakerCircles.forEach(circle => {
        const onclickAttr = circle.getAttribute('onclick');
        
        if (onclickAttr) {
            const match = onclickAttr.match(/playSentenceAudio\('([^']+)'\)/);
            
            if (match && match[1] !== 'None') {
                audioFiles.push(match[1]);
            }
        }
    });
    
    if (audioFiles.length === 0) {
        console.error('No audio files found');
        return;
    }
    

    
    // Stop any currently playing audio
    if (window.currentAudio) {
        window.currentAudio.pause();
        clearActiveStates();
    }
    
    // Initialize conversation audio state
    conversationAudioState.isPlaying = true;
    conversationAudioState.currentIndex = 0;
    
    // Update button text
    updateConversationButtonText();
    
    // Play all audio files in sequence
    playAudioSequence(audioFiles, 0);
}

// Stop conversation audio
function stopConversationAudio() {
    if (window.currentAudio) {
        window.currentAudio.pause();
        conversationAudioState.isPlaying = false;
        updateConversationButtonText();
    }
}



// Toggle play/stop conversation audio
function toggleConversationAudio() {
    if (conversationAudioState.isPlaying) {
        stopConversationAudio();
    } else {
        // Always start from the beginning when playing
        playFullConversationAudio();
    }
}

// Update conversation button text based on state
function updateConversationButtonText() {
    const playButton = document.querySelector('.play-conversation-btn');
    if (playButton) {
        if (conversationAudioState.isPlaying) {
            playButton.innerHTML = '⏹️ Stop Conversation Audio';
            playButton.onclick = stopConversationAudio;
        } else {
            playButton.innerHTML = '▶️ Play Conversation Audio';
            playButton.onclick = toggleConversationAudio;
        }
    }
}

// Initialize conversation page when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a conversation page
    const conversationChatContainer = document.querySelector('.conversation-chat-container');
    if (conversationChatContainer) {
        // Initialize the conversation button
        updateConversationButtonText();
    }
});

// Helper function to play audio files in sequence
function playAudioSequence(audioFiles, index) {
    if (index >= audioFiles.length) {
        clearActiveStates();
        conversationAudioState.isPlaying = false;
        conversationAudioState.currentIndex = 0;
        updateConversationButtonText();
        return; // Finished playing all audio
    }
    
    const audioFile = audioFiles[index];
    const audioPaths = [
        `/static/audio_files/conversations/${audioFile}`,
        `/static/audio_files/hsk_characters/${audioFile}`,
        `/static/audio_files/stories/${audioFile}`,
        `/audio/conversations/${audioFile}`,
        `/audio/hsk_characters/${audioFile}`,
        `/audio/stories/${audioFile}`
    ];
    
    let currentPathIndex = 0;
    
    function tryNextPath() {
        if (currentPathIndex >= audioPaths.length) {
            console.error('All audio paths failed for:', audioFile);
            // Continue with next audio file even if current one fails
            if (conversationAudioState.isPlaying) {
                playAudioSequence(audioFiles, index + 1);
            }
            return;
        }
        
        const currentPath = audioPaths[currentPathIndex];
        console.log(`🎵 Trying audio path: ${currentPath}`);
        
        window.currentAudio = new Audio(currentPath);
        conversationAudioState.currentIndex = index;
        
        // Find and highlight the corresponding input and play button
        const speakerCircles = document.querySelectorAll('.speaker-circle');
        speakerCircles.forEach(circle => {
            const onclickAttr = circle.getAttribute('onclick');
            if (onclickAttr && onclickAttr.includes(audioFile)) {
                highlightActiveElements(circle);
            }
        });
        
        window.currentAudio.addEventListener('ended', () => {
            clearActiveStates();
            // Play next audio file after current one ends
            if (conversationAudioState.isPlaying) {
                playAudioSequence(audioFiles, index + 1);
            }
        });
        
        window.currentAudio.addEventListener('error', () => {
            console.warn(`❌ Failed to load: ${currentPath}`);
            currentPathIndex++;
            tryNextPath();
        });
        
        window.currentAudio.play().catch(error => {
            console.error('Error playing conversation audio:', error);
            currentPathIndex++;
            tryNextPath();
        });
    }
    
    tryNextPath();
}

// Highlight active elements (input field and play button)
function highlightActiveElements(activeCircle) {
    // Clear any existing active states
    clearActiveStates();
    
    // Add active class to the circle
    activeCircle.classList.add('speaker-circle-active');
    
    // Find and highlight the corresponding input field
    const chatMessage = activeCircle.closest('.chat-message');
    const inputField = chatMessage.querySelector('.chat-input-bubble');
    if (inputField) {
        inputField.classList.add('chat-input-active');
    }
}

// Clear all active states
function clearActiveStates() {
    // Remove active classes from all elements
    document.querySelectorAll('.speaker-circle-active').forEach(circle => {
        circle.classList.remove('speaker-circle-active');
    });
    
    document.querySelectorAll('.chat-input-active').forEach(input => {
        input.classList.remove('chat-input-active');
    });
} 