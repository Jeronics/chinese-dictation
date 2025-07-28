// Minimalist Cylindrical Hanzi Carousel
class CylindricalHanziCarousel {
    constructor() {
        this.currentIndex = 0;
        this.hanziList = [];
        this.isOpen = false;
        this.createCarousel();
    }

    createCarousel() {
        // Create carousel container
        this.carousel = document.createElement('div');
        this.carousel.id = 'hanzi-carousel';
        this.carousel.className = 'hanzi-carousel';
        
        // Create carousel content - minimal version
        this.carousel.innerHTML = `
            <div class="carousel-cylinder">
                <div class="carousel-track" id="carousel-track">
                    <!-- Hanzi cards will be inserted here -->
                </div>
            </div>
            <div class="carousel-controls">
                <button class="carousel-nav carousel-prev" id="carousel-prev">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                <button class="carousel-nav carousel-next" id="carousel-next">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
            <button class="carousel-close" id="carousel-close">&times;</button>
        `;
        
        document.body.appendChild(this.carousel);
        this.bindEvents();
    }

    bindEvents() {
        // Close button
        document.getElementById('carousel-close').addEventListener('click', () => {
            this.close();
        });

        // Navigation buttons
        document.getElementById('carousel-prev').addEventListener('click', () => {
            this.prev();
        });

        document.getElementById('carousel-next').addEventListener('click', () => {
            this.next();
        });

        // Close on overlay click
        this.carousel.addEventListener('click', (e) => {
            if (e.target === this.carousel) {
                this.close();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!this.isOpen) return;
            
            switch(e.key) {
                case 'Escape':
                    this.close();
                    break;
                case 'ArrowLeft':
                    this.prev();
                    break;
                case 'ArrowRight':
                    this.next();
                    break;
            }
        });

        // Touch/swipe support
        let startX = 0;
        let endX = 0;

        this.carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
        });

        this.carousel.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            
            if (Math.abs(diff) > 50) { // Minimum swipe distance
                if (diff > 0) {
                    this.next();
                } else {
                    this.prev();
                }
            }
        });
    }

    show(hanziList) {
        this.hanziList = hanziList;
        this.currentIndex = 0;
        this.isOpen = true;
        
        this.createHanziCards();
        this.updateDisplay();
        this.carousel.classList.add('carousel-open');
    }

    close() {
        this.isOpen = false;
        this.carousel.classList.remove('carousel-open');
        this.hanziList = [];
    }

    prev() {
        if (this.hanziList.length <= 1) return;
        this.currentIndex = (this.currentIndex - 1 + this.hanziList.length) % this.hanziList.length;
        this.updateDisplay();
    }

    next() {
        if (this.hanziList.length <= 1) return;
        this.currentIndex = (this.currentIndex + 1) % this.hanziList.length;
        this.updateDisplay();
    }

    createHanziCards() {
        const track = document.getElementById('carousel-track');
        track.innerHTML = '';
        
        console.log('Creating hanzi cards for:', this.hanziList);
        
        this.hanziList.forEach((hanzi, index) => {
            const card = document.createElement('div');
            card.className = 'hanzi-card';
            card.dataset.index = index;
            
            card.innerHTML = `
                <div class="hanzi-character">${hanzi}</div>
                <div class="stroke-container" id="stroke-${index}"></div>
            `;
            
            track.appendChild(card);
            console.log(`Created card ${index} for hanzi: ${hanzi}`);
        });
        
        console.log('Total cards created:', track.children.length);
    }

    updateDisplay() {
        if (this.hanziList.length === 0) return;

        // Update card positions for cylindrical effect
        this.updateCardPositions();
        
        // Update stroke order animation
        this.updateStrokeOrder();
        
        // Update navigation buttons
        this.updateNavigation();
    }

    updateCardPositions() {
        const cards = document.querySelectorAll('.hanzi-card');
        const totalCards = cards.length;
        
        console.log('Updating card positions for', totalCards, 'cards');
        
        cards.forEach((card, index) => {
            const offset = (index - this.currentIndex + totalCards) % totalCards;
            const angle = (offset * 360) / totalCards;
            const radius = 150; // Smaller radius for better visibility
            const z = Math.cos((angle * Math.PI) / 180) * radius;
            const x = Math.sin((angle * Math.PI) / 180) * radius;
            const scale = Math.max(0.4, (z + radius) / (2 * radius)); // Higher minimum scale
            const opacity = Math.max(0.3, (z + radius) / (2 * radius)); // Higher minimum opacity
            
            console.log(`Card ${index}: x=${x}, z=${z}, scale=${scale}, opacity=${opacity}`);
            
            card.style.transform = `translateX(${x}px) translateZ(${z}px) scale(${scale})`;
            card.style.opacity = opacity;
            card.style.zIndex = Math.round(z);
        });
    }

    updateStrokeOrder() {
        const currentCard = document.querySelector(`.hanzi-card[data-index="${this.currentIndex}"]`);
        if (!currentCard) return;
        
        const strokeContainer = currentCard.querySelector('.stroke-container');
        const hanzi = this.hanziList[this.currentIndex];
        
        strokeContainer.innerHTML = '';
        
        if (typeof HanziWriter !== 'undefined') {
            // Get the actual container dimensions
            const containerRect = strokeContainer.getBoundingClientRect();
            const containerSize = Math.min(containerRect.width, containerRect.height);
            
            // Use container size with some padding
            const writerSize = Math.max(60, containerSize - 10); // Minimum 60px, with 10px padding
            
            HanziWriter.create(strokeContainer, hanzi, {
                width: writerSize,
                height: writerSize,
                showOutline: true,
                showCharacter: false,
                padding: 5,
                strokeAnimationSpeed: 1,
                delayBetweenStrokes: 200,
                strokeColor: '#ffffff',
                outlineColor: '#808080',
            }).animateCharacter();
        }
    }



    updateNavigation() {
        const prevBtn = document.getElementById('carousel-prev');
        const nextBtn = document.getElementById('carousel-next');
        
        prevBtn.style.display = this.hanziList.length <= 1 ? 'none' : 'block';
        nextBtn.style.display = this.hanziList.length <= 1 ? 'none' : 'block';
    }
}

// Initialize carousel
let hanziCarousel;

document.addEventListener('DOMContentLoaded', function() {
    hanziCarousel = new CylindricalHanziCarousel();
});

// Function to show carousel with multiple hanzi
function showHanziCarousel(hanziList) {
    if (!hanziCarousel) {
        hanziCarousel = new CylindricalHanziCarousel();
    }
    hanziCarousel.show(hanziList);
}

// Enhanced clickable hanzi function
function showStrokeOrder(hanzi) {
    console.log('showStrokeOrder called with:', hanzi);
    
    // Extract all hanzi from the correct sentence only
    let allHanzi = [hanzi];
    
    // Find the paragraph containing "Correct sentence"
    const paragraphs = document.querySelectorAll('.result p');
    for (const p of paragraphs) {
        const text = p.textContent || p.innerText;
        if (text.includes('Correct sentence:')) {
            // Extract hanzi from this specific paragraph
            const hanziRegex = /[\u4e00-\u9fff]/g;
            const extractedHanzi = text.match(hanziRegex);
            
            if (extractedHanzi && extractedHanzi.length > 0) {
                allHanzi = extractedHanzi;
                console.log('Extracted hanzi:', allHanzi);
            }
            break;
        }
    }
    
    // Show carousel with all hanzi
    console.log('Showing carousel with:', allHanzi);
    showHanziCarousel(allHanzi);
} 