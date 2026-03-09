
document.addEventListener("DOMContentLoaded", function() {

    const chatbotBtn = document.getElementById("chatbot-button");
    const chatbotBox = document.getElementById("chatbot-box");
    const closeChat = document.getElementById("close-chat");
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    // Track if welcome message has been shown
    let welcomeShown = false;

    chatbotBtn.onclick = () => {
        chatbotBox.style.display = "flex";

        if (!welcomeShown) {
            chatMessages.innerHTML = ""; // clear chat
            setTimeout(() => {
                addMessage("Hi there! How can I help you today?", false);
            }, 500);
            welcomeShown = true;
        }
    };

    closeChat.onclick = () => chatbotBox.style.display = "none";

    sendBtn.onclick = sendMessage;

    chatInput.addEventListener("keypress", function(e) {
        if(e.key === "Enter") sendMessage();
    });

    async function sendMessage() {

        let message = chatInput.value.trim();
        if (!message) return;

        // User message
        addMessage(message, true);

        chatInput.value = "";

        // SHOW typing animation
        showTyping();

        try {
            let response = await fetch("/chatbot-api/", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: message})
            });

            let data = await response.json();

            // HIDE typing animation
            hideTyping();

            // AI response
            addMessage(data.reply, false);

        } catch (err) {

            hideTyping();
            addMessage("Oops! Something went wrong.", false);
            console.error(err);

        }
    }

        function addMessage(text, isUser) {

        const messageDiv = document.createElement("div");
        messageDiv.textContent = text;

        if(isUser){
            messageDiv.classList.add("user-message");
        } else {
            messageDiv.classList.add("bot-message");
        }

        chatMessages.appendChild(messageDiv);

        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: "smooth"
        });
    }
});

function showTyping(){
    document.getElementById("typing-indicator").style.display = "block";
}

function hideTyping(){
    document.getElementById("typing-indicator").style.display = "none";
}

