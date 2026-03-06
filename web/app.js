const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const translateInput = document.getElementById("translateInput");
const saveWord = document.getElementById("saveWord");
const chatInput = document.getElementById("chatInput");
const translateBtn = document.getElementById("translateBtn");
const chatBtn = document.getElementById("chatBtn");

function sendPayload(payload) {
  if (!tg) {
    alert("Open this page inside Telegram Mini App.");
    return;
  }
  tg.sendData(JSON.stringify(payload));
}

translateBtn.addEventListener("click", () => {
  const text = translateInput.value.trim();
  if (!text) {
    translateInput.focus();
    return;
  }

  sendPayload({
    action: "translate",
    text,
    save: Boolean(saveWord.checked),
  });

  if (saveWord.checked) {
    translateInput.value = "";
  }
});

chatBtn.addEventListener("click", () => {
  const text = chatInput.value.trim();
  if (!text) {
    chatInput.focus();
    return;
  }

  sendPayload({
    action: "chat",
    text,
  });

  chatInput.value = "";
});
