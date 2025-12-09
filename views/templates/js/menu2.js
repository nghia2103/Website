document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.menu2 button');
    const textSection = document.querySelector('.text-section2');
    const imageSection = document.querySelector('.image-section2 img');

    // Dữ liệu cho từng danh mục
    const contentData = {
        'COFFEES': {
            title: 'COFFEES',
            text: 'Discover the magic of coffee—crafted from premium roasted beans, bursting with bold flavors and invigorating caffeine. From silky cappuccinos to refreshing cold brews, every sip is an experience. Join us in our cozy café vibe, where rich aromas and perfect brews create moments to savor!',
            image: 'our_product_img/coffee.png'
        },
        'COLD DRINKS': {
            title: 'COLD DRINKS',
            text: 'Dive into our refreshing cold drinks! From icy cold brews to creamy frappes, each sip bursts with bold flavors and cool vibes. Perfect for chilling out or catching up with friends, our drinks bring the café experience to life!',
            image: 'our_product_img/colddrink.png'
        },
        'TEAS': {
            title: 'TEAS',
            text: 'Savor our aromatic teas—vibrant green, calming chamomile, or robust black. Served hot or iced, each sip offers a refreshing, flavorful escape perfect for any moment.',
            image: 'our_product_img/tea.png'
        },
        'YOURGUTS': {
            title: 'YOURGUTS',
            text: 'Dive into our creamy yogurts—smooth, tangy, and topped with fresh fruits or crunchy granola. A wholesome, delightful treat for a light and satisfying bite.',
            image: 'our_product_img/yourguts.png'
        },
        'FOODS': {
            title: 'FOODS',
            text: 'Enjoy our fresh, delicious foods—flaky croissants, savory sandwiches, and crisp salads. Crafted daily, they’re the ideal complement to your café visit.',
            image: 'our_product_img/foods.png'
        },
        'SPECIALS': {
            title: 'SPECIALS',
            text: 'Discover our unique specials—seasonal drinks like pumpkin spice lattes and exclusive treats like artisanal pastries. These limited-time offerings bring bold, unforgettable flavors to your café experience.',
            image: 'our_product_img/special.png'
        }
    };

    // Danh sách các danh mục để tự động chuyển
    const categories = Object.keys(contentData);
    let currentIndex = 0;
    let autoChangeInterval;

    // Hàm cập nhật nội dung và trạng thái button
    function updateContent(category) {
        // Xóa class active2 khỏi tất cả button
        buttons.forEach(btn => btn.classList.remove('active2'));
        // Thêm class active2 cho button tương ứng
        buttons.forEach(btn => {
            if (btn.textContent === category) {
                btn.classList.add('active2');
            }
        });

        // Cập nhật nội dung
        if (contentData[category]) {
            textSection.querySelector('h1').textContent = contentData[category].title;
            textSection.querySelector('p').textContent = contentData[category].text;
            imageSection.src = contentData[category].image;
        }
    }

    // Xử lý sự kiện nhấn button
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // Dừng tự động chuyển khi nhấn button
            clearInterval(autoChangeInterval);
            // Cập nhật nội dung
            const category = this.textContent;
            currentIndex = categories.indexOf(category);
            updateContent(category);
            // Khởi động lại tự động chuyển sau 5 giây
            autoChangeInterval = setInterval(autoChangeContent, 10000);
        });
    });

    // Hàm tự động chuyển nội dung
    function autoChangeContent() {
        currentIndex = (currentIndex + 1) % categories.length;
        updateContent(categories[currentIndex]);
    }

    // Khởi động tự động chuyển nội dung
    updateContent(categories[currentIndex]);
    autoChangeInterval = setInterval(autoChangeContent, 10000);
});