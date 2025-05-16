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

function zoomFragment(page) {
    FlutterChannel.postMessage(`zoom://fragment?page=${page}`);
}

function searchDrills(size, type, bones) {
    let implantSize = `implantSize=${size}`;
    let sequencyType = `sequencyType=${type}`;
    let boneTypes = `boneTypes=${bones}`;
    let message = `zoom://drills?${[implantSize, sequencyType, boneTypes].join('&')}`;
    FlutterChannel.postMessage(message);
}

function seeSummary() {
    FlutterChannel.postMessage(`catalog://summary`);
}

function zoomContentImage(url) {
    let path = window.location.pathname.replaceAll('/src', '/assets/images').replaceAll('index.html', '');
    zoomImg(path + url);
}