/*
	districtView
	=============
	Wrapper for the district level "baseball card" view
*/
import {parseData} from './distopiaInterface.js'
import Histogram from "./viz/histogram.js";

export class DistrictView {
	constructor(districtId = 0){
		console.log("I'm a district, look at me go!");
		this.districtFocus = districtId;
		//let's instantiate all the visualizations we want to do
		//histograms for now, add these to the html as well (10 new id's, plus districtmap)
		/*
			we'll have a dict of visualizations, e.g.
			{
				"income": histogram object
			}
		*/
		//for different viz, use same structure as histogram.js
		//just instantiate it and pass the html id as a selector for that viz
		this.metricPlots = {};
		
		METRICS.forEach((metric, i) => {
			switch (METRIC_TYPE[i]){
				case "histogram":
					this.metricPlots[metric] = new Histogram("#", [], [], styles);
					break;
				case "scalar":
					break;
			}
		});
	}

	setDistrictFocus(districtId){
		this.districtFocus = districtId;
		this.currentPrecints = d.districts[this.districtFocus].precints;
		this.updateDistrictMap();
	}

	updateDistrictMap(){
		/*
			This updates the actual polygons that visualize the shape of the district we are focused on
		*/
		//get the actual polygons corresponding with precincts
		let polygons = [];
		for(let i = 0; i < this.currentPrecincts.length; i++){
			polygons.push(d.counties[this.currentPrecints[i]].boundaries);
		}
		//now draw the polygons
	}
}