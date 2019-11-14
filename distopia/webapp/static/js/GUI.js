import {DistopiaInterface} from"./distopiaInterface.js";
import {UI_CONSTANTS, TASK_DESCRIPTIONS} from "./distopiaElements.js";

const METRICS = Object.keys(UI_CONSTANTS);

// current State of the data - not to be confused with the state ex: Wisconsin
// for metric Focus instead of string we want to type it as a union instead of any string
/** 
* @typedef {{
	*		blocks: {Number: Array<Array<Number>>},
	*		metricFocus: string,
	*       selectedDistrict: Number,
	*       centroids: {"id": {"district": Number, "coordinates": [Number,Number]}},
	*		counter: Number,
	*		centroid_counter: Number,
	*		currentTask: string,
	*/
var State = {
	"blocks": {},
	 "metricFocus": "population",
	 "selectedDistrict": 1,
	 "centroids": {},
	 "counter": 0,
	 "centroid_counter": 0,
	 "currentTask": "",
}

// Not including this instate because want to prevent entire state update code from running every 1 second
window.taskTimeLimit = 30;
window.currentTime = 0;

// initializations
var distopia = new DistopiaInterface({initialView: "state", "metricFocus": State.metricFocus});
initInteractive();
initState();
// called twice just to get the boundries to draw properly - this is a bug that needs to be fixed
initState();

initTasksAndTimers();

function updateState(newState){
	if (newState.metricFocus && State.metricFocus != newState.metricFocus){
		distopia.handleCommand({"cmd": "focus_state", "param": newState.metricFocus}).then()
		d3.selectAll(".dist_label").raise();
	}
	if (newState.blocks && State.blocks != newState.blocks){
		console.log(newState.blocks);
		let counter = State.counter;
		if (typeof(counter) == 'undefined'){
			counter = 0;
		}
		console.log("counter  =" + counter);
		d3.json('http://localhost:5000/evaluate', {
      	method:"POST",
      	body: JSON.stringify({
		  "blocks": newState.blocks,
		  "packet_count": counter,
		  "session_id": window.session_id,
      	}),
      	headers: {
        "Content-type": "application/json; charset=UTF-8"
      	}
		})
		.then((data) =>{
			newState.counter = data['count'];
			distopia.handleData({data: JSON.stringify(data)});
			d3.selectAll(".dist_label").raise();
		},(error)=>{
			if (error.message){
				// TODO - figure out how to better communicate this error
				window.alert("Centroids cannot provide valid districts.");
			}
		});
	}
	State = {...State,...newState};
}

function initInteractive(){
    const centroidAddButton = document.getElementById("state");
    centroidAddButton.onclick = (e) => addCentroid(e);

    const metricSelector = document.getElementById("metric_selector");
    metricSelector.onchange = () => updateState({"metricFocus": metricSelector.value});
	// add options for the metric filter
    for (let i = 0; i < METRICS.length; i++){
        const option = document.createElement("option");
        option.text = METRICS[i];
        metricSelector.options.add(option, i);
    }
	metricSelector.value = State.metricFocus;
	
	// set up district selector
	const districtSelector = document.getElementById("district_selector");
	districtSelector.onchange = () => updateState({"selectedDistrict": districtSelector.value});
	// keyboard shortcuts to select district
	document.onkeyup = (e) => {
		if(e.which >=49 && e.which <=56){
			let key = e.which - 48;	
			districtSelector.value = key;
			updateState({
				"selectedDistrict": key,
			})	
		}
		else{
			return;
		}
	}

	// add options for the metric filter
	for (let i = 1; i < 9; i++){
		const option = document.createElement("option");
		option.text = i;
		districtSelector.options.add(option, i);
	}
	districtSelector.value = State.selectedDistrict;

	// reset centroids button
	const resetCentroidsButton = document.getElementById("reset_centroids");
	resetCentroidsButton.onclick = () => {
		(Object.keys(State.centroids)).forEach(
			(key) => removeCentroid(key));
		initState();
	}

}


// Renders the tasks and the timer. Kicks of the timer counting down as well
function initTasksAndTimers(){
	let randomTask = () => TASK_DESCRIPTIONS[Math.floor(Math.random() * TASK_DESCRIPTIONS.length)];

	const timerDiv = d3.select("#timer");
	const taskDiv = d3.select("#task_dialog");

	taskDiv.append("text").attr("id", "task_text")
	.attr("x", 80)
	.attr("y", 60)
	.text(State.currentTask);

	timerDiv.append("text").attr("id", "task_time")
	.attr("x", 80)
	.attr("y", 80);

	let taskTime = () => setInterval(() => {
		if (window.currentTime == 0){
			updateState({currentTask: randomTask()});
			d3.select("#task_text").text(State.currentTask);
			window.currentTime = window.taskTimeLimit;
		}
		else{
			window.currentTime --;
		}
		d3.select("#task_time").text("Time Remaining: " + window.currentTime);
	}, 1000);
	
	taskTime();		
}


function initState(){
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
		"centroids": {},
		"counter": 0,
		"centroid_counter": 0
		}
	);
}


function removeCentroid(id){
	console.log("removing centroid ",id)
	d3.select("#"+id).remove();
	delete State.centroids[id];
	
	// if there are at least 8 districts with centroids
	const districtSet = new Set([]);
		(Object.keys(State.centroids)).forEach(key => {
			const district = State.centroids[key].district;
			if (!districtSet.has(district)){
				districtSet.add(district);
			}
		})
	if (districtSet.size >= 8){
		createBlocksFromCentroids();
	}
}


function addCentroid(e){
	// console.log("adding centroid");
	const stateDiv = d3.select("#state");
	const {xScale, yScale} = distopia.stateView;
	updateState({"centroid_counter": State.centroid_counter +1});
	const id = "marker" + State.centroid_counter;
	const idSelector = "#"+id;


	const endDrag = (d) => {
		// console.log("dragging");
		// console.log(d);
		// console.log(d3.event);
		if(Math.abs(d3.event.x-d.startX) < 2 && Math.abs(d3.event.y-d.startY < 2)){
			// console.log("no drag");
			return;
		}
		d3.select(idSelector).attr("x", d3.event.x).attr("y", d3.event.y);
		State.centroids[id]["coordinates"] = [xScale.invert(d3.event.x), yScale.invert(d3.event.y)];
		// check if min 8 centroids are present and if so call agent
		const districtSet = new Set([]);
		(Object.keys(State.centroids)).forEach(key => {
			const district = State.centroids[key].district;
			if (!districtSet.has(district)){
				districtSet.add(district);
			}
		})
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
	.on("click", () => { 
		d3.event.stopPropagation(); 
		removeCentroid(id);
	})
	.call(d3.drag().on("start", () => { 
		var d = {};
		// TODO - live dragging
		var updateCounter = 0;
		d.startX = d3.event.x;
		d.startY = d3.event.y;
		d3.select(idSelector).classed("dragging", true); 
		d3.event.on("drag", () =>{
			d3.select(idSelector).attr("x",d3.event.x).attr("y",d3.event.y);
			// TODO - live dragging
			// updateCounter = (updateCounter+1) % 500;
			// if (updateCounter == 0){
			// 	endDrag(d);
			// }
		});
		d3.event.on("end", () => endDrag(d));
	}
	));

	State.centroids[id] = {};
	State.centroids[id]["district"] = State.selectedDistrict;
	State.centroids[id]["coordinates"] = [xScale.invert(e.offsetX),yScale.invert(e.offsetY)];

	const districtSet = new Set([]);
		(Object.keys(State.centroids)).forEach(key => {
			const district = State.centroids[key].district;
			if (!districtSet.has(district)){
				districtSet.add(district);
			}
		})
	if (districtSet.size >= 8){
		createBlocksFromCentroids();
	}
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
	updateState({"blocks": basicBlocks});
}