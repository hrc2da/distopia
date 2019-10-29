import {DistopiaInterface} from"./distopiaInterface.js";
import {UI_CONSTANTS} from "./distopiaElements.js";

const METRICS = Object.keys(UI_CONSTANTS);

// current State of the data - not to be confused with the state ex: Wisconsin
// for metric Focus instead of string we want to type it as a union instead of any string
/** 
* @typedef {{
	*		blocks: {Number: Array<Array<Number>>},
	*		packetCount: Number,
	*		metricFocus: string,
	*       centroids: {"id": Number}
	*	}}
	*/
var State = {
	"blocks": {},
	"packetCount": null,
	// TODO - figure out why this cannot be set to empty string
	 "metricFocus": "population",
	 "centroids": {},
}

// initializations
var distopia = new DistopiaInterface({initialView: "state", "metricFocus": State.metricFocus});
initInteractive();
initState();

function updateState(newState){
	if (State.metricFocus != newState.metricFocus){
		// do something 
		distopia.handleCommand({"cmd": "focus_state", "param": newState.metricFocus});
	}
	if (State.blocks != newState.blocks){
		d3.json('http://localhost:5000/evaluate', {
      	method:"POST",
      	body: JSON.stringify({
		  "blocks": newState.blocks,
		  "packet_count": newState.packetCount
      	}),
      	headers: {
        "Content-type": "application/json; charset=UTF-8"
      	}
		})
		.then((data) =>{
			distopia.handleData({data: JSON.stringify(data)});
		})
	}
	State = newState;
}

function initInteractive(){
    const centroidAddButton = document.getElementById("add_centroid");
    centroidAddButton.onclick = () => addCentroid();

    const metricSelector = document.getElementById("metric_selector");
    metricSelector.onchange = () => {
        console.log('selector changed');
        const newSelectedMetric = document.getElementById("metric_selector").value;
        console.log(newSelectedMetric);
        updateState({
            "blocks": State.blocks,
            "packetCount": State.packetCount,
			"metricFocus": newSelectedMetric,
			"centroids": State.centroids,
        });
	}
	// add options for the metric filter
    for (let i = 0; i < METRICS.length; i++){
        const option = document.createElement("option");
        option.text = METRICS[i];
        metricSelector.options.add(option, i);
    }
    metricSelector.value = "population";
}

function initState(){
	// currently set with a hardcoded state
	updateState({
		"blocks": {
			0: [[263,678],[261,330]],
			1: [[603,206],[708,188]],
			2: [[765,385],[588,430],[488,530]],
			3: [[473,185],[383,530],[375,640],[505,356]],
			4: [[755,576],[838,371]],
			5: [[733,113],[483,46]],
			6: [[818,26]],
			7: [[823,135]]
			},
		"packetCount": 0,
		"metricFocus": "population",
		"centroids": {}
		}
	);
}

// centroid logic:
function addCentroid(){
	const stateDiv = d3.select("#state");
	const {height,width, xScale, yScale} = distopia.stateView;
	stateDiv.append("text").attr("class", "dist_label")
	.attr("x", xScale(height/2))
	.attr("y", yScale(width/2))
	.attr("id", "marker1")
	.text(1)
	.call(d3.drag().on("start", () => { d3.select('#marker1').classed("dragging", true); d3.event.on("end", () =>{d3.select("#marker1").attr("x",d3.event.x).attr("y",d3.event.y);})}));//))
}
