function themeChange(){
  document.querySelectorAll(".section").forEach(function(e){
    ScrollTrigger.create({
      trigger: e,
      start: "top 50%",
      end: "bottom 50%",
      onEnter: function(){
        document.body.setAttribute("theme", e.dataset.color);
      },
      onEnterBack: function(){
        document.body.setAttribute("theme", e.dataset.color);
      }
    });
  });
}

// (function () {
//   const locomotiveScroll = new LocomotiveScroll();
// })();

// Initialize Marquee Animation with smooth infinite scroll
function initMarquee() {
  const marquees = document.querySelectorAll('.marquee-track');
  
  marquees.forEach((marquee, index) => {
    const items = marquee.querySelectorAll('.marquee-item');
    const isFirstRow = index === 0; // Check if it's the first row
    
    // Duplicate items for seamless looping (3 copies for smoother loop)
    const itemsArray = Array.from(items);
    for (let i = 0; i < 2; i++) { // Create 2 additional copies
      itemsArray.forEach(item => {
        const clone = item.cloneNode(true);
        marquee.appendChild(clone);
      });
    }
    
    // Get the total width of all original items
    const firstItem = items[0];
    const itemWidth = firstItem.offsetWidth + 24; // 24px gap
    const totalWidth = itemWidth * itemsArray.length;
    
    // Set initial position based on direction
    const initialX = isFirstRow ? 0 : -totalWidth;
    gsap.set(marquee, { x: initialX });
    
    // Calculate duration based on number of items (faster for more items)
    const baseDuration = 20; // Base duration in seconds for one full loop
    const duration = baseDuration * (itemsArray.length / 3); // Adjust based on number of items
    
    // Create the animation
    const tl = gsap.timeline({ 
      repeat: -1,
      defaults: { ease: 'none' }
    });
    
    // Animate the marquee
    tl.to(marquee, {
      x: isFirstRow ? `-=${totalWidth}` : `+=${totalWidth}`,
      duration: duration,
      ease: 'linear',
      modifiers: {
        x: gsap.utils.unitize(x => {
          // Reset position when reaching the end for seamless loop
          const xNum = parseFloat(x);
          const maxX = isFirstRow ? 0 : -totalWidth;
          const minX = isFirstRow ? -totalWidth * 2 : totalWidth;
          
          if (isFirstRow && xNum <= -totalWidth) {
            return 0;
          } else if (!isFirstRow && xNum >= 0) {
            return -totalWidth;
          }
          return xNum;
        })
      }
    });
    
    // Pause on hover with smooth transition
    const container = marquee.closest('.marquee-container');
    container.addEventListener('mouseenter', () => {
      gsap.to(tl, { 
        timeScale: 0.3, 
        duration: 0.5,
        ease: 'power2.out'
      });
    });
    
    container.addEventListener('mouseleave', () => {
      gsap.to(tl, { 
        timeScale: 1, 
        duration: 0.5,
        ease: 'power2.inOut'
      });
    });
    
    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        tl.kill();
        initMarquee(); // Reinitialize on resize
      }, 250);
    });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  // Initialize marquee animation
  initMarquee();
  // Elements
  const videoThumbnail = document.querySelector('.video-thumbnail');
  const videoModal = document.querySelector('.video-modal');
  const closeButton = document.querySelector('.close-button');
  const modalVideo = document.getElementById('modal-video');
  const cursorDot = document.querySelector('.cursor-dot');
  const cursorText = document.querySelector('.cursor-dot-fill');
  
  if (!videoThumbnail) return;

  const moveCursor = (e) => {
    const mouseX = e.clientX;
    const mouseY = e.clientY;
    
    gsap.to(cursorDot, {
      x: mouseX,
      y: mouseY,
      duration: 0.1,
      ease: 'power1.out'
    });
  };

  videoThumbnail.addEventListener('mouseenter', () => {
    cursorDot.classList.add('active');
    document.body.style.cursor = 'none';
  });

  videoThumbnail.addEventListener('mouseleave', () => {
    cursorDot.classList.remove('active');
    document.body.style.cursor = 'auto';
  });

  document.addEventListener('mousemove', moveCursor);

  videoThumbnail.addEventListener('click', (e) => {
    e.preventDefault();
    videoModal.classList.add('active');
    document.body.classList.add('modal-open');
    cursorDot.classList.remove('active');
    
    setTimeout(() => {
      modalVideo.play().catch(error => {
        console.error('Error playing video:', error);
      });
    }, 300);
    
    gsap.fromTo(
      videoModal.querySelector('.relative'),
      { y: 50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.5, ease: 'power2.out' }
    );
  });

  closeButton.addEventListener('click', (e) => {
    e.stopPropagation();
    modalVideo.pause();
    videoModal.classList.remove('active');
    document.body.classList.remove('modal-open');
  });

  videoModal.addEventListener('click', (e) => {
    if (e.target === videoModal) {
      modalVideo.pause();
      videoModal.classList.remove('active');
      document.body.classList.remove('modal-open');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && videoModal.classList.contains('active')) {
      modalVideo.pause();
      videoModal.classList.remove('active');
      document.body.classList.remove('modal-open');
    }
  });

  const thumbnailVideo = videoThumbnail.querySelector('video');
  if (thumbnailVideo) {
    thumbnailVideo.muted = true;
    
    const playPromise = thumbnailVideo.play();
    
    if (playPromise !== undefined) {
      playPromise.catch(error => {
        console.log('Autoplay prevented, showing fallback UI');
      });
    }
  }
});


themeChange();

