const btnBackToTop = document.querySelector("#btn_back_to_top");

function toggleScrollTop() {
  if (!btnBackToTop) return;

  const shouldShow = window.scrollY > 100;
  btnBackToTop.classList.toggle("opacity-0", !shouldShow);
  btnBackToTop.classList.toggle("invisible", !shouldShow);
  btnBackToTop.classList.toggle("opacity-100", shouldShow);
  btnBackToTop.classList.toggle("visible", shouldShow);
}

if (btnBackToTop) {
  btnBackToTop.addEventListener("click", (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

window.addEventListener("load", toggleScrollTop);
document.addEventListener("scroll", toggleScrollTop);
