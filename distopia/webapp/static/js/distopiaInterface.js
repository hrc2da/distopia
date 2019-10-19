/*
	DistopiaInterface
	=================
	The main controller for the Distopia HUD
*/

import {DistrictView} from "./districtView.js";
import {StateView} from "./stateView.js";

var MIN_X, MIN_Y, MAX_X, MAX_Y;

// current State of the data - not to be confused with the state ex: Wisconsin
// for metric Focus instead of string we want to type it as a union instead of any string
/** 
* @typedef {{
	*		blocks: {Number: Array<Array<Number>>},
	*		packetCount: Number,
	*		metricFocus: string,
	*	}}
	*/
var State = {
	"blocks": {},
	"packetCount": null,
	// TODO - figure out why this cannot be set to empty string
 	"metricFocus": "population"
}


function updateState(newState){
	// need to add in some kind of hashing
	console.log(newState);
	console.log(State);
	if (State != newState){
		State = newState;
		d3.json('http://localhost:5000/evaluate', {
      	method:"POST",
      	body: JSON.stringify({
		  "blocks": State.blocks,
		  "packet_count": State.packetCount
      	}),
      	headers: {
        "Content-type": "application/json; charset=UTF-8"
      	}
		})
		.then((data) =>{
			distopia.handleData({data: JSON.stringify(data)});
			console.log(data);
		})
	}
}

// used for autobinding
var SELF;
// used to toggle off TUI settings
const isWebApp = true;

export class DistopiaInterface{
	/*
		This class interfaces between the TUI and the HUD.$
		It contains the ROS initialization and listener callbacks
		It also initializes the state and district views.						
	*/
	constructor(initialView = "state"){
		this.districtIDs = [0, 1, 2, 3, 4, 5, 6, 7];
		this.counter = 0;
		this.districts = [];
		this.counties = [];
		if (! isWebApp){
			this.initRosBridge();
			this.initDataListener();
			this.initControlListener();
		}
		this.setupCounties();
		this.initInteractive();

		SELF = this;

		//initializes stateView and districtView classes as null variables
		//(easy way to check if they need to be initialized)
		this.stateView = new StateView(null, State.metricFocus, this.counties);
		//this.districtView = new DistrictView(null);

		this.currentView = initialView;
		console.log(this.currentView);

		if(initialView == "state"){
			$("#district-view").hide();
			$("#state-view").show();
		}
		else{
			$("#state-view").hide();
			$("#district-view").show();
		}
	}

	initRosBridge(){
		this.ros = new ROSLIB.Ros({
			//url: 'ws://daarm.ngrok.io'
			url: 'ws://localhost:9090'
		});
		
		this.ros.on('connection', function(){
			console.log("Connected to ROS bridge");
		});
		
		this.ros.on('error', function(error){
			console.log('Error connecting to websocket server: ', error);
		});
		
		this.ros.on('close', function() {
			console.log('Connection to websocket server closed.');
		});
	}

	initDataListener(){
		this.dataListener = new ROSLIB.Topic({
			ros: this.ros,
			name: '/evaluated_designs',
			messageType : 'std_msgs/String'
		});
		console.log("starting data listening");
		this.dataListener.subscribe(this.handleData);
	}

	initControlListener(){
		this.controlListener = new ROSLIB.Topic({
			ros: this.ros,
			name: '/tuio_control',
			messageType : 'std_msgs/String'
		});
		this.controlListener.subscribe(this.handleCommand);
	}

	initInteractive(){
		const updateButton = document.getElementById("test_button");
		updateButton.onclick = () => this.listener();
	}

	updateView(data){
		this.counter = messageData.counter;
		this.districts = messageData.districts;
		if(this.getView() == "state"){
			//console.log("handling for state");
			this.stateView.update(this.districts);
		}
		else{
			console.log("handling for district");
			this.districtView.update(this.districts);
		}
	}

	handleData(message){
		//check the counter
		const messageData = JSON.parse(message.data);
		if(messageData.count <= SELF.counter){
			return;
		}
		SELF.counter = messageData.count;
		SELF.districts = messageData.districts;
		console.log(messageData);
		if(SELF.getView() == "state"){
			if(SELF.stateView == null){ SELF.stateView = new StateView(SELF.districts); }
			else{ SELF.stateView.update(SELF.districts); }
		}
		else{
			if(SELF.districtView == null){ SELF.districtView = new DistrictView(SELF.districts); }
			else{ SELF.districtView.update(SELF.districts); }
		}
	}

	handleCommand(message){
		//console.log("Got Command:",message);
		const messageData = JSON.parse(message.data);
		if(messageData.cmd == "focus_state"){
			if(SELF.stateView.getMetricFocus() != messageData.param){
				SELF.stateView.update(SELF.districts,messageData.param);	
			}
			if(SELF.getView() != "state"){
				SELF.toggleView();
			}
		}
		else{
			SELF.districtView.setDistrictFocus(messageData.district) //this may not be right
			if(SELF.getView() != "district"){
				SELF.toggleView();
			}
		}

	}

	setupCounties(){
		let self = this;
		d3.json("static/data/records.json").then(function(data){
			data.forEach(function(county){
				self.counties.push({
					id: county[0],
					name: county[3],
					boundaries: null,
					x: [null, null],
					y: [null, null],
					fill: "white"
				});
			});
		});
		d3.json("static/data/polygons.json").then(function(data){
			for(var i = 0; i < data.length; i++){
				self.counties[i].boundaries = data[i][0];
				self.counties[i].x[0] = d3.min(self.counties[i].boundaries, function(countyPoint){
					return countyPoint[0];
				});
				self.counties[i].x[1] = d3.max(self.counties[i].boundaries, function(countyPoint){
					return countyPoint[0];
				});
				self.counties[i].y[0] = d3.min(self.counties[i].boundaries, function(countyPoint){
					return countyPoint[1];
				});
				self.counties[i].y[1] = d3.max(self.counties[i].boundaries, function(countyPoint){
					return countyPoint[1];
				});
			}
			MIN_X = d3.min(self.counties, function(county){
				return d3.min(county.boundaries, function(countyPoint){
					return countyPoint[0];
				});
			});
			MIN_Y = d3.min(self.counties, function(county){
				return d3.min(county.boundaries, function(countyPoint){
					return countyPoint[1];
				});
			});
			MAX_X = d3.max(self.counties, function(county){
				return d3.max(county.boundaries, function(countyPoint){
					return countyPoint[0];
				});
			});
			MAX_Y = d3.max(self.counties, function(county){
				return d3.max(county.boundaries, function(countyPoint){
					return countyPoint[1];
				});
			});
			self.stateView.setBounds(MIN_X, MIN_Y, MAX_X, MAX_Y);
			//initateStateView();
		});
	}

	// callback function for interactive events
	listener(){
		// currently a hard-coded state update
		const newState = {
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
			"metricFocus": "population"
			};
		updateState(newState);
	}

	toggleView(){
		if(this.currentView == "state"){
			$("#district-view").hide();
			$("#state-view").show();
			this.currentView = "district";
		}
		else{
			$("#state-view").hide();
			$("#district-view").show();

			this.currentView = "state";
		}
	}
	
	modifyCounty(id, data){
		if(this.counties[id] != null){
			this.counties[id] = data;
			return true;
		}
		else{
			return false;
		}
	}
	
	//first call getCounty id and then modify
	getCounty(id){
		if(this.counties[id] != null){
			return this.counties[id];
		}
		else { return false; }
	}

	getView(){
		return this.currentView;
	}

	setView(v){
		this.currentView = v;
		return this.currentView;
	}
	
	getCounties(){
		return this.counties;
	}
}

export var distopia = new DistopiaInterface();

// TODO - figure out if this is needed
$(".button").click(() =>{
	distopia.toggleView();
});