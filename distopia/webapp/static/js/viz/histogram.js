/*
	Histogram
	==========
	Generic histogram
	Inputs:
		selector: d3 selector, e.g. "#district7"
		data: 
*/
import {parseData} from '../distopiaInterface.js';

const padding = {
	left: 50,
	right: 15,
	top: 25,
	bottom: 25
};

class Histogram{
	constructor(selector, initialData, labels, styles) {
		this.selector = selector;
		this.render(initialData, labels, styles);
	}

	render(data, labels, styles, max){
		d3.select(this.selector).selectAll(".xAxis").remove(); 
		d3.select(this.selector).selectAll(".yAxis").remove();
		d3.select(this.selector).selectAll("rect").remove();

		let white = 0;
		//SPECIAL CASE FOR RACE BREAKDOWN DATA
		if(labels[0] == "white"){
			max = 0.25;
			let arr = data.slice(0);
			let otherInd, pacInd;
			labels.forEach((label, index) => {
				if(label == "white"){
					white = data[index];
					arr.splice(index, 1);
				}
				else if(label == "pacific_Islander"){ pacInd = index; }
				else if(label == "other"){ otherInd = index; }
			});
			if(pacInd != undefined){
				arr[otherInd] += pacInd;
				arr.splice(pacInd, 1);
			}
			
			labels = ["Black", "Hispanic", "Native American", "Asian", "Other", "Two or More"];
			data = arr;
		}

		//SPECIAL CASE FOR INCOME BREAKDOWN DATA
		if(labels[0] == "0"){
			let bins = [0, 0, 0, 0, 0];
			labels.forEach((label, index) => {
				if(label == "0" || label == "10" || label == "15"){
					bins[0] += parseFloat(data[index]);
				}
				else if(label == "25" || label == "35"){
					bins[1] += parseFloat(data[index]);
				}
				else if(label == "50"){
					bins[2] += parseFloat(data[index]);
				}
				else if(label == "75"){
					bins[3] += parseFloat(data[index]);
				}
				else {
					bins[4] += parseFloat(data[index]);
				}
			});
			labels = ["$0 to $25k", "$25k to $50k", "$50k to $75k", "$75k to $100k", "$100k +"];
			data = bins;
		}

		//SPECIAL CASE FOR AGE
		if(labels[0] == "2.5"){
			let bins = [0, 0, 0, 0, 0, 0, 0, 0, 0];
			let binLabels = []
			for(let i = 0; i <= 7; i ++){
				bins[i] = data[2 * i] + data[2 * i + 1];
				let l1 = parseFloat(labels[2 * i]);
				l1 -= 2.5;
				let l2 = parseFloat(labels[2 * i + 1]);
				l2 += 2.5;
				binLabels.push("" + l1 + " to " + l2);
			}
			binLabels.push("80+")
			for(let i = 16; i < 19; i++){
				bins[8] += data[i];
			}
			data = bins;
			labels = binLabels;
		}

		if(labels[0] == "Manufacturing"){labels[2] = "Professional"}
		if(labels[0] == "democrat"){labels = ["Democrat", "Republican"]}
		if(labels[0] == "total"){labels = ["Total Population", "Voting Population"]}
		if(labels[0] == "High school"){labels = ["High School/GED", "Bachelor's"]}

		let colors = null;
		if(styles.colors != null){ colors = styles.colors; }
		const width = parseFloat(d3.select(this.selector).style("width"));
		const height = parseFloat(d3.select(this.selector).style("height"));

		const xScale = d3.scaleBand().domain(labels.map(function(d){ return d; })).range([padding.left, width - padding.right])
			.paddingInner([0.1]).paddingOuter([0.2]).align([0.5]);
		const yScale = d3.scaleLinear().domain([0, max]).range([height - padding.bottom, padding.top]);

		//sum across the frequency bins to normalize the counts
		let sum = 0;
		data.forEach((d) => { sum += d; });
		sum += white; //SPECIAL CASE FOR RACE DATA

		let s = d3.axisLeft(yScale);
		if(max > 1){ s = s.tickFormat(d3.formatPrefix(".1", 1e6)); }
		else { s = s.tickFormat(d3.format(".0%")); }
		s.ticks(5);
		//adds axis to the histogram
		d3.select(this.selector).append("g").attr("class", "xAxis")
			.attr("transform", "translate(" + [0, height - padding.bottom] + ")")
			.call(d3.axisBottom(xScale));
		d3.select(this.selector).append("g").attr("class", "yAxis")
			.attr("transform", "translate(" + [padding.left, 0] + ")")
			.call(s);
		
		//enters data
		let rect = d3.select(this.selector)
			.selectAll("rect").data(parseData(labels, data))
			.attr("x", function(d){ return xScale(d.name); })
			.attr("y", function(d){
				if(max > 1){ return yScale(d.amount); }
				else{ return yScale(d.amount/sum); }
			})
			.attr("width", xScale.bandwidth())
			.attr("height", function(d){
				if(max > 1){ return yScale(0) - yScale(d.amount); }
				else{ return yScale(0) - yScale(d.amount/sum); }
			})
			.attr("fill", function(d,i){
				if(colors != null){ return colors[labels[i]]; }
			});

		//updates data
		rect.enter().append("rect")
			.attr("x", function(d){ return xScale(d.name); })
			.attr("y", function(d){
				if(max > 1){ return yScale(d.amount); }
				else{ return yScale(d.amount/sum); }
			})
			.attr("width", xScale.bandwidth())
			.attr("height", function(d){ 
				if(max > 1){ return yScale(0) - yScale(d.amount); }
				else{ return yScale(0) - yScale(d.amount/sum); }
			})
			.attr("fill", function(d,i){
				if(colors != null){ return colors[labels[i]]; }
			});
		
		//removes data
		rect.exit().remove();
	}

	update(data, labels, styles, max) {
		this.render(data, labels, styles, max);
	}
}

export default Histogram;