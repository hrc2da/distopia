import {DistopiaInterface} from"./distopiaInterface.js";
import {UI_CONSTANTS} from "./distopiaElements.js";

const METRICS = Object.keys(UI_CONSTANTS);

// current State of the data - not to be confused with the state ex: Wisconsin
// for metric Focus instead of string we want to type it as a union instead of any string
/** 
* @typedef {{
	*		blocks: {Number: Array<Array<Number>>},
	*		metricFocus: string,
	*       selectedDistrict: Number,
	*       centroids: {"id": {"district": Number, "coordinates": [Number,Number]}},
	*	}}
	*/
var State = {
	"blocks": {},
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
		d3.selectAll(".dist_label").raise();
	}
	if (State.blocks != newState.blocks){
		console.log('backend req');
		console.log(newState.blocks);
		d3.json('http://localhost:5000/evaluate', {
      	method:"POST",
      	body: JSON.stringify({
		  "blocks": newState.blocks,
		  "packet_count": 0,
      	}),
      	headers: {
        "Content-type": "application/json; charset=UTF-8"
      	}
		})
		.then((data) =>{
			console.log(data);
			distopia.handleData({data: JSON.stringify(data)});
			d3.selectAll(".dist_label").raise();
		})
	}
	State = newState;
}

function initInteractive(){
    const centroidAddButton = document.getElementById("state");
    centroidAddButton.onclick = (e) => addCentroid(e);

    const metricSelector = document.getElementById("metric_selector");
    metricSelector.onchange = () => {
        const newSelectedMetric = metricSelector.value;
        updateState({
            "blocks": State.blocks,
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
		"metricFocus": "population",
		"selectedDistrict": 1,
		"centroids": {}
		}
	);
}

// centroid logic:
function addCentroid(e){
	const stateDiv = d3.select("#state");
	const {height,width, xScale, yScale} = distopia.stateView;

	const id = "marker" + Object.keys(State.centroids).length;
	const idSelector = "#"+id;


	const endDrag = () => {
		d3.select(idSelector).attr("x", d3.event.x).attr("y", d3.event.y);
		State.centroids[id]["coordinates"] = [d3.event.x, d3.event.y];
		// check if min 8 centroids are present and if so call agent
		const districtSet = new Set([]);
		(Object.keys(State.centroids)).forEach(key => {
			const district = State.centroids[key].district;
			if (!districtSet.has(district)){
				districtSet.add(district);
			}
		})
		// if there are at least 8 districts with centroids
		if (districtSet.size >= 8){
			createBlocksFromCentroids();
		}
	}


	stateDiv.append("text").attr("class", "dist_label")
	.attr("x", e.offsetX)
	.attr("y", e.offsetY)
	.attr("id", id)
	.text(State.selectedDistrict)
	.style("cursor", "pointer")
	.call(d3.drag().on("start", () => { 
		d3.select(idSelector).classed("dragging", true); 
		d3.event.on("drag", () =>{
			d3.select(idSelector).attr("x",d3.event.x).attr("y",d3.event.y);
		});
		d3.event.on("end", endDrag);
	}
	))
	// need to init the object before goign one level deeper
	State.centroids[id] = {};
	State.centroids[id]["district"] = State.selectedDistrict;
	State.centroids[id]["coordinates"] = [e.x,e.y]
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
		basicBlocks[centroidDistrict].push([centroidLeft, centroidRight])
	});
	updateState({
		"blocks": basicBlocks,
		"metricFocus": State.metricFocus,
		"selectedDistrict": State.selectedDistrict,
		"centroids": State.centroids,
	});
}