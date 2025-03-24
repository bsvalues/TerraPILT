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
 * Calculate PILT for each district with validation
 * @param {Array} districts - Array of district data objects
 * @returns {Object} - Object containing calculated data and validation results
 */
function calculatePILT(districts) {
  // Validate district data if validation function is available
  if (window.validateDistrictData) {
    const validationResult = window.validateDistrictData(districts);
    
    if (!validationResult.isValid) {
      // Display validation errors if the function is available
      if (window.displayValidationMessages) {
        window.displayValidationMessages(validationResult);
      }
      
      // Return validation result along with original data
      return {
        data: districts.map(district => {
          const basePILT = district.assessedValue * district.levyRate;
          const piltDue = basePILT - (district.deduction || 0);
          
          return {
            ...district,
            basePILT,
            piltDue
          };
        }),
        validationResult
      };
    }
    
    // Use validated data
    districts = validationResult.validatedData;
  }
  
  // Perform calculation
  const calculatedData = districts.map(district => {
    const basePILT = district.assessedValue * district.levyRate;
    const piltDue = basePILT - (district.deduction || 0);
    
    return {
      ...district,
      basePILT,
      piltDue
    };
  });
  
  // Return the calculated data with validation info
  return {
    data: calculatedData,
    validationResult: window.validateDistrictData ? 
      { isValid: true, errors: [], warnings: [] } : 
      null
  };
}

/**
 * Aggregate PILT data to get totals
 * @param {Object} piltResults - Object containing PILT calculations by district
 * @returns {Object} - Aggregated totals
 */
function aggregatePILT(piltResults) {
  const piltData = piltResults.data || [];
  return piltData.reduce((totals, district) => {
    return {
      assessedValue: totals.assessedValue + district.assessedValue,
      basePILT: totals.basePILT + district.basePILT,
      deduction: totals.deduction + (district.deduction || 0),
      piltDue: totals.piltDue + district.piltDue
    };
  }, { assessedValue: 0, basePILT: 0, deduction: 0, piltDue: 0 });
}

/**
 * Perform "what-if" analysis by adjusting rates or values
 * @param {Array} districts - Original district data
 * @param {Object} options - Adjustment options
 * @returns {Object} - Object containing adjusted data and validation results
 */
function whatIfAnalysis(districts, options = {}) {
  // Validate options if validation function is available
  if (window.validateWhatIfOptions) {
    const optionsValidation = window.validateWhatIfOptions(options);
    
    if (!optionsValidation.isValid) {
      // Display validation errors if the function is available
      if (window.displayValidationMessages) {
        window.displayValidationMessages(optionsValidation);
      }
      
      // Return original data with validation info
      return {
        data: districts,
        validationResult: optionsValidation
      };
    }
  }
  
  const { 
    newRates = {}, 
    valueAdjustments = {}, 
    deductionAdjustments = {} 
  } = options;
  
  // Apply adjustments
  const adjustedData = districts.map(district => {
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
  
  // Validate adjusted data if validation function is available
  if (window.validateDistrictData) {
    const validationResult = window.validateDistrictData(adjustedData);
    
    if (!validationResult.isValid) {
      // Display validation errors
      if (window.displayValidationMessages) {
        window.displayValidationMessages(validationResult);
      }
      
      return {
        data: adjustedData,
        validationResult
      };
    }
    
    return {
      data: validationResult.validatedData,
      validationResult: { isValid: true, errors: [], warnings: [] }
    };
  }
  
  // Return adjusted data without validation
  return {
    data: adjustedData,
    validationResult: null
  };
}

// Make these functions available to the browser
window.districtData = districtData;
window.calculatePILT = calculatePILT;
window.aggregatePILT = aggregatePILT;
window.whatIfAnalysis = whatIfAnalysis;