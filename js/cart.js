function addSkuToCart(sku) {
    Channel.postMessage(`cart://add?sku=${sku}`);
}