let stopDivKey = "stops"

// Add behaviour to stop toggle buttons
let elements = document.getElementsByClassName("stop-toggle")
for (let element of elements) {
    let id = element.id.substring(12)
    element.onclick = function (e) {
        console.log(`hello ${id}!`)
        let stopSection = document.getElementById(`${stopDivKey}-${id}`)
        if (stopSection.style.display === "none") {
            stopSection.style.display = "block"
            element.innerText = "Show less"
        } else {
            stopSection.style.display = "none"
            element.innerText = "Show more"
        }
    }
}