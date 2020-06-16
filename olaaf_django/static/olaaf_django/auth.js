/*
  Element that holds files that are being authenticated.
 */
const fileList = document.getElementById("file-list");

/*
  Appends <li> that holds file details
 */
const appendFileItem = (file) => {
  const el = document.createElement("li");
  el.innerHTML = `<span id="${file.name}"><u>${file.name}</u></span>`;
  fileList.append(el);
};


const checkAuthenticity = async (files) => {
  const filesHashes = [];
  for (const f of files) {
    try {
      const hash = await calculateHash(f);
      filesHashes.push({ fileName: f.name, fileHash: hash });
      appendFileItem(f);
    } catch (e) {
      console.log(e.message);
    }
  }

  try {
    const authResponse = await sendCheckHashesRequest(filesHashes);
    Object.keys(authResponse).forEach((fileName) => {
      const status = authResponse[fileName];
      const fileItem = document.getElementById(status.fileName);
      fileItem.innerHTML += ` | Authentic: ${status.authentic} | Current: ${status.current}`;
    });
  } catch (e) {
    // could not authenticate file(s)
    console.log(e.message);
  }
};

/*
  Sends list of file names and hashes that should be authenticated to the server
  and returns response once received.
 */
const sendCheckHashesRequest = async (data) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const url = window.location.origin + "/_api/check-hashes";
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject("Error");
        }
      }
    };
    xhr.send(JSON.stringify(data));
  });
};

/*
  Extracts `tuf-authenticate` div element from html string.
 */
const getAuthDiv = (html) => {
  const doc = document.createElement("html");
  doc.innerHTML = html;
  const elems = doc.getElementsByClassName("tuf-authenticate");
  return elems ? elems[0].outerHTML.trim() : null;
};

/*
  Removes prefixes in links before calculating sha256 hash.
 */
const resetLocalUrls = (authDiv) => {
  const pubPrefixRe = /(\/)?_publication\/\d{4}-\d{2}(-\d{2})?(-\d{2})?/gi;
  const datePrefixRe = /(\/)?_date\/\d{4}-\d{2}-\d{2}/gi;
  return authDiv.replace(pubPrefixRe, "").replace(datePrefixRe, "");
};

/*
  Reads a content of the uploaded html file.
 */
const readHtmlFile = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      let authDiv = getAuthDiv(e.target.result);
      if (!authDiv) {
        resolve(null);
      }

      authDiv = resetLocalUrls(authDiv);
      resolve(new TextEncoder("utf-8").encode(authDiv));
    };
    reader.onerror = (e) => reject();
    reader.readAsText(file);
  });
};

/*
  Reads a content of the uploaded pdf file.
 */
const readPdfFile = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject();
    reader.readAsArrayBuffer(file);
  });
};

/*
  Perform sha256 hash for a given byte array.
 */
const sha256 = async (msgBuffer) => {
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray
    .map((b) => ("00" + b.toString(16)).slice(-2))
    .join("");
  return hashHex;
};

/*
  Calculates sha256 hash of the uploaded file depending on a file type (html/pdf).
 */
const calculateHash = async (file, _) => {
  switch (file.type) {
    case "text/html":
      return await sha256(await readHtmlFile(file));
    case "application/pdf":
      return await sha256(await readPdfFile(file));
    default:
      throw new Error(`File type ${file.type} is not supported!`);
  }
};

const preventDefaults = (e) => {
  e.preventDefault();
  e.stopPropagation();
};

/*
  DRAG - N - DROP
 */
const dropArea = document.getElementById("drop-area");

const highlight = (e) => {
  dropArea.classList.add("highlight");
};

const unhighlight = (e) => {
  dropArea.classList.remove("highlight");
};

["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});
["dragenter", "dragover"].forEach((eventName) => {
  dropArea.addEventListener(eventName, highlight, false);
});
["dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, unhighlight, false);
});

const dropFiles = (e) => {
  checkAuthenticity(e.dataTransfer.files);
};

dropArea.addEventListener("drop", dropFiles, false);
