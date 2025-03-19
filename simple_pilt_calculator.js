/**
 * Simple PILT calculator in JavaScript
 */

// Sample district data
const districtData = [
  { 
    district: "City of Richland", 
    assessedValue: 24580000, 
    levyRate: 0.0025, 
    deduction: 0 
  },
  { 
    district: "City of Kennewick", 
    assessedValue: 18760000, 
    levyRate: 0.0025, 
    deduction: 5000 
  },
  { 
    district: "City of Pasco", 
    assessedValue: 15420000, 
    levyRate: 0.0025, 
    deduction: 0 
  },
  { 
    district: "West Richland", 
    assessedValue: 8150000, 
    levyRate: 0.0025, 
    deduction: 2500 
  },
  { 
    district: "Benton City", 
    assessedValue: 4380000, 
    levyRate: 0.0025, 
    deduction: 0 
  },
  { 
    district: "Prosser", 
    assessedValue: 6240000, 
    levyRate: 0.0025, 
    deduction: 0 
  }
];

/**
 * Calculate PILT for each district
 * @param {Array} districts - Array of district data objects
 * @returns {Array} - Array of district data with calculated PILT
 */
function calculatePILT(districts) {
  return districts.map(district => {
    const basePILT = district.assessedValue * district.levyRate;
    const piltDue = basePILT - district.deduction;
    
    return {
      ...district,
      basePILT,
      piltDue
    };
  });
}

/**
 * Aggregate PILT data to get totals
 * @param {Array} piltData - Array of PILT calculations by district
 * @returns {Object} - Aggregated totals
 */
function aggregatePILT(piltData) {
  return piltData.reduce((totals, district) => {
    return {
      assessedValue: totals.assessedValue + district.assessedValue,
      basePILT: totals.basePILT + district.basePILT,
      deduction: totals.deduction + district.deduction,
      piltDue: totals.piltDue + district.piltDue
    };
  }, { assessedValue: 0, basePILT: 0, deduction: 0, piltDue: 0 });
}

/**
 * Perform "what-if" analysis by adjusting rates or values
 * @param {Array} districts - Original district data
 * @param {Object} options - Adjustment options
 * @returns {Array} - Adjusted district data
 */
function whatIfAnalysis(districts, options = {}) {
  const { 
    newRates = {}, 
    valueAdjustments = {}, 
    deductionAdjustments = {} 
  } = options;
  
  return districts.map(district => {
    const newDistrict = {...district};
    
    // Apply new levy rate if specified
    if (newRates[district.district]) {
      newDistrict.levyRate = newRates[district.district];
    }
    
    // Apply value adjustment if specified (as multiplier, e.g., 1.05 for 5% increase)
    if (valueAdjustments[district.district]) {
      newDistrict.assessedValue = district.assessedValue * valueAdjustments[district.district];
    }
    
    // Apply deduction adjustment if specified
    if (deductionAdjustments[district.district] !== undefined) {
      newDistrict.deduction = deductionAdjustments[district.district];
    }
    
    return newDistrict;
  });
}

// Make these functions available to the browser
window.districtData = districtData;
window.calculatePILT = calculatePILT;
window.aggregatePILT = aggregatePILT;
window.whatIfAnalysis = whatIfAnalysis;