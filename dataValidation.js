/**
 * Advanced Data Validation for PILT Dashboard
 * This module provides robust data validation for PILT calculations
 */

/**
 * Validate district data structure
 * @param {Object} district - District data object
 * @returns {Object} - Validation result with isValid flag and errors array
 */
function validateDistrict(district) {
    const errors = [];
    const warnings = [];
    
    // Required fields
    if (!district.district) {
        errors.push("District name is required");
    } else if (typeof district.district !== 'string') {
        errors.push("District name must be a string");
    }
    
    // Assessed Value validation
    if (district.assessedValue === undefined || district.assessedValue === null) {
        errors.push("Assessed value is required");
    } else if (typeof district.assessedValue !== 'number') {
        errors.push("Assessed value must be a number");
    } else if (district.assessedValue < 0) {
        errors.push("Assessed value cannot be negative");
    } else if (district.assessedValue > 1000000000000) { // $1 trillion sanity check
        warnings.push("Assessed value is unusually high, please verify");
    }
    
    // Levy Rate validation
    if (district.levyRate === undefined || district.levyRate === null) {
        errors.push("Levy rate is required");
    } else if (typeof district.levyRate !== 'number') {
        errors.push("Levy rate must be a number");
    } else if (district.levyRate < 0) {
        errors.push("Levy rate cannot be negative");
    } else if (district.levyRate > 0.1) { // 10% sanity check
        warnings.push("Levy rate is unusually high, please verify");
    }
    
    // Deduction validation
    if (district.deduction === undefined) {
        district.deduction = 0; // Default to 0 if not provided
    } else if (typeof district.deduction !== 'number') {
        errors.push("Deduction must be a number");
    } else if (district.deduction < 0) {
        errors.push("Deduction cannot be negative");
    } else if (district.deduction > district.assessedValue * district.levyRate) {
        warnings.push("Deduction exceeds the base PILT amount");
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings,
        validatedDistrict: errors.length === 0 ? district : null
    };
}

/**
 * Validate an array of district data
 * @param {Array} districts - Array of district data objects
 * @returns {Object} - Validation result with isValid flag, errors, and validated data
 */
function validateDistrictData(districts) {
    if (!Array.isArray(districts)) {
        return {
            isValid: false,
            errors: ["Data must be an array of districts"],
            validatedData: null
        };
    }
    
    if (districts.length === 0) {
        return {
            isValid: false,
            errors: ["No district data provided"],
            validatedData: null
        };
    }
    
    const results = districts.map((district, index) => {
        const result = validateDistrict(district);
        if (!result.isValid) {
            result.errors = result.errors.map(err => `District ${index + 1} (${district.district || 'unnamed'}): ${err}`);
            result.warnings = result.warnings.map(warn => `District ${index + 1} (${district.district || 'unnamed'}): ${warn}`);
        }
        return result;
    });
    
    const allErrors = results.flatMap(r => r.errors);
    const allWarnings = results.flatMap(r => r.warnings);
    const validatedData = results.every(r => r.isValid) 
        ? results.map(r => r.validatedDistrict) 
        : null;
    
    return {
        isValid: allErrors.length === 0,
        errors: allErrors,
        warnings: allWarnings,
        validatedData
    };
}

/**
 * Validate what-if analysis options
 * @param {Object} options - What-if analysis options
 * @returns {Object} - Validation result
 */
function validateWhatIfOptions(options) {
    const errors = [];
    const warnings = [];
    
    if (typeof options !== 'object') {
        errors.push("Options must be an object");
        return { isValid: false, errors, warnings };
    }
    
    // Validate newRates
    if (options.newRates && typeof options.newRates !== 'object') {
        errors.push("newRates must be an object mapping district names to rates");
    } else if (options.newRates) {
        for (const [district, rate] of Object.entries(options.newRates)) {
            if (typeof rate !== 'number') {
                errors.push(`New rate for ${district} must be a number`);
            } else if (rate < 0) {
                errors.push(`New rate for ${district} cannot be negative`);
            } else if (rate > 0.1) { // 10% sanity check
                warnings.push(`New rate for ${district} is unusually high`);
            }
        }
    }
    
    // Validate valueAdjustments
    if (options.valueAdjustments && typeof options.valueAdjustments !== 'object') {
        errors.push("valueAdjustments must be an object mapping district names to multipliers");
    } else if (options.valueAdjustments) {
        for (const [district, adjustment] of Object.entries(options.valueAdjustments)) {
            if (typeof adjustment !== 'number') {
                errors.push(`Value adjustment for ${district} must be a number`);
            } else if (adjustment <= 0) {
                errors.push(`Value adjustment for ${district} must be positive`);
            } else if (adjustment > 5) { // 500% increase sanity check
                warnings.push(`Value adjustment for ${district} is unusually high`);
            }
        }
    }
    
    // Validate deductionAdjustments
    if (options.deductionAdjustments && typeof options.deductionAdjustments !== 'object') {
        errors.push("deductionAdjustments must be an object mapping district names to deduction amounts");
    } else if (options.deductionAdjustments) {
        for (const [district, deduction] of Object.entries(options.deductionAdjustments)) {
            if (typeof deduction !== 'number') {
                errors.push(`Deduction adjustment for ${district} must be a number`);
            } else if (deduction < 0) {
                errors.push(`Deduction adjustment for ${district} cannot be negative`);
            }
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Format currency values consistently
 * @param {number} value - The value to format
 * @returns {string} - Formatted currency string
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

/**
 * Format percentage values consistently
 * @param {number} value - The decimal value to format as percentage
 * @returns {string} - Formatted percentage string
 */
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
    }).format(value);
}

/**
 * Display validation errors and warnings in the UI
 * @param {Object} validationResult - The validation result object
 * @param {string} containerId - ID of the container element to show messages in
 */
function displayValidationMessages(validationResult, containerId = 'validation-messages') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    if (validationResult.errors.length === 0 && validationResult.warnings.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    // Display errors
    if (validationResult.errors.length > 0) {
        const errorList = document.createElement('div');
        errorList.className = 'validation-errors';
        
        const errorHeader = document.createElement('h4');
        errorHeader.textContent = 'Errors:';
        errorList.appendChild(errorHeader);
        
        const ul = document.createElement('ul');
        validationResult.errors.forEach(error => {
            const li = document.createElement('li');
            li.textContent = error;
            ul.appendChild(li);
        });
        
        errorList.appendChild(ul);
        container.appendChild(errorList);
    }
    
    // Display warnings
    if (validationResult.warnings.length > 0) {
        const warningList = document.createElement('div');
        warningList.className = 'validation-warnings';
        
        const warningHeader = document.createElement('h4');
        warningHeader.textContent = 'Warnings:';
        warningList.appendChild(warningHeader);
        
        const ul = document.createElement('ul');
        validationResult.warnings.forEach(warning => {
            const li = document.createElement('li');
            li.textContent = warning;
            ul.appendChild(li);
        });
        
        warningList.appendChild(ul);
        container.appendChild(warningList);
    }
}

// Make these functions available to the browser
window.validateDistrict = validateDistrict;
window.validateDistrictData = validateDistrictData;
window.validateWhatIfOptions = validateWhatIfOptions;
window.formatCurrency = formatCurrency;
window.formatPercentage = formatPercentage;
window.displayValidationMessages = displayValidationMessages;