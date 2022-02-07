let stopDivKey = "stops"
let stopButtonClass = "stop-toggle"

let performanceDivKey = "performance-details"
let performanceButtonClass = "performance-toggle"

function assignOnclickBehaviour(className, divKey, text) {
    console.log(className.length)
    let elements = document.getElementsByClassName(className)
    for (let element of elements) {
        console.log(element.id)
        let id = element.id.substring(className.length + 1)
        element.onclick = function (e) {
            console.log(`hello ${id}!`)
            let section = document.getElementById(`${divKey}-${id}`)
            if (section.style.display === "none") {
                section.style.display = "flex"
                element.innerText = `Hide ${text}`
            } else {
                section.style.display = "none"
                element.innerText = `Show ${text}`
            }
        }
    }
}

assignOnclickBehaviour(stopButtonClass, stopDivKey, "stops")
assignOnclickBehaviour(performanceButtonClass, performanceDivKey, "performance")
