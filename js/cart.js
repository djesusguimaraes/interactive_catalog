function addSkuToCart(sku) {
    Channel.postMessage(`cart://add?sku=${sku}`);
}

function zoomImg(url) {
    Channel.postMessage(`zoom://image?url=${url}`);
}