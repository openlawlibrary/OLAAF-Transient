chrome.browserAction.onClicked.addListener(function(tab) {
    chrome.tabs.executeScript({
        file:'lib/jsalert.min.js'
    }, 
    function() {
    // Guaranteed to execute only after the previous script returns
         chrome.tabs.executeScript({
            file: "authenticate.js"
        });
    });
});