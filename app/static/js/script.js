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

(function () {
  const locomotiveScroll = new LocomotiveScroll();
})();

document.addEventListener('DOMContentLoaded', function() {
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