function addSkuToCart(sku) {
    FlutterChannel.postMessage(`cart://add?sku=${sku}`);
}

function zoomImg(url) {
    FlutterChannel.postMessage(`zoom://image?url=${url}`);
}