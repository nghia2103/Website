document.addEventListener('DOMContentLoaded', () => {
    const chatIcon = document.getElementById('chatIcon');
    const chatBox = document.getElementById('chatBox');
    const chatBubble = chatIcon ? chatIcon.querySelector('.chat-bubble') : null;
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    const messageList = document.getElementById('messageList');
    const chatWindow = document.querySelector('.chat-window');

    if (!chatIcon || !chatBox || !sendButton || !messageInput || !messageList || !chatWindow) {
        console.error('Không tìm thấy các phần tử chatbox');
        return;
    }

    let userId = null;
    let senderName = 'User';
    let lastMessageNum = 0;
    let pollingInterval = null;

    // Đảm bảo chatBox ẩn khi khởi tạo
    chatBox.style.display = 'none';
    console.log('Khởi tạo: chatBox đã ẩn (display: none)');

    // Lấy customer_id và thông tin user
    fetch('/get_customer_id', { credentials: 'include' })
        .then(response => {
            if (!response.ok) throw new Error('Chưa đăng nhập');
            return response.json();
        })
        .then(data => {
            userId = data.customer_id;
            return fetch('/api/user');
        })
        .then(response => response.json())
        .then(userData => {
            senderName = `${userData.first_name} ${userData.last_name}`;
            initializeChat();
        })
        .catch(error => {
            console.error('Lỗi khởi tạo chat:', error);
            chatBox.style.display = 'none';
            chatIcon.style.display = 'none';
        });

    function initializeChat() {
        chatIcon.addEventListener('click', () => {
            const isVisible = chatBox.style.display === 'flex';
            chatBox.style.display = isVisible ? 'none' : 'flex';
            if (chatBubble) chatBubble.classList.toggle('active', !isVisible);
            console.log(`Nhấp chatIcon: chatBox display = ${chatBox.style.display}`);
            if (!isVisible) {
                console.log('Mở chatbox, tải tin nhắn');
                loadMessages(true);
                startPolling();
            } else {
                console.log('Đóng chatbox, dừng polling');
                stopPolling();
            }
        });

        function loadMessages(fullLoad = false) {
            fetch(`/user_messages/${userId}`, { credentials: 'include' })
                .then(response => {
                    if (!response.ok) throw new Error(`Lỗi tải tin nhắn: ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    if (!data.success) throw new Error(data.message);
                    const messages = data.messages;
                    console.log('Tin nhắn từ server:', messages);
                    if (fullLoad) {
                        messageList.innerHTML = '';
                        lastMessageNum = 0;
                    }
                    if (messages.length === 0) {
                        console.log('Không có tin nhắn');
                        return;
                    }
                    messages.forEach(msg => {
                        const messageNum = parseInt(msg.message_id.replace('MS', ''));
                        if (!lastMessageNum || messageNum > lastMessageNum) {
                            addMessageToList(msg);
                            lastMessageNum = messageNum;
                        }
                    });
                    chatWindow.scrollTop = chatWindow.scrollHeight;
                })
                .catch(error => console.error('Lỗi tải tin nhắn:', error));
        }

        function addMessageToList(msg) {
            const existingMessage = document.querySelector(`li[data-message-id="${msg.message_id}"]`);
            if (existingMessage) {
                console.log(`Tin nhắn ${msg.message_id} đã tồn tại`);
                return;
            }

            console.log('Thêm tin nhắn:', msg);

            const li = document.createElement('li');
            li.dataset.messageId = msg.message_id;
            const displayName = msg.sender_name || (msg.direction === 'user_to_admin' ? senderName : 'Admin');
            li.textContent = `${displayName}: ${msg.content} (${msg.time})`;
            li.style.backgroundColor = msg.direction === 'user_to_admin' ? '#d1e7dd' : '#f8d7da';
            li.style.marginBottom = '5px';
            li.style.padding = '8px';
            li.style.borderRadius = '8px';
            li.style.maxWidth = '70%';
            li.style.alignSelf = msg.direction === 'user_to_admin' ? 'flex-end' : 'flex-start';
            li.style.marginLeft = msg.direction === 'user_to_admin' ? 'auto' : '10px';
            li.style.marginRight = msg.direction === 'user_to_admin' ? '10px' : 'auto';
            li.style.display = 'block';
            li.style.visibility = 'visible';
            messageList.appendChild(li);
            console.log(`Thêm tin nhắn thành công: ${msg.message_id}`);
        }

        function sendMessage() {
            const content = messageInput.value.trim();
            if (!content) return;

            fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    user_id: userId,
                    admin_id: null,
                    direction: 'user_to_admin',
                    content: content
                })
            })
            .then(response => {
                if (!response.ok) throw new Error(`Lỗi tin nhắn: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const tempMsg = {
                        message_id: data.message_id,
                        sender_name: senderName,
                        content: content,
                        time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
                        direction: 'user_to_admin'
                    };
                    addMessageToList(tempMsg);
                    lastMessageNum = parseInt(data.message_id.replace('MS', ''));
                    chatWindow.scrollTop = chatWindow.scrollHeight;
                } else {
                    console.error('Lỗi nhận phản hồi từ server:', data.message);
                }
            })
            .catch(error => console.error('Lỗi gửi tin nhắn:', error));

            messageInput.value = '';
        }

        function startPolling() {
            if (pollingInterval) clearInterval(pollingInterval);
            pollingInterval = setInterval(() => {
                if (chatBox.style.display === 'flex') {
                    console.log('Polling tin nhắn mới');
                    loadMessages();
                }
            }, 2000);
        }

        function stopPolling() {
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});