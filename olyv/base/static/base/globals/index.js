/**
 * Correct scrolling position upon page load for URLs containing hash links.
 */
// TODO: If there is a navigation thing, move this there
window.addEventListener("load", function (e) {
  if (window.location.hash) {
    if (document.querySelector(window.location.hash)) {
      setTimeout(() => {
        let section = document.querySelector(window.location.hash);
        let scrollMarginTop = getComputedStyle(section).scrollMarginTop;
        window.scrollTo({
          top: section.offsetTop - parseInt(scrollMarginTop),
          behavior: "smooth",
        });
      }, 100);
    }
  }
});

/**
 * Apply .scrolled class to the body as the page is scrolled down
 */
// TODO: Move this part to the header and specify it as .scrolled-checked-by-header
function toggleScrolled() {
  const selectBody = document.querySelector("body");
  const selectHeader = document.querySelector("#header");
  if (
    !!selectHeader &&
    !selectHeader.classList.contains("scroll-up-sticky") &&
    !selectHeader.classList.contains("sticky-top") &&
    !selectHeader.classList.contains("fixed-top")
  )
    return;
  window.scrollY > 100
    ? selectBody.classList.add("scrolled")
    : selectBody.classList.remove("scrolled");
}

document.addEventListener("scroll", toggleScrolled);
window.addEventListener("load", toggleScrolled);

// TODO: Go through everything modal-related below and clean up
// Store scroll position when modal opens
let scrollPosition = 0;

// Listen for modal show event
document.addEventListener("show.bs.modal", function (event) {
  // Get current scroll position
  scrollPosition = window.pageYOffset || document.documentElement.scrollTop;

  // Set the scroll position as a CSS custom property
  document.documentElement.style.setProperty(
    "--scroll-top",
    `-${scrollPosition}px`
  );
});

// Listen for modal hidden event
document.addEventListener("hidden.bs.modal", function (event) {
  // Temporarily hide scroll transition
  document.documentElement.style.scrollBehavior = "auto";

  // Set scroll position immediately (while body is still fixed)
  window.scrollTo(0, scrollPosition);

  // Remove the fixed positioning
  document.documentElement.style.removeProperty("--scroll-top");

  // Ensure scroll position is maintained
  window.scrollTo(0, scrollPosition);

  // Restore smooth scrolling after a brief delay
  setTimeout(() => {
    document.documentElement.style.scrollBehavior = "";
    scrollPosition = 0;
  }, 10);
});
