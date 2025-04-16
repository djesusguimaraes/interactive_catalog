function addToCartBySku(sku) {
    FlutterChannel.postMessage(`cart://add?sku=${sku}`);
}

function addToCartByText(text) {
    FlutterChannel.postMessage(`cart://add?text=${text}`);
}

function addToCartByVariations(variations) {
    FlutterChannel.postMessage(`cart://add?variations=${variations}`);
}

function zoomImg(url) {
    FlutterChannel.postMessage(`zoom://image?url=${url}`);
}