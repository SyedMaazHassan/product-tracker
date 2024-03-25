var AccessPanel = document.getElementById("accessPanel");
var toggleAccessPanel = document.getElementById("toggleAccessPanel");

var fontSwap = document.getElementById("fontSwap");
var fontIncrease = document.getElementById("fontIncrease");
var fontDecrease = document.getElementById("fontDecrease");

var btnTextLighten = document.getElementById("contrastTextLighten");
var btnTextDarken = document.getElementById("contrastTextDarken");
var btnBgLighten = document.getElementById("contrastBgLighten");
var btnBgDarken = document.getElementById("contrastBgDarken");

var reset = document.getElementById("reset");

var bgColorSliders = document.getElementsByClassName("rangeBg");
var textColorSliders = document.getElementsByClassName("rangeText");

var toggleBlur = document.getElementById("toggleBlur");

function fontReplace() {
  if (document.body.classList.contains("accessible-font") == true) {
    document.body.classList.remove("accessible-font");
  } else {
    document.body.classList.add("accessible-font");
  }
}

var fontSize = 0;

function fontDec(inc) {
  var minInc = 0;
  inc--;
  if (inc <= minInc) {
    inc = minInc;
  }
  return inc;
}

function fontInc(inc) {
  inc++;
  return inc >= 4 ? 4 : inc; // shorthand version of fontDec
}

function fontRem() {
  for (var i = 0; i < document.body.classList.length; i++) {
    var className = document.body.classList[i];
    if (className.indexOf("fontsize-") >= 0) {
      document.body.classList.remove(className);
    }
  }
}

var contrastBg = [255, 255, 255];
var contrastText = [0, 0, 0];

function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

function contrastChange(target, array) {
  var valueInc = target * 51;
  for (var i = 0; i < array.length; i++) {
    var newVal = clamp(parseInt(array[i]) + valueInc, 0, 255);
    array[i] = newVal;
    if (array == contrastBg) {
      bgColorSliders[i].value = newVal;
    }
    if (array == contrastText) {
      textColorSliders[i].value = newVal;
    }
  }
}

document.addEventListener("click", function (event) {
  var el = event.target;

  if (el == reset) {
    document.body.removeAttribute("style");
    document.body.removeAttribute("class");
    contrastBg = [255, 255, 255];
    contrastText = [0, 0, 0];
    fontSize = 0;
    for (var i = 0; i < 3; i++) {
      bgColorSliders[i].value = 255;
      textColorSliders[i].value = 0;
    }
  }

  if (el == toggleAccessPanel) {
    if (!accessPanel.classList.contains("visible") == true) {
      AccessPanel.classList.add("visible");
    } else {
      AccessPanel.classList.remove("visible");
    }
  }

  if (el == fontSwap) {
    fontReplace();
  }

  if (el == fontIncrease || el == fontDecrease) {
    fontRem();
  }

  if (el == fontDecrease) {
    fontSize = fontDec(fontSize);
    document.body.classList.add("fontsize-" + fontSize);
  }

  if (el == fontIncrease) {
    fontSize = fontInc(fontSize);
    document.body.classList.add("fontsize-" + fontSize);
  }

  if (el == contrastTextLighten) {
    contrastChange(1, contrastText);
    document.body.style["color"] = "rgb(" + contrastText + ")";
  }

  if (el == contrastTextDarken) {
    contrastChange(-1, contrastText);
    document.body.style["color"] = "rgb(" + contrastText + ")";
  }

  if (el == contrastBgLighten) {
    contrastChange(1, contrastBg);
    document.body.style["background-color"] = "rgb(" + contrastBg + ")";
  }

  if (el == contrastBgDarken) {
    contrastChange(-1, contrastBg);
    document.body.style["background-color"] = "rgb(" + contrastBg + ")";
  }

  if (el == toggleBlur) {
    if (!document.body.classList.contains("blur") == true) {
      document.body.classList.add("blur");
    } else {
      document.body.classList.remove("blur");
    }
  }
});

document.addEventListener("keydown", function (event) {
  var key = event.keyCode;

  if (key == "81") {
    if (!accessPanel.classList.contains("visible") == true) {
      AccessPanel.classList.add("visible").focus();
    } else {
      AccessPanel.classList.remove("visible");
    }
  }

  // redo as switch cases
  if (key == "65") {
    fontReplace();
  }

  if (key == "68" || key == "83") {
    fontRem();
  }

  if (key == "83") {
    fontSize = fontDec(fontSize);
    document.body.classList.add("fontsize-" + fontSize);
  }

  if (key == "68") {
    fontSize = fontInc(fontSize);
    document.body.classList.add("fontsize-" + fontSize);
  }

  if (key == "90") {
    contrastChange(1, contrastText);
    document.body.style["color"] = "rgb(" + contrastText + ")";
  }

  if (key == "88") {
    contrastChange(-1, contrastText);
    document.body.style["color"] = "rgb(" + contrastText + ")";
  }

  if (key == "67") {
    contrastChange(1, contrastBg);
    document.body.style["background-color"] = "rgb(" + contrastBg + ")";
  }

  if (key == "86") {
    contrastChange(-1, contrastBg);
    document.body.style["background-color"] = "rgb(" + contrastBg + ")";
  }

  if (key == "70") {
    document.body.removeAttribute("style");
    document.body.removeAttribute("class");
    contrastBg = [255, 255, 255];
    contrastText = [0, 0, 0];
    fontSize = 0;
    for (var i = 0; i < 3; i++) {
      bgColorSliders[i].value = 255;
      textColorSliders[i].value = 0;
    }
  }
});

function bgInputValues(i) {
  contrastBg[i] = bgColorSliders[i].value;
  document.body.style.backgroundColor = "rgb(" + contrastBg.join(",") + ")";
}
function bgInputChange() {
  for (var i = 0; i < 3; i++) {
    bgInputValues(i);
  }
}
document.addEventListener("input", bgInputChange);

function textInputValues(i) {
  contrastText[i] = textColorSliders[i].value;
  document.body.style.color = "rgb(" + contrastText.join(",") + ")";
}
function textInputChange() {
  for (var i = 0; i < 3; i++) {
    textInputValues(i);
  }
}
document.addEventListener("input", textInputChange);
