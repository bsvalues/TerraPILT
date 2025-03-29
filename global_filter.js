/**
 * Global Filtering System for PILT Dashboard
 * This module provides functionality for filtering data across all dashboard widgets
 */

// Global state for active filters
let activeFilters = {
    district: [],
    minValue: null,
    minRate: null
};

// Original unfiltered data
let originalData = [];

// Filtered data (will be used by widgets)
let filteredData = [];

/**
 * Initialize the global filtering system
 */
function initGlobalFilters() {
    console.log('Initializing global filters');
    
    // Store original data
    if (window.piltData && window.piltData.length > 0) {
        originalData = [...window.piltData];
    }
    
    // Populate district filter
    populateDistrictFilter();
    
    // Set up event listeners
    const toggleFilterPanelBtn = document.getElementById('toggleFilterPanelBtn');
    if (toggleFilterPanelBtn) {
        toggleFilterPanelBtn.addEventListener('click', () => {
            const filterContent = document.querySelector('.filter-content');
            if (filterContent) {
                if (filterContent.style.display === 'none') {
                    filterContent.style.display = 'grid';
                    toggleFilterPanelBtn.textContent = 'Hide Filters';
                } else {
                    filterContent.style.display = 'none';
                    toggleFilterPanelBtn.textContent = 'Show Filters';
                }
            }
        });
    }
    
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            // Get filter values
            const districtSelect = document.getElementById('globalDistrictFilter');
            const minValueInput = document.getElementById('minValueFilter');
            const minRateInput = document.getElementById('minRateFilter');
            
            const selectedDistricts = Array.from(districtSelect.selectedOptions).map(option => option.value);
            const minValue = minValueInput.value ? parseFloat(minValueInput.value) : null;
            const minRate = minRateInput.value ? parseFloat(minRateInput.value) : null;
            
            // Apply filters
            applyGlobalFilter({
                district: selectedDistricts,
                minValue: minValue,
                minRate: minRate
            });
        });
    }
    
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    // Try to restore any saved filters
    restoreSavedFilters();
}

/**
 * Populate the district filter select with available districts
 */
function populateDistrictFilter() {
    if (!window.piltData || window.piltData.length === 0) return;
    
    const districtSelect = document.getElementById('globalDistrictFilter');
    if (!districtSelect) return;
    
    // Clear existing options
    districtSelect.innerHTML = '';
    
    // Get unique districts
    const districts = [...new Set(window.piltData.map(item => item.district))];
    
    // Add options
    districts.forEach(district => {
        const option = document.createElement('option');
        option.value = district;
        option.textContent = district;
        districtSelect.appendChild(option);
    });
}

/**
 * Apply global filters to the data
 * @param {Object} filters - Filter configuration
 */
function applyGlobalFilter(filters) {
    console.log('Applying global filters:', filters);
    
    // Update active filters
    activeFilters = {
        district: filters.district || [],
        minValue: filters.minValue,
        minRate: filters.minRate
    };
    
    // Make sure we have data to filter
    if (!originalData.length && window.piltData && window.piltData.length) {
        originalData = [...window.piltData];
    }
    
    // Apply filters to create filtered dataset
    filteredData = originalData.filter(item => {
        // Filter by district if districts are selected
        if (activeFilters.district.length > 0 && !activeFilters.district.includes(item.district)) {
            return false;
        }
        
        // Filter by minimum assessed value
        if (activeFilters.minValue !== null && item.assessedValue < activeFilters.minValue) {
            return false;
        }
        
        // Filter by minimum levy rate
        if (activeFilters.minRate !== null && item.levyRate < activeFilters.minRate) {
            return false;
        }
        
        return true;
    });
    
    // Update the global piltData with filtered data
    window.piltData = filteredData;
    
    // Update filter display
    updateActiveFiltersDisplay();
    
    // Update all widgets with new filtered data
    updateAllWidgets();
    
    // Save filters to localStorage
    saveFilters();
    
    return filteredData;
}

/**
 * Update display of active filters
 */
function updateActiveFiltersDisplay() {
    // Check if we already have an active filters container
    let activeFiltersContainer = document.querySelector('.active-filters');
    
    // If not, create one
    if (!activeFiltersContainer) {
        activeFiltersContainer = document.createElement('div');
        activeFiltersContainer.className = 'active-filters';
        
        // Add it after the filter content
        const filterPanel = document.querySelector('.dashboard-filter-panel');
        if (filterPanel) {
            filterPanel.appendChild(activeFiltersContainer);
        }
    }
    
    // Clear existing filter tags
    activeFiltersContainer.innerHTML = '';
    
    // If no filters are active, hide the container
    const hasActiveFilters = activeFilters.district.length > 0 || 
                             activeFilters.minValue !== null || 
                             activeFilters.minRate !== null;
    
    if (!hasActiveFilters) {
        activeFiltersContainer.style.display = 'none';
        return;
    }
    
    // Show container
    activeFiltersContainer.style.display = 'flex';
    
    // Add label
    const label = document.createElement('span');
    label.textContent = 'Active Filters:';
    label.style.fontWeight = 'bold';
    activeFiltersContainer.appendChild(label);
    
    // Create filter tags for districts
    activeFilters.district.forEach(district => {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `District: ${district} <span class="filter-tag-remove" data-filter-type="district" data-filter-value="${district}">×</span>`;
        activeFiltersContainer.appendChild(tag);
    });
    
    // Create filter tag for minimum value
    if (activeFilters.minValue !== null) {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `Min Value: ${formatCurrency(activeFilters.minValue)} <span class="filter-tag-remove" data-filter-type="minValue">×</span>`;
        activeFiltersContainer.appendChild(tag);
    }
    
    // Create filter tag for minimum rate
    if (activeFilters.minRate !== null) {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `Min Rate: ${activeFilters.minRate} <span class="filter-tag-remove" data-filter-type="minRate">×</span>`;
        activeFiltersContainer.appendChild(tag);
    }
    
    // Add event listeners to remove buttons
    const removeButtons = document.querySelectorAll('.filter-tag-remove');
    removeButtons.forEach(button => {
        button.addEventListener('click', () => {
            const filterType = button.getAttribute('data-filter-type');
            const filterValue = button.getAttribute('data-filter-value');
            
            removeFilter(filterType, filterValue);
        });
    });
}

/**
 * Remove a specific filter
 * @param {string} filterType - Type of filter to remove
 * @param {string} filterValue - Value to remove (for arrays like district)
 */
function removeFilter(filterType, filterValue) {
    if (filterType === 'district' && filterValue) {
        // Remove specific district
        activeFilters.district = activeFilters.district.filter(d => d !== filterValue);
    } else if (filterType === 'minValue') {
        // Clear min value filter
        activeFilters.minValue = null;
        
        // Reset input
        const minValueInput = document.getElementById('minValueFilter');
        if (minValueInput) minValueInput.value = '';
    } else if (filterType === 'minRate') {
        // Clear min rate filter
        activeFilters.minRate = null;
        
        // Reset input
        const minRateInput = document.getElementById('minRateFilter');
        if (minRateInput) minRateInput.value = '';
    }
    
    // Update selected options in district select
    const districtSelect = document.getElementById('globalDistrictFilter');
    if (districtSelect) {
        Array.from(districtSelect.options).forEach(option => {
            option.selected = activeFilters.district.includes(option.value);
        });
    }
    
    // Re-apply filters
    applyGlobalFilter(activeFilters);
}

/**
 * Clear all active filters
 */
function clearAllFilters() {
    // Reset filter inputs
    const districtSelect = document.getElementById('globalDistrictFilter');
    const minValueInput = document.getElementById('minValueFilter');
    const minRateInput = document.getElementById('minRateFilter');
    
    if (districtSelect) {
        Array.from(districtSelect.options).forEach(option => {
            option.selected = false;
        });
    }
    
    if (minValueInput) minValueInput.value = '';
    if (minRateInput) minRateInput.value = '';
    
    // Reset active filters
    activeFilters = {
        district: [],
        minValue: null,
        minRate: null
    };
    
    // Restore original data
    if (originalData.length > 0) {
        window.piltData = [...originalData];
        filteredData = [...originalData];
    }
    
    // Update filter display
    updateActiveFiltersDisplay();
    
    // Update all widgets
    updateAllWidgets();
    
    // Save empty filters
    saveFilters();
    
    console.log('All filters cleared');
}

/**
 * Update all dashboard widgets with filtered data
 */
function updateAllWidgets() {
    console.log('Updating all widgets with filtered data');
    
    // Update summary widget
    updateWidgetSummary(document.querySelector('[data-widget-id="summary"]'));
    
    // Regenerate all charts
    const chartWidgets = document.querySelectorAll('[data-widget-id*="chart"]');
    chartWidgets.forEach(widget => {
        regenerateWidgetChart(widget);
    });
    
    // Update table widget
    regenerateWidgetTable(document.querySelector('[data-widget-id="table"]'));
}

/**
 * Save current filters to localStorage
 */
function saveFilters() {
    try {
        localStorage.setItem('piltDashboardFilters', JSON.stringify(activeFilters));
        console.log('Filters saved:', activeFilters);
    } catch (e) {
        console.error('Error saving filters:', e);
    }
}

/**
 * Restore saved filters from localStorage
 */
function restoreSavedFilters() {
    try {
        const savedFilters = localStorage.getItem('piltDashboardFilters');
        if (savedFilters) {
            const filters = JSON.parse(savedFilters);
            console.log('Restoring saved filters:', filters);
            
            // Update UI with saved filter values
            const districtSelect = document.getElementById('globalDistrictFilter');
            const minValueInput = document.getElementById('minValueFilter');
            const minRateInput = document.getElementById('minRateFilter');
            
            if (districtSelect && filters.district) {
                Array.from(districtSelect.options).forEach(option => {
                    option.selected = filters.district.includes(option.value);
                });
            }
            
            if (minValueInput && filters.minValue !== null) {
                minValueInput.value = filters.minValue;
            }
            
            if (minRateInput && filters.minRate !== null) {
                minRateInput.value = filters.minRate;
            }
            
            // Apply the filters
            applyGlobalFilter(filters);
        }
    } catch (e) {
        console.error('Error restoring filters:', e);
    }
}

/**
 * Save the entire dashboard state including filters and layout
 */
function saveDashboardState() {
    // Save filters
    saveFilters();
    
    // Save layout (already implemented elsewhere)
    if (typeof saveDashboardLayout === 'function') {
        saveDashboardLayout();
    }
    
    console.log('Dashboard state saved');
}

/**
 * Restore the entire dashboard state
 */
function restoreDashboardState() {
    // Restore saved filters
    restoreSavedFilters();
    
    // Restore layout (already implemented elsewhere)
    if (typeof loadDashboardLayout === 'function') {
        loadDashboardLayout();
    }
    
    console.log('Dashboard state restored');
}

/**
 * Get currently active filters
 * @returns {Object} Active filters
 */
function getActiveFilters() {
    return {...activeFilters};
}

// Make sure formatCurrency is available
function formatCurrency(value) {
    if (typeof window.formatCurrency === 'function') {
        return window.formatCurrency(value);
    }
    
    return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Format rate as percentage with 4 decimal places
function formatRate(value) {
    return value.toFixed(4);
}