const form = document.querySelector(".form-query");

const showInfo = (text) => {
  // Find the element
  const infoElement = document.querySelector("main .fetch-info");

  // Set the text
  infoElement.innerHTML = text;
};

form.addEventListener("submit", (e) => {
  e.preventDefault();

  const form = new FormData(e.target);
  const prompt = form.get("prompt");

  fetch("http://127.0.0.1:5000/generate", {
    method: "POST",
    body: JSON.stringify({
      query: prompt,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      const url = data["playlist_url"];
      showInfo(`Playlist has been created: <a href="${url}">${prompt}</a>`);
    });

  showInfo("Generating the playlist...");
});
