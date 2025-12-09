document.addEventListener('DOMContentLoaded', function() {
    const testimonialContent = document.querySelector('.testimonial-content');
    const leftArrow = document.querySelector('.nav-arrow.left-arrow');
    const rightArrow = document.querySelector('.nav-arrow.right-arrow');

    // Dữ liệu cho 5 testimonial
    const testimonials = [
        {
            quote: "Dunkies coffee is my daily ritual! The bold flavors and cozy atmosphere make every visit a delight.",
            author: "HALIT KEIGAD, FL"
        },
        {
            quote: "The cold drinks at Dunkies are a game-changer! Perfectly refreshing and bursting with flavor.",
            author: "SARAH NGUYEN, CA"
        },
        {
            quote: "I love the teas here! The herbal blends are so calming, and the vibe is always welcoming.",
            author: "LINH TRAN, NY"
        },
        {
            quote: "Dunkies' food menu is fantastic! The pastries pair so well with their espresso—pure bliss!",
            author: "JAMES PHAM, TX"
        },
        {
            quote: "The seasonal specials are always a surprise! Dunkies never fails to keep things exciting.",
            author: "EMILY VU, WA"
        }
    ];

    let currentIndex = 0;
    let autoChangeInterval;

    // Hàm cập nhật nội dung testimonial
    function updateTestimonial(index) {
        testimonialContent.querySelector('.quote').textContent = testimonials[index].quote;
        testimonialContent.querySelector('.author').textContent = testimonials[index].author;
    }

    // Xử lý sự kiện nhấn nút trái
    leftArrow.addEventListener('click', function() {
        clearInterval(autoChangeInterval); // Dừng tự động chuyển
        currentIndex = (currentIndex - 1 + testimonials.length) % testimonials.length;
        updateTestimonial(currentIndex);
        autoChangeInterval = setInterval(autoChangeTestimonial, 10000); // Khởi động lại
    });

    // Xử lý sự kiện nhấn nút phải
    rightArrow.addEventListener('click', function() {
        clearInterval(autoChangeInterval); // Dừng tự động chuyển
        currentIndex = (currentIndex + 1) % testimonials.length;
        updateTestimonial(currentIndex);
        autoChangeInterval = setInterval(autoChangeTestimonial, 10000); // Khởi động lại
    });

    // Hàm tự động chuyển testimonial
    function autoChangeTestimonial() {
        currentIndex = (currentIndex + 1) % testimonials.length;
        updateTestimonial(currentIndex);
    }

    // Khởi động tự động chuyển nội dung
    updateTestimonial(currentIndex);
    autoChangeInterval = setInterval(autoChangeTestimonial, 10000);
});