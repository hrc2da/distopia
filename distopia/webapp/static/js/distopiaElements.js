

export const parseData = (labels, data) => {
	let objArray = [];
	labels.forEach((label, i) => objArray.push({name: label, amount: data[i]}));
	return objArray;
}

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

export var UI_CONSTANTS = {
	// "age": {
	// 	//every scale, get scaleMax, scaleMin, scaleVale
	// 	"scale": ([median_age,total_pop]) => simplifiedScale([35,55],["white","#C93FFF"], median_age),
	// 	"domain":[35,55],
	// 	"label":"years old",
	// 	"labelText": "Median Age per District",
	// 	"histLabel": "Age Distribution per District",
	// 	"colors":{
	// 		"0 to 10":"#447C1C",
	// 		"10 to 20":"#588B20",
	// 		"20 to 30":"#6E9A25",
	// 		"30 to 40":"#87A82A",
	// 		"40 to 50":"#A1B62F",
	// 		"50 to 60":"#BDC434",
	// 		"60 to 70":"#D2CA39",
	// 		"70 to 80":"#E0C63E",
	// 		"80+":"#EDC044",
	// 	}
	// },
	// "education":{
    // 	//percentage with bachelor's degree or higher
	// 	"scale": ([num_college, total_pop]) => simplifiedScale([0,1],["white","purple"], num_college/total_pop),
	// 	"domain":[0, 1],
	// 	"label":"years old",
	// 	"labelText": "College Educated",
	// 	"histLabel": "Educational Attainment per District",
	// 	"colors": {
	// 		"High School/GED": "#CCCCCC",
	// 		"Bachelor's": "#82E0E6"
	// 	}
	// },
	// "income": {
	// 	"scale": ([median_income, tot_pop]) => simplifiedScale([35000,70000],["white","green"],median_income),
	// 	"domain":[35000, 70000],
	// 	"label":"annual income",
	// 	"labelText": "Median Income per District",
	// 	"histLabel": "Income Distribution per District",
	// 	"colors":{
	// 		"$0 to $25k": "#D7F6FF",
	// 		"$25k to $50k": "#B1D4FF",
	// 		"$50k to $75k" :"#8C9EFF",
	// 		"$75k to $100k" :"#7E6AFF",
	// 		"$100k +" :"#9449FF"
	// 	}
	// },
	// "occupation": {
	// 	//percentage employed out of total population
	// 	"scale": ([num_employed, total_pop]) => simplifiedScale([0.45,0.55],["white","pink"],num_employed/total_pop),
	// 	"domain": [0.45,0.55],
	// 	"label": "employed",
	// 	"labelText": "% Employed per District",
	// 	"histLabel": "Occupation Sector Distribution per District",
	// 	"colors":{
	// 		"Manufacturing": "#E6AF81",
	// 		"Retail": "#E68882",
	// 		"Professional": "#8A82E5",
	// 		"Public": "#BDE682",
	// 		"Service": "#82E0E6",
	// 	}
	// },
	"population": {
		//voting population out of 3 million (or max which will be defined later)
		"scale": ([pop_voting, total_pop]) => simplifiedScale([0,3000000],["white","orange"],pop_voting),
		"domain":[0,3000000],
		"label": "voters",
		"labelText": "Population per District",
		"histLabel": "Total Population vs. Voting Population",
		"colors": {
			"Total Population": "#CCCCCC",
			"Voting Population": "#82E0E6"
		}
	},
	"projected_votes": {
		//lean to either republican or democrat
		// let scale = d3.scaleLinear().domain([-1, 0, 1]).range(["#D0021B","white", "#4A90E2"]);
		// let prop_democrat = num_democrat/total_votes;
		// let prop_republican = 1 - prop_democrat;
		// return scale(prop_democrat - prop_republican);
		"scale": ([num_democrat, total_votes])=> simplifiedScale([0,0.5,1],["#D0021B","white","#4A90E2"], num_democrat/total_votes),
		"domain": [0, 1],
		"label": "Democrat",
		"labelText": "Partisan Lean per District",
		"histLabel": "Partisan Breakdown per District",
		"colors": {
			"Democrat": "#4A90E2",
			"Republican": "#D0021B"
		}
	},
	// "race": {
	// 	//number nonwhite divided by total population
	// 	"scale": ([num_minorities, total_pop]) => simplifiedScale([0,1],["white","#102C42"], num_minorities/total_pop),
	// 	"domain": [0,1],
	// 	"label": "Non-white",
	// 	"labelText": "% Minority population per District",
	// 	"histLabel": "Non-White Racial Distribution per District",
	// 	"colors": {
	// 		"white": "#E6AF81",
	// 		"Black": "#E68882",
	// 		"Hispanic": "#8A82E5",
	// 		"Asian": "#BDE682",
	// 		"Native American": "#82E0E6",
	// 		"pacific_islander": "#CCCCCC",
	// 		"Other": "#000000",
	// 		"Two or More": "#444444"
	// 	}
	// },
	"pvi": {
		"scale": ([wasted_votes,_]) => simplifiedScale([0,20000],["white","red"], wasted_votes),
		"domain":[0,200000],
		"label": "Wasted Votes",
		"labelText": "# Wasted Votes",
		"histLabel": "This Plot is Under Construction",
	},
	"compactness": {
		"scale": ([compactness,_]) => simplifiedScale([0,1],["white","green"], compactness),
		"domain": [0,1],
		"label": "Compactness",
		"labelText": "How Regular Shapes Are",
		"histLabel": "This Plot is Under Construction"
	}	
}

export var TASK_DESCRIPTIONS = [
    // population
    "Try to evenly balance the number of people each district has.",
    // pvi
    "Try to create districts that minimize the number of wasted votes.",
    // compactness
	"Try to create districts that are round and regularly shaped.",
	// TASK PAIRS ///////////////////////////
	// Pop + PVI
	"Try to evenly balance the number of people each district has. and \n Try to create districts that minimize the number of wasted votes.",
	// POP + compactness
	"Try to evenly balance the number of people each district has. and \n Try to create districts that are round and regularly shaped.",
	// PVI + compactness
	"Try to create districts that minimize the number of wasted votes. \n Try to create districts that are round and regularly shaped.",
	// ALL 3
	"Try to evenly balance the number of people each district has. and \n Try to create districts that minimize the number of wasted votes. \n Try to create districts that are round and regularly shaped."

];