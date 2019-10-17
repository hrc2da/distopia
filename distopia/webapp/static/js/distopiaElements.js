

/**
 * @param {Array<Number>} domain
 * @param {Array<String>} range
 * @param {any} scaling_var
 * @param {any} scaling_normalizer
 */
function simplifiedScale(domain,range, scaling_var){
    let scale = d3.scaleLinear().domain(domain).range(range);
    return scale(scaling_var);
}
//These are global color scales for different metrics
//To invoke, scales.[NAME OF SCALE](VALUE) ex: scales.partisanFill(0.5)
export var SCALE = {
	//every scale, get scaleMax, scaleMin, scaleVale
	"age": ([median_age,total_pop]) => simplifiedScale([35,55],["white","#C93FFF"], median_age),
	"education": function([num_college, total_pop]){
		//percentage with bachelor's degree or higher
		let scale = d3.scaleLinear().domain([0, 1]).range(["white", "purple"]);
		return scale(num_college/total_pop);
	},
	"income": ([median_income, tot_pop]) => {return simplifiedScale([35000,70000],["white","green"],median_income)},
	"occupation": function([num_employed, total_pop]){
		//percentage employed out of total population
		let scale = d3.scaleLinear().domain([0.45,0.55]).range(["white", "pink"]);
		return scale(num_employed/total_pop);
    },
    //voting population out of 3 million (or max which will be defined later)
	"population": ([pop_voting, total_pop]) => simplifiedScale([0,3000000],["white","orange"],pop_voting),
	"projected_votes": function([num_democrat, total_votes]){
		//lean to either republican or democrat
		// let scale = d3.scaleLinear().domain([-1, 0, 1]).range(["#D0021B","white", "#4A90E2"]);
		// let prop_democrat = num_democrat/total_votes;
		// let prop_republican = 1 - prop_democrat;
		// return scale(prop_democrat - prop_republican);
		let scale = d3.scaleLinear().domain([0, 0.5, 1]).range(["#D0021B","white", "#4A90E2"]);
		let prop_democrat = num_democrat/total_votes;
		return scale(prop_democrat);
	},
	"race": function([num_minorities, total_pop]){
		//number nonwhite divided by total population
		let scale = d3.scaleLinear().domain([0,1]).range(["white", "#102C42"]);
		return scale(num_minorities/total_pop);
	},
	"pvi": function([wasted_votes,_]){
		let scale = d3.scaleLinear().domain([0,200000]).range(["white","red"]);
		return scale(wasted_votes)
	},
	"compactness": function([compactness,_]){
		let scale = d3.scaleLinear().domain([0,1]).range(["white","green"]);
		return scale(compactness)
	}
}

export var DOMAIN = {
	"age": {
		domain: [35,55],
		label: "years old"
	},
	"education": {
		domain: [0, 1],
		label: "College Educated"
	},
	"income": {
		domain: [35000, 70000],
		label: "annual income"
	},
	"occupation": {
		domain: [0.45,0.55],
		label: "employed"
	},
	"population": {
		domain: [0,3000000],
		label: "voters"
	},
	"projected_votes": {
		domain: [0, 1],
		label: "Democrat"
	},
	"race":{
		domain: [0,1],
		label: "Non-white"
	},
	"pvi":{
		domain: [0,200000],
		label: "Wasted Votes"
	},
	"compactness": {
		domain: [0,1],
		label: "Compactness"
	}
}

export const METRICS = ["age","education","income","occupation","population","projected_votes","race","sex"]

export const METRIC_TYPE = ["histogram","histogram","histogram","histogram","histogram","histogram","histogram","histogram"]

export const STYLES = {
	"race": {
		colors:{
			"white": "#E6AF81",
			"Black": "#E68882",
			"Hispanic": "#8A82E5",
			"Asian": "#BDE682",
			"Native American": "#82E0E6",
			"pacific_islander": "#CCCCCC",
			"Other": "#000000",
			"Two or More": "#444444"
		}
	},
	"population": {
		colors:{
			"Total Population": "#CCCCCC",
			"Voting Population": "#82E0E6"
		}
	},
	"age":{
		colors: {
			"0 to 10":"#447C1C",
			"10 to 20":"#588B20",
			"20 to 30":"#6E9A25",
			"30 to 40":"#87A82A",
			"40 to 50":"#A1B62F",
			"50 to 60":"#BDC434",
			"60 to 70":"#D2CA39",
			"70 to 80":"#E0C63E",
			"80+":"#EDC044",
		}
	},
	"education":{
		colors:{
			"High School/GED": "#CCCCCC",
			"Bachelor's": "#82E0E6"
		}
	},
	"projected_votes":{
		colors:{
			"Democrat": "#4A90E2",
			"Republican": "#D0021B"
		}
	},
	"income":{
		colors: {
			"$0 to $25k": "#D7F6FF",
			"$25k to $50k": "#B1D4FF",
			"$50k to $75k" :"#8C9EFF",
			"$75k to $100k" :"#7E6AFF",
			"$100k +" :"#9449FF"
		}
	},
	"occupation":{
		colors:{
			"Manufacturing": "#E6AF81",
			"Retail": "#E68882",
			"Professional": "#8A82E5",
			"Public": "#BDE682",
			"Service": "#82E0E6",
		}
	}
}