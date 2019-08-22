content = new XMLSerializer().serializeToString(document)
href = window.location.href
url = new URL(href).pathname

var xhr = new XMLHttpRequest();
xhr.open("POST", 'http://localhost:8000/_api/authenticate', true);

if (href.endsWith('.pdf')){
  JSAlert.alert("Validation initiated...").dismissIn(1000 * 3);
  var request = new XMLHttpRequest();
  request.open('GET', href, true);
  request.responseType = 'blob'
  request.send(null);
  request.onreadystatechange = function () {
    if (request.readyState === 4 && request.status === 200) {
      blob = request.response
      if (blob != null){
        if (blob instanceof File){
          //Unlike Chrome, Firefox can't send this object
          //Since pdfs which can be authenticated (for now) are not instances of File
          //say that authentication cannot be performed.
          //TODO Convert to blob, send to server
          JSAlert.alert('Cannot authenticate')
          return
        }
        xhr.onreadystatechange = function() {
          if (xhr.readyState == 4) {
            JSAlert.alert(`${href}<br/><br/>${xhr.responseText}`)
            }
          }
          var formData = new FormData();
          formData.append('content', blob);
          formData.append('url', url)
          xhr.send(formData);
      }
    }
  }
}
else{

  content = encodeURIComponent(content)
  params = `url=${url}&content=${content}`
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.onreadystatechange = function() {
    if (xhr.readyState == 4) {
      JSAlert.alert(`${href}<br/><br/>${xhr.responseText}`)
    }
  }
  xhr.send(params);
}
