const chatBox = document.getElementById("chat-box");
const msgInput = document.getElementById("msg");
const sendBtn = document.getElementById("send");

sendBtn.onclick = async () => {
  const msg = msgInput.value.trim();
  if (!msg) return;

  // show user message
  chatBox.innerHTML += `<div class='text-right text-blue-700 my-1'>${msg}</div>`;
  msgInput.value = "";

  // send to backend
  const res = await fetch("/chatbot_api", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg })
  });
  const data = await res.json();

  // show bot reply
  chatBox.innerHTML += `<div class='text-left text-gray-700 my-1'>${data.reply}</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;
};
