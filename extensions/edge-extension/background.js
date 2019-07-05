browser.browserAction.onClicked.addListener(() => {
  browser.tabs.executeScript({
    file:'lib/jsalert.min.js'
  }, function() {
      // Guaranteed to execute only after the previous script returns
      browser.tabs.executeScript({
        file: "authenticate.js",
        allFrames: true
      });
  });
});

