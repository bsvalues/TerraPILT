/**
 * Verification script to check PILT calculations
 */

// Load the calculator functions
const calculatorScript = require('./simple_pilt_calculator.js');

console.log("===== PILT Calculation Verification =====");

// Sample test data
const testData = [
  { 
    district: "Test District 1", 
    assessedValue: 10000000, 
    levyRate: 0.0025, 
    deduction: 0 
  },
  { 
    district: "Test District 2", 
    assessedValue: 5000000, 
    levyRate: 0.0025, 
    deduction: 2500 
  }
];

// Manual calculations
const manualCalculations = [
  {
    district: "Test District 1",
    basePILT: 10000000 * 0.0025, // = 25000
    piltDue: 10000000 * 0.0025 - 0 // = 25000
  },
  {
    district: "Test District 2",
    basePILT: 5000000 * 0.0025, // = 12500
    piltDue: 5000000 * 0.0025 - 2500 // = 10000
  }
];

// Run the calculations from our library
const piltResults = window.calculatePILT(testData);

// Compare results
piltResults.forEach((result, index) => {
  const manual = manualCalculations[index];
  console.log(`\nDistrict: ${result.district}`);
  console.log(`Assessed Value: $${result.assessedValue.toLocaleString()}`);
  console.log(`Levy Rate: ${result.levyRate}`);
  console.log(`Deduction: $${result.deduction.toLocaleString()}`);
  
  console.log(`\nBase PILT Calculation:`);
  console.log(`Expected: $${manual.basePILT.toLocaleString()}`);
  console.log(`Actual: $${result.basePILT.toLocaleString()}`);
  console.log(`Match: ${manual.basePILT === result.basePILT ? '✓' : '✗'}`);
  
  console.log(`\nPILT Due Calculation:`);
  console.log(`Expected: $${manual.piltDue.toLocaleString()}`);
  console.log(`Actual: $${result.piltDue.toLocaleString()}`);
  console.log(`Match: ${manual.piltDue === result.piltDue ? '✓' : '✗'}`);
});

// Verify aggregation
const manualTotals = {
  assessedValue: 15000000,
  basePILT: 37500,
  deduction: 2500,
  piltDue: 35000
};

const calculatedTotals = window.aggregatePILT(piltResults);

console.log("\n===== Aggregation Verification =====");
console.log(`Total Assessed Value - Expected: $${manualTotals.assessedValue.toLocaleString()}, Actual: $${calculatedTotals.assessedValue.toLocaleString()}, Match: ${manualTotals.assessedValue === calculatedTotals.assessedValue ? '✓' : '✗'}`);
console.log(`Total Base PILT - Expected: $${manualTotals.basePILT.toLocaleString()}, Actual: $${calculatedTotals.basePILT.toLocaleString()}, Match: ${manualTotals.basePILT === calculatedTotals.basePILT ? '✓' : '✗'}`);
console.log(`Total Deduction - Expected: $${manualTotals.deduction.toLocaleString()}, Actual: $${calculatedTotals.deduction.toLocaleString()}, Match: ${manualTotals.deduction === calculatedTotals.deduction ? '✓' : '✗'}`);
console.log(`Total PILT Due - Expected: $${manualTotals.piltDue.toLocaleString()}, Actual: $${calculatedTotals.piltDue.toLocaleString()}, Match: ${manualTotals.piltDue === calculatedTotals.piltDue ? '✓' : '✗'}`);

// Test what-if scenario
console.log("\n===== What-If Analysis Verification =====");

// Test adjusting levy rate
const newRates = { "Test District 1": 0.003 };
const valueAdjustments = { "Test District 2": 1.1 }; // 10% increase
const deductionAdjustments = { "Test District 2": 5000 };

const whatIfResults = window.whatIfAnalysis(testData, {
  newRates,
  valueAdjustments,
  deductionAdjustments
});

// Expected results after adjustments
const expectedWhatIf = [
  {
    district: "Test District 1",
    assessedValue: 10000000,
    levyRate: 0.003,
    deduction: 0
  },
  {
    district: "Test District 2",
    assessedValue: 5500000, // 5000000 * 1.1
    levyRate: 0.0025,
    deduction: 5000
  }
];

whatIfResults.forEach((result, index) => {
  const expected = expectedWhatIf[index];
  console.log(`\nDistrict: ${result.district}`);
  console.log(`Levy Rate - Expected: ${expected.levyRate}, Actual: ${result.levyRate}, Match: ${expected.levyRate === result.levyRate ? '✓' : '✗'}`);
  console.log(`Assessed Value - Expected: ${expected.assessedValue}, Actual: ${result.assessedValue}, Match: ${expected.assessedValue === result.assessedValue ? '✓' : '✗'}`);
  console.log(`Deduction - Expected: ${expected.deduction}, Actual: ${result.deduction}, Match: ${expected.deduction === result.deduction ? '✓' : '✗'}`);
});