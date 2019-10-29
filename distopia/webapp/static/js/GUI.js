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
	*       selectedDistrict: Number,
	*       centroids: {"id": {"district": Number, "coordinates": [Number,Number]}},
	*	}}
	*/
var State = {
	"blocks": {},
	"packetCount": null,
	// TODO - figure out why this cannot be set to empty string
	 "metricFocus": "population",
	 "selectedDistrict": 1,
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
		console.log('backend req');
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
        const newSelectedMetric = metricSelector.value;
        updateState({
            "blocks": State.blocks,
            "packetCount": State.packetCount,
			"metricFocus": newSelectedMetric,
			"centroids": State.centroids,
			"selectedDistrict": State.selectedDistrict
        });
	}
	// add options for the metric filter
    for (let i = 0; i < METRICS.length; i++){
        const option = document.createElement("option");
        option.text = METRICS[i];
        metricSelector.options.add(option, i);
    }
	metricSelector.value = State.metricFocus;
	
	// set up district selector
	const districtSelector = document.getElementById("district_selector");
	districtSelector.onchange = () =>
	{
		const newSelectedDistrict = districtSelector.value;
		updateState({
			"blocks": State.blocks,
			"packetCount": State.packetCount,
			"metricFocus": State.metricFocus,
			"centroids": State.centroids,
			"selectedDistrict": newSelectedDistrict,
		})
	}

	// add options for the metric filter
	for (let i = 1; i < 9; i++){
		const option = document.createElement("option");
		option.text = i;
		districtSelector.options.add(option, i);
	}
	districtSelector.value = State.selectedDistrict;

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
		"selectedDistrict": 1,
		"centroids": {}
		}
	);
}

// centroid logic:
function addCentroid(){
	const stateDiv = d3.select("#state");
	const {height,width, xScale, yScale} = distopia.stateView;

	const id = "marker" + Object.keys(State.centroids).length;
	const idSelector = "#"+id;


	const endDrag = () => {
		d3.select(idSelector).attr("x", d3.event.x).attr("y", d3.event.y);
		State.centroids[id]["coordinates"] = [d3.event.x, d3.event.y];
		// check if min 8 centroids are present and if so call agent
		if (Object.keys(State.centroids).length >= 8){
			createBlocksFromCentroids();
			// console.log('has 8 centroids');
		}
	}

	stateDiv.append("text").attr("class", "dist_label")
	.attr("x", xScale(height/2))
	.attr("y", yScale(width/2))
	.attr("id", id)
	.text(State.selectedDistrict)
	.call(d3.drag().on("start", () => { 
		d3.select(idSelector).classed("dragging", true); 
		d3.event.on("drag", () =>{
			d3.select(idSelector).attr("x",d3.event.x).attr("y",d3.event.y);
		});
		d3.event.on("end", endDrag);
	}
	));
	// need to init the object before goign one level deeper
	State.centroids[id] = {};
	State.centroids[id]["district"] = State.selectedDistrict;
}

function createBlocksFromCentroids(){
	const{centroids} = State;

	const basicBlocks = {0: [], 1: [], 2:[], 3:[], 4:[], 5:[], 6: [], 7: []};
	// map centroids into the blocks
	const centroidKeys = Object.keys(centroids);
	centroidKeys.forEach(element => {
		const centroidDistrict = centroids[element].district-1;
		const centroidLeft = centroids[element].coordinates[0];
		const centroidRight = centroids[element].coordinates[1];
		console.log(centroidLeft,centroidRight);
		basicBlocks[centroidDistrict].push([centroidLeft, centroidRight])
	});
	console.log(basicBlocks);
	updateState({
		"blocks": basicBlocks,
		"packetCount": State.packetCount,
		"metricFocus": State.metricFocus,
		"selectedDistrict": State.selectedDistrict,
		"centroids": State.centroids,
	});
}