/**
 * Cleanup CSP nonce meta tag after use
 */
const nonceMetaTag = document.querySelector("meta[name='nonce']");
if (nonceMetaTag) nonceMetaTag.remove();
