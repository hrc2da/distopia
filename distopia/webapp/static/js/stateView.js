/*
	StateView
	==========
	A statewide view of a selected metric, with a heatmap and a set of histograms
*/
import {UI_CONSTANTS} from './distopiaElements.js'
import Histogram from "./viz/histogram.js";
import RadarChart from "./viz/radarchart.js";

var SELF;

export class StateView {
	
	constructor(initData, metricFocus = "population", counties){
		console.log(metricFocus);
		this.counties = counties;
		this.metricFocus = metricFocus;
		console.log("Initiating State View");
		this.stateDiv = d3.select("#state");
	
		this.width = parseFloat(d3.select("#state").style("width"));
		this.height = parseFloat(d3.select("#state").style("height"));
		SELF = this;

		this.xScale = null;
		this.yScale = null;

		this.MIN_X = null;
		this.MIN_Y = null;
		this.MAX_X = null;
		this.MAX_Y = null;

		this.drawn = false;
		this.drawStatePolygons();

		let max = 1;
		if(this.metricFocus == "population"){ max = 3000000; }
		this.paintRadar([0.1,0.1,0.1]);
	}

	filterByFocusMetric(data){
		let districtData = []
		data.forEach(district => {
			let d = {
				precincts: district.precincts,
				name: null,
				labels: null,
				data: null,
				scalar_value: null,
				scalar_maximum: null
			}
			district.metrics.forEach(m => {
				if(m.name == this.metricFocus){
					d.name = m.name;
					d.labels = m.labels;
					d.data = m.data;
					d.scalar_value = m.scalar_value;
					d.scalar_maximum = m.scalar_maximum;
				}
			});
			districtData.push(d);
		});
		return districtData;
	}
	
	setMetricFocus(metric){
		this.metricFocus = metric;
	}

	getMetricFocus(){
		return this.metricFocus;
	}

	setBounds(MIN_X, MIN_Y, MAX_X, MAX_Y){
		this.MIN_X = MIN_X;
		this.MIN_Y = MIN_Y;
		this.MAX_X = MAX_X;
		this.MAX_Y = MAX_Y;

		var scale = this.height/(this.MAX_Y - this.MIN_Y - 40);

		var xExtents = (this.MAX_X - this.MIN_X) * scale;
		var padding = (this.width - xExtents)/2;

		this.xScale = d3.scaleLinear().domain([MIN_X, MAX_X]).range([padding, xExtents + padding]);
		this.yScale = d3.scaleLinear().domain([MIN_Y, MAX_Y]).range([this.height - 20, 20]);
	}

	paintStateViz(){
		let state = this.stateDiv.selectAll("polygon").data(this.counties);
		state.attr("fill", function(county){
			return county.fill;
		});
	}

	paintHistograms(data){
		let max = 1;
		console.log(this.metricFocus);
		if(this.metricFocus == "population"){ max = 3000000; }
		for(var i = 0; i < this.histograms.length; i++){
			this.histograms[i].update(data[i].data, data[i].labels, {colors:UI_CONSTANTS[this.metricFocus].colors}, max);
		}
	}
	paintDashboard(data,precalculated_stats){
		if(precalculated_stats == undefined){ 
			return;
		}
		if(precalculated_stats.standardized_metrics != undefined){
			let standardized_metrics = precalculated_stats.standardized_metrics
			this.paintRadar(standardized_metrics);
		}

		// USE WHEN WE ARE INCLUDING INTENT IN THE CODE
		// if(precalculated_stats.prediction != undefined && precalculated_stats.prediction != null){
		// 	let prediction = precalculated_stats.prediction;
		// 	this.paintIntent(prediction);
		// }


	}

	paintIntent(prediction){
		console.log("painting intent");
		let svg = d3.select("#intent_dialog");
		let width = 400;//svg.attr("width");
		let height = 200;//svg.attr("height");
		let bar_width = width/3;
		let xpadding = 20;
		let ypadding = 20;
		svg.selectAll("rect").remove();
		svg.selectAll("text").remove();
		svg.selectAll(".bar").data(prediction)
			.enter().append("rect")
			.attr("x", (d,i) => xpadding + i*bar_width)
			.attr("y", (d) => {
				if(d > 0){
					return ypadding + height/2-d*height*0.5;
				}
				else{
					return ypadding + height/2;
				}
			})
			.attr("width",bar_width)
			.attr("height",(d)=> Math.abs(d)*height*0.5);
		//labels
		svg.append("text").text("Population Std")
				.attr("fill",prediction[0] > 0 ? "black" : "white")
				.attr("x",40)
				.attr("y",110);
		svg.append("text").text("Wasted Votes")
				.attr("fill",prediction[1] > 0 ? "black" : "white")
				.attr("x",170)
				.attr("y",110);
		svg.append("text").text("Compactness")
				.attr("fill",prediction[2] > 0 ? "black" : "white")
				.attr("x",300)
				.attr("y",110);
		//svg.append("text").text("Population2").attr("fill","black").attr("x",x_padding + 2*width/3).attr("y",y_padding + height/2);
		//svg.append("text").text("Population3").attr("fill","black").attr("x",x_padding + 3*width/3).attr("y",y_padding + height/2);
	}
	
	paintRadar(data){
		var radarChartOptions = {
			w: this.width*0.8,
			h: this.height*0.7,
			margin:{top: 100, right: 20, bottom: 20, left: 100}, 
			unit: '',
			format: '0.00f',
			maxValue: 100,
			levels: 5,
			labelFactor: 1.3, 
		}
		console.log("radar");
		console.log(data);
		let radarData = [
			{
				name: '',
				axes: [
					{
						axis:"Population Balance",value:this.rescale_standardized(-data[0])
					},
					{
						axis: "Voter Efficiency", value:this.rescale_standardized(-data[1])
					},
					{
						axis: "Shape Regularity", value:this.rescale_standardized(data[2])
					}
				]	
			}
		]
		RadarChart("#radar",radarData,radarChartOptions);
	}
	rescale_standardized(val){
		//rescale a z-standardized value to between 0 and 100, with 50 being the mean and the boundaries being 3 std's away
		let truncated = Math.min(val,3);
		truncated = Math.max(truncated,-3);
		return truncated*50/3 + 50;
	}
	update(data,metric,precalculated_stats){
		console.log("updating");
		//d3.selectAll(".dist_label").remove();
		d3.selectAll(".label").remove();
		d3.selectAll(".key").remove();
		//update the viz. Note that the
		if(metric != undefined){
			if(metric != this.metric){
				this.setMetricFocus(metric);
			}
		}
		if(data.length < 8){ return; }
		let bounds = [];

		data.forEach((district) => {
			bounds.push(district.boundary);
		});

		this.drawDistrictBounds(bounds);

		//pull the metric wanted for each district
		let max = 1;
		if(this.metricFocus == "population"){ max = 3000000; }
		const districtData = this.filterByFocusMetric(data);


		if(!this.drawn){ this.drawStatePolygons(); }

		const labelText = UI_CONSTANTS[this.metricFocus].labelText;
		const histLabel = UI_CONSTANTS[this.metricFocus].histLabel;
		

		// TODO removing label until we decide new text bc it interferes with the buttons
		// d3.select("#label_area").append("text").text(labelText).attr("class", "label")
		// 	.attr("x", parseFloat(d3.select("#label_area").style("width"))/2)
		// 	.attr("y", parseFloat(d3.select("#label_area").style("height"))/2)
		// 	.style("text-anchor", "middle").style("alignment-baseline", "middle")
		// 	.style("font-size", "2em");

		d3.select("#task_dialog").append("text").text("Currrent Task:").attr("class", "label")
			.attr("x", parseFloat(d3.select("#task_dialog").style("width"))/10)
			.attr("y", parseFloat(d3.select("#task_dialog").style("height"))/4)
			.style("text-anchor", "left").style("alignment-baseline", "middle")
			.style("font-size", "1.5em");
			
		// INTENT DIALOGUE CODE
		// d3.select("#intent_dialog").append("text").text("Predicted Task Weights:").attr("class","label")
		// 	.attr("x", parseFloat(d3.select("#intent_dialog").style("width"))/10)
		// 	.attr("y", parseFloat(d3.select("#intent_dialog").style("height"))/5)
		// 	.style("font-size", "1.25em");


		districtData.forEach((district, i) => {
			let distX_min = 1000000, distX_max = 0, distY_min = 1000000, distY_max = 0;
			let scale = UI_CONSTANTS[this.metricFocus].scale;
			let f = scale([district.scalar_value, district.scalar_maximum]);
			district.precincts.forEach((precinct) => {
				this.counties[precinct].fill = f;
				if(distX_min > this.counties[precinct].x[0]){ distX_min = this.counties[precinct].x[0]; }
				if(distX_max < this.counties[precinct].x[1]){ distX_max = this.counties[precinct].x[1]; }
				if(distY_min > this.counties[precinct].y[0]){ distY_min = this.counties[precinct].y[0]; }
				if(distY_max < this.counties[precinct].y[1]){ distY_max = this.counties[precinct].y[1]; }
			});
			// this code was used to indicate the number of the districts previously
			// may be confusing with the centroids also on the screen

			// district labels - not to be confused with centroids
			// this.stateDiv.append("text").attr("class", "dist_label")
			// 	.attr("x", this.xScale(distX_min + (distX_max-distX_min)/2))
			// 	.attr("y", this.yScale(distY_min + (distY_max-distY_min)/2))
			// 	.attr("id", "marker"+(i+1))
			// 	.text(i+1)
		});

		let key = d3.select("#scale").append("g").attr("class", "key");
		
		let key_height = parseFloat(d3.select("#scale").style("height"));
		let key_width = parseFloat(d3.select("#scale").style("width"));
	
		let scale = UI_CONSTANTS[this.metricFocus].scale;
		let domain = UI_CONSTANTS[this.metricFocus].domain;
		let step = (domain[domain.length-1] - domain[0])/5;

		key.append("rect").attr("width", 6 * (key_height - 40)).attr("height", key_height - 40)
			.attr("x", 0).attr("y", 10)
			.attr("fill", "none").attr("stroke", "black").attr("stroke-width", 2);	
		
		if(domain[1] <= 1){
			key.append("text").attr("x", (key_height - 40)/2).attr("y", key_height - 16)
				.text(parseInt(domain[0] * 100) + "% " + UI_CONSTANTS[this.metricFocus].label)
				.attr("text-anchor", "middle").attr("alignment-baseline", "middle");
			key.append("text").attr("x", 5.5 * (key_height - 40)).attr("y", key_height - 16)
				.text(parseInt(domain[domain.length-1] * 100) + "% " + UI_CONSTANTS[this.metricFocus].label)
				.attr("text-anchor", "middle").attr("alignment-baseline", "middle");
		}
		else if (domain[1] == 70000){
			key.append("text").attr("x", (key_height - 40)/2).attr("y", key_height - 16)
				.text("$" + parseInt(domain[0]) + " " + UI_CONSTANTS[this.metricFocus].label)
				.attr("text-anchor", "middle").attr("alignment-baseline", "middle");
			key.append("text").attr("x", 5.5 * (key_height - 40)).attr("y", key_height - 16)
				.text("$" + parseInt(domain[domain.length-1]) + " " + UI_CONSTANTS[this.metricFocus].label)
				.attr("text-anchor", "middle").attr("alignment-baseline", "middle");
		}
		else{
			key.append("text").attr("x", (key_height - 40)/2).attr("y", key_height - 16)
				.text(parseInt(domain[0]) + " " + UI_CONSTANTS[this.metricFocus].label)
				.attr("text-anchor", "middle").attr("alignment-baseline", "middle");
			key.append("text").attr("x", 5.5 * (key_height - 40)).attr("y", key_height - 16)
				.text(parseInt(domain[domain.length-1]) + " " + UI_CONSTANTS[this.metricFocus].label)
				.attr("text-anchor", "middle").attr("alignment-baseline", "middle");
		}
		
		for(var i = 0; i <= 5; i++){
			key.append("rect").attr("height", key_height - 40).attr("width", key_height - 40)
				.attr("x", i * (key_height - 40)).attr("y", 10).attr("fill", () => {
					if(domain[1] == 0.55){ return scale([domain[0] + i * step, 1]) }
					else { return scale([domain[0] + i * step, domain[domain.length-1]]) }
				});
		}

		key.attr("transform", "translate(" + (key_width - (6 * (key_height - 40)))/2 + ",0)")

		this.paintStateViz();
		this.paintDashboard(data,precalculated_stats);
	}

	drawStatePolygons(){
		if(this.xScale != null){
			this.stateDiv.selectAll("polygon").data(this.counties).enter().append("polygon")
				.attr("points", function(county){
					return county.boundaries.map(function(point){
						return [SELF.xScale(point[0]), SELF.yScale(point[1])].join(",");
					}).join(" ");
				})
				.attr("fill", function(county){
					return county.fill;
				});
			this.drawn = true;
		}
		else{ return; }
	}

	drawDistrictBounds(boundaries) {
		var correctBounds = [];
		var lineGenerator = d3.line();

		d3.selectAll(".bounds").remove();
		boundaries.forEach((bounds) => {
			var b = [];
			bounds.forEach((pt, i) => {
				if(i%2 == 0){
					let p = [];
					p.push(this.xScale(pt));
					b.push(p);
				}
				else { b[b.length - 1].push(this.yScale(pt)); }
			});
			correctBounds.push(b);
		});

		correctBounds.forEach((bounds) => {
			this.stateDiv.append("path").attr("class", "bounds")
				.attr("d", lineGenerator(bounds)).attr("fill", "transparent").attr("stroke", "black").attr("stroke-width", "4px");
		});
	}
}