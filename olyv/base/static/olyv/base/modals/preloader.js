const modalPreloader = document.querySelector("#modal_preloader");

if (modalPreloader) {
  window.addEventListener("load", () => {
    modalPreloader.remove();
  });
}
