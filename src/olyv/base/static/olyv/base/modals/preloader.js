const modalPreloader = document.querySelector("#modal_preloader");

if (modalPreloader) {
  // Remove preloader modal once page fully loads
  window.addEventListener("load", () => {
    modalPreloader.remove();
  });
}
