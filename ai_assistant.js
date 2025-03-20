/**
 * AI Assistant functionality for PILT Dashboard
 * This module provides AI-powered features for data analysis and insights
 */

class AIAssistant {
    constructor(apiKey = null) {
        this.apiKey = apiKey;
        this.messageHistory = [];
        
        // Add initial system message to set context
        this.addMessage('system', 
            'You are an AI assistant for a PILT (Payment in Lieu of Taxes) dashboard. ' +
            'Your role is to help users understand and analyze their PILT data. ' +
            'Respond in a helpful, clear manner with accurate information about PILT calculations, ' +
            'district data, and financial implications. ' +
            'PILT is calculated as (Assessed Value × Levy Rate) - Deduction = PILT Due.'
        );
    }
    
    /**
     * Set the OpenAI API key
     * @param {string} apiKey - The OpenAI API key
     */
    setApiKey(apiKey) {
        this.apiKey = apiKey;
    }
    
    /**
     * Clear the message history
     */
    clearHistory() {
        this.messageHistory = [];
        
        // Re-add the system message
        this.addMessage('system', 
            'You are an AI assistant for a PILT (Payment in Lieu of Taxes) dashboard. ' +
            'Your role is to help users understand and analyze their PILT data. ' +
            'Respond in a helpful, clear manner with accurate information about PILT calculations, ' +
            'district data, and financial implications. ' +
            'PILT is calculated as (Assessed Value × Levy Rate) - Deduction = PILT Due.'
        );
    }
    
    /**
     * Add a message to the history
     * @param {string} role - The role of the message sender ('user', 'assistant', or 'system')
     * @param {string} content - The message content
     */
    addMessage(role, content) {
        this.messageHistory.push({
            role: role,
            content: content
        });
        
        // Limit history to 20 messages for performance
        if (this.messageHistory.length > 20) {
            // Remove the oldest user/assistant message (but keep the system message)
            const systemMessages = this.messageHistory.filter(msg => msg.role === 'system');
            const otherMessages = this.messageHistory.filter(msg => msg.role !== 'system');
            otherMessages.shift(); // Remove oldest non-system message
            this.messageHistory = [...systemMessages, ...otherMessages];
        }
    }
    
    /**
     * Get the current PILT data and format it for analysis
     * @param {Array} piltData - The PILT data to analyze
     * @returns {string} - A text representation of the data
     */
    formatDataForAnalysis(piltData) {
        if (!piltData || piltData.length === 0) {
            return "No PILT data available for analysis.";
        }
        
        let dataText = "PILT DATA ANALYSIS FRAMEWORK\n";
        dataText += "================================\n\n";
        
        // Add data for each district with enhanced structure
        dataText += "DISTRICT-LEVEL METRICS\n";
        dataText += "---------------------\n\n";
        
        let totalAssessedValue = 0;
        let totalBasePILT = 0;
        let totalDeduction = 0;
        let totalPILTDue = 0;
        let avgLevyRate = 0;
        
        // First pass to calculate totals for later use
        piltData.forEach(district => {
            totalAssessedValue += district.assessedValue || 0;
            totalBasePILT += district.basePILT || 0;
            totalDeduction += district.deduction || 0;
            totalPILTDue += district.piltDue || 0;
            avgLevyRate += district.levyRate || 0;
        });
        
        avgLevyRate = avgLevyRate / piltData.length;
        
        // Create sorted copies for analysis
        const sortedByValue = [...piltData].sort((a, b) => (b.assessedValue || 0) - (a.assessedValue || 0));
        const sortedByPILT = [...piltData].sort((a, b) => (b.piltDue || 0) - (a.piltDue || 0));
        const sortedByRate = [...piltData].sort((a, b) => (b.levyRate || 0) - (a.levyRate || 0));
        
        // Second pass to display districts with richer context
        piltData.forEach((district, index) => {
            // Calculate derived metrics
            const effectiveRate = district.piltDue / district.assessedValue;
            const deductionPercent = district.deduction / district.basePILT * 100;
            
            // Determine rankings (position in sorted arrays)
            const valueRank = sortedByValue.findIndex(d => d === district) + 1;
            const piltRank = sortedByPILT.findIndex(d => d === district) + 1;
            const rateRank = sortedByRate.findIndex(d => d === district) + 1;
            
            // Calculate percentages of total
            const pctOfTotalValue = (district.assessedValue / totalAssessedValue * 100);
            const pctOfTotalPILT = (district.piltDue / totalPILTDue * 100);
            
            dataText += `DISTRICT ID: ${district.district || 'Unknown'}\n`;
            dataText += `• Assessed Value: $${(district.assessedValue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})} (${pctOfTotalValue.toFixed(2)}% of total, rank #${valueRank})\n`;
            dataText += `• Levy Rate: ${(district.levyRate || 0).toFixed(6)} (${((district.levyRate / avgLevyRate) * 100 - 100).toFixed(2)}% vs avg, rank #${rateRank})\n`;
            dataText += `• Base PILT: $${(district.basePILT || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
            dataText += `• Deduction: $${(district.deduction || 0).toLocaleString('en-US', {maximumFractionDigits: 2})} (${deductionPercent.toFixed(2)}% of base)\n`;
            dataText += `• PILT Due: $${(district.piltDue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})} (${pctOfTotalPILT.toFixed(2)}% of total, rank #${piltRank})\n`;
            dataText += `• Effective Rate: ${effectiveRate.toFixed(6)}\n`;
            
            // Add separator between districts
            if (index < piltData.length - 1) {
                dataText += "\n";
            }
        });
        
        // Add aggregated summary metrics
        dataText += "\n\nAGGREGATE FINANCIAL METRICS\n";
        dataText += "--------------------------\n";
        dataText += `• Total Districts: ${piltData.length}\n`;
        dataText += `• Total Assessed Value: $${totalAssessedValue.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Total Base PILT: $${totalBasePILT.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Total Deductions: $${totalDeduction.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Total PILT Due: $${totalPILTDue.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Effective Deduction Rate: ${(totalDeduction / totalBasePILT * 100).toFixed(2)}%\n`;
        dataText += `• Average Levy Rate: ${avgLevyRate.toFixed(6)}\n`;
        dataText += `• PILT Capture Rate: ${(totalPILTDue / totalAssessedValue * 100).toFixed(4)}%\n`;
        
        // Add top district analysis
        dataText += "\n\nTOP DISTRICT RANKINGS\n";
        dataText += "--------------------\n";
        
        // Top by assessed value
        dataText += "Highest Assessed Value Districts:\n";
        for (let i = 0; i < Math.min(3, sortedByValue.length); i++) {
            const district = sortedByValue[i];
            const percentOfTotal = (district.assessedValue / totalAssessedValue * 100).toFixed(2);
            dataText += `${i+1}. ${district.district}: $${district.assessedValue.toLocaleString('en-US', {maximumFractionDigits: 2})} (${percentOfTotal}% of total)\n`;
        }
        
        // Top by PILT due
        dataText += "\nHighest PILT Due Districts:\n";
        for (let i = 0; i < Math.min(3, sortedByPILT.length); i++) {
            const district = sortedByPILT[i];
            const percentOfTotal = (district.piltDue / totalPILTDue * 100).toFixed(2);
            dataText += `${i+1}. ${district.district}: $${district.piltDue.toLocaleString('en-US', {maximumFractionDigits: 2})} (${percentOfTotal}% of total)\n`;
        }
        
        // Top by levy rate
        dataText += "\nHighest Levy Rate Districts:\n";
        for (let i = 0; i < Math.min(3, sortedByRate.length); i++) {
            const district = sortedByRate[i];
            const percentAboveAvg = ((district.levyRate / avgLevyRate - 1) * 100).toFixed(2);
            dataText += `${i+1}. ${district.district}: ${district.levyRate.toFixed(6)} (${percentAboveAvg}% above average)\n`;
        }
        
        // Calculate quartiles for distribution analysis
        function calculateQuartiles(values) {
            const sorted = [...values].sort((a, b) => a - b);
            const len = sorted.length;
            
            if (len === 0) return { min: 0, q1: 0, median: 0, q3: 0, max: 0 };
            
            // Calculate quartile indices
            const q1Index = Math.floor(len * 0.25);
            const medianIndex = Math.floor(len * 0.5);
            const q3Index = Math.floor(len * 0.75);
            
            return {
                min: sorted[0] || 0,
                q1: sorted[q1Index] || 0,
                median: sorted[medianIndex] || 0,
                q3: sorted[q3Index] || 0,
                max: sorted[len - 1] || 0
            };
        }
        
        // Distribution analysis
        const assessedValueQuartiles = calculateQuartiles(piltData.map(d => d.assessedValue || 0));
        const piltDueQuartiles = calculateQuartiles(piltData.map(d => d.piltDue || 0));
        
        dataText += "\n\nDISTRIBUTION ANALYSIS\n";
        dataText += "--------------------\n";
        dataText += "Assessed Value Distribution:\n";
        dataText += `• Minimum: $${assessedValueQuartiles.min.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• 25th Percentile: $${assessedValueQuartiles.q1.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Median: $${assessedValueQuartiles.median.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• 75th Percentile: $${assessedValueQuartiles.q3.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Maximum: $${assessedValueQuartiles.max.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        
        dataText += "\nPILT Due Distribution:\n";
        dataText += `• Minimum: $${piltDueQuartiles.min.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• 25th Percentile: $${piltDueQuartiles.q1.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Median: $${piltDueQuartiles.median.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• 75th Percentile: $${piltDueQuartiles.q3.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        dataText += `• Maximum: $${piltDueQuartiles.max.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
        
        return dataText;
    }
    
    /**
     * Get insights about the current PILT data
     * @param {Array} piltData - The PILT data to analyze
     * @returns {Promise<string>} - The insights text
     */
    async getDataInsights(piltData) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Format data for analysis
        const dataText = this.formatDataForAnalysis(piltData);
        
        // Create prompt with advanced data analysis directives
        const prompt = `
Analyze the following PILT (Payment in Lieu of Taxes) data with exceptional depth and precision:

${dataText}

Generate a comprehensive analysis that delivers transformative insights:

1. DISTRICT PERFORMANCE ANALYSIS
   - Identify top and bottom performing districts with exact figures and percentages
   - Calculate precise variance from district averages
   - Highlight specific outliers that require immediate attention

2. LEVY RATE OPTIMIZATION
   - Perform statistical analysis of current levy rate distribution
   - Identify potential rate adjustments to maximize revenue without creating disproportionate burden
   - Calculate the exact revenue impact of standardizing rates across similar districts

3. DEDUCTION EFFICIENCY ASSESSMENT
   - Quantify the exact impact of deductions on final PILT amounts
   - Identify districts where deduction ratios are non-standard
   - Calculate potential revenue adjustments from optimizing deduction policies

4. PATTERN RECOGNITION
   - Identify hidden correlations between district characteristics and PILT metrics
   - Detect any anomalies that suggest data inconsistencies or policy exceptions
   - Flag potential opportunities for strategic adjustments

5. REVENUE DISTRIBUTION MAPPING
   - Calculate precise distribution of tax burden across district types
   - Identify any imbalances in contribution versus benefit ratios
   - Suggest specific redistributions to achieve optimal revenue balance

Format your response with crystal-clear section headers, precise figures, and actionable strategic recommendations. Your insights should deliver immediate value for financial decision-makers.
`;
        
        this.addMessage('user', prompt);
        
        // Call API with enhanced parameters
        const response = await this.callOpenAI(this.messageHistory, {
            temperature: 0.5,  // More consistent, precise outputs
            max_tokens: 1200   // Allow for more detailed analysis
        });
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Get recommendations for what-if scenarios
     * @param {Array} piltData - The current PILT data
     * @returns {Promise<string>} - The recommendations text
     */
    async getWhatIfRecommendations(piltData) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Format data for analysis
        const dataText = this.formatDataForAnalysis(piltData);
        
        // Create advanced strategic prompt
        const prompt = `
Perform an advanced strategic analysis of the following PILT (Payment in Lieu of Taxes) data and develop high-impact "what-if" scenarios that could transform revenue optimization:

${dataText}

Create 5 precision-engineered scenario models with exact parameters:

SCENARIO 1: LEVY RATE OPTIMIZATION MODEL
- Specify exact percentage adjustments for each district category 
- Calculate precise revenue impact figures with confidence intervals
- Provide implementation timeline with specific milestones
- Include risk assessment with mitigation strategies

SCENARIO 2: STRATEGIC DEDUCTION RECALIBRATION
- Identify specific deduction thresholds to optimize revenue
- Quantify exact financial impact by district type
- Outline legal/policy considerations with actionable steps
- Provide phased implementation approach with specific targets

SCENARIO 3: DISTRICT CONSOLIDATION ANALYSIS
- Identify optimal district groupings based on statistical similarities
- Calculate administrative efficiency gains with exact figures
- Project precise revenue changes under consolidated approach
- Outline governance implications with specific recommendations

SCENARIO 4: PROGRESSIVE RATE STRUCTURE MODEL
- Design tiered levy rate structure with specific thresholds and rates
- Calculate redistribution impact with precise equity metrics
- Quantify exact revenue changes by district category
- Include transitional implementation framework with timeline

SCENARIO 5: FUTURE-FOCUSED GROWTH PROJECTION
- Model specific growth rates for assessed values by district type
- Project PILT revenue changes over 5-year horizon with confidence intervals
- Identify key trigger points requiring policy adjustments
- Outline monitoring framework with specific metrics and thresholds

For each scenario, provide exact parameter values, calculations, expected outcomes, implementation considerations, and strategic rationale. Your analysis should be data-driven, immediately actionable, and transformative for financial planning.
`;
        
        this.addMessage('user', prompt);
        
        // Call API with enhanced parameters
        const response = await this.callOpenAI(this.messageHistory, {
            temperature: 0.4,  // Higher precision for financial projections
            max_tokens: 1500   // Allow for comprehensive scenario details
        });
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Explain a PILT calculation in simple terms
     * @param {Object} district - The district data
     * @returns {Promise<string>} - The explanation text
     */
    async explainCalculation(district) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        if (!district) {
            throw new Error("No district data provided.");
        }
        
        // Create enhanced interactive learning prompt
        const prompt = `
Create a crystal-clear, accessible explanation of the PILT calculation for the following district:

District: ${district.district}
Assessed Value: $${(district.assessedValue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
Levy Rate: ${(district.levyRate || 0).toFixed(6)}
Base PILT: $${(district.basePILT || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
Deduction: $${(district.deduction || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}
PILT Due: $${(district.piltDue || 0).toLocaleString('en-US', {maximumFractionDigits: 2})}

Your explanation should be both intuitive for newcomers and valuable for professionals:

1. START WITH A CLEAR DEFINITION
   - Explain what PILT is in plain language
   - Why this payment exists and who it benefits
   - Real-world context for its importance

2. VISUAL CALCULATION BREAKDOWN
   - Show each step as a simple formula with the actual numbers
   - Use visual formatting (e.g., Step 1: ✓) to make steps easy to follow
   - Highlight each component's purpose in the overall calculation

3. CONTEXTUAL INSIGHTS
   - Compare this district's figures to typical values
   - Explain what makes this district's calculation unique
   - Provide perspective on whether the final amount is typical/atypical

4. PRACTICAL IMPLICATIONS
   - Explain what this PILT payment means for the district
   - How changes to each parameter would affect the outcome
   - What stakeholders should understand about this payment

Format your response with clear sections, helpful visual structure, and language that balances simplicity with precision. Use bullet points, spacing, and formatting to enhance clarity.
`;
        
        this.addMessage('user', prompt);
        
        // Call API with enhanced parameters
        const response = await this.callOpenAI(this.messageHistory, {
            temperature: 0.5,  // Balance creativity with precision
            max_tokens: 1200   // Allow for comprehensive, well-formatted explanation
        });
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Chat with the AI about PILT data
     * @param {string} userMessage - The user's message
     * @param {Array} piltData - The current PILT data (optional)
     * @returns {Promise<string>} - The AI's response
     */
    async chat(userMessage, piltData = null) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // If this is the first few messages, set advanced system instructions
        if (this.messageHistory.length <= 3 || this.messageHistory.every(msg => msg.role !== 'system')) {
            // Remove any existing system messages
            this.messageHistory = this.messageHistory.filter(msg => msg.role !== 'system');
            
            // Add enhanced system message with PILT expertise
            this.addMessage('system', `You are an expert PILT financial analyst and advisor with decades of experience in municipal finance.
Your responses should demonstrate exceptional expertise, insight, and strategic thinking about PILT data.

Communication Guidelines:
- Be concise yet comprehensive - every word should deliver value
- Use precise, quantified statements rather than generalizations
- Structure complex answers with clear formatting (headers, bullet points)
- Tailor explanations to both strategic and operational perspectives
- Connect insights to actionable recommendations
- Use financial and policy terminology accurately and appropriately

When analyzing PILT data, always consider:
- Revenue optimization opportunities without compromising equity
- District-specific context and unique circumstances
- Historical trends and future projections
- Regulatory and policy implications
- Strategic financial impact on municipal operations

Respond with confidence, authority, and a focus on delivering transformative insights.`);
            
            // If we have PILT data, add it as enhanced context
            if (piltData && piltData.length > 0) {
                const dataText = this.formatDataForAnalysis(piltData);
                this.addMessage('system', `Current PILT data for your analysis:\n${dataText}

Please use this exact data when providing calculations or specific figures in your responses.
When making comparisons, ensure you're using the precise values from this dataset.`);
            }
        }
        
        // Add user message
        this.addMessage('user', userMessage);
        
        // Call API with enhanced conversation parameters
        const response = await this.callOpenAI(this.messageHistory, {
            temperature: 0.6,     // Balance precision with conversational tone
            max_tokens: 1200,     // Allow for detailed responses
            presence_penalty: 0.2, // Encourage addressing new aspects of questions
            frequency_penalty: 0.2 // Discourage repetitive phrasing
        });
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Generate a summary report of the PILT data
     * @param {Array} piltData - The PILT data to summarize
     * @returns {Promise<string>} - The summary report text
     */
    async generateSummaryReport(piltData) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Format data for analysis
        const dataText = this.formatDataForAnalysis(piltData);
        
        // Create enhanced executive report prompt
        const prompt = `
Create an executive-grade analytical report based on the following PILT (Payment in Lieu of Taxes) data:

${dataText}

Develop a premium-quality report with these precise components:

SECTION 1: EXECUTIVE DASHBOARD
- Produce exact KPIs with YTD performance metrics
- Generate concise highlights using quantified metrics
- Include critical alerts for immediate attention
- Provide strategic snapshot with actionable intelligence

SECTION 2: DISTRICT PERFORMANCE MATRIX
- Conduct quantitative assessment of each district's contribution with precise metrics
- Identify specific performance trends with statistical validation
- Flag outliers with exact variance percentages
- Rank districts by multiple performance indicators with weighted scoring

SECTION 3: FINANCIAL IMPACT ANALYSIS
- Calculate exact revenue implications with confidence intervals
- Model precise cash flow impact on county operations
- Quantify benefit distribution with demographic overlays
- Forecast detailed revenue stability with multi-factor analysis

SECTION 4: EQUITY & DISTRIBUTION ASSESSMENT
- Map precise tax burden distribution using multiple equity metrics
- Identify specific districts with non-standard contribution ratios
- Calculate exact fairness indices across district types
- Provide statistical analysis of burden-to-benefit ratios

SECTION 5: COMPARATIVE BENCHMARKING
- Generate detailed trend analysis with multi-year projections
- Compare performance against similar county benchmarks (simulated if needed)
- Identify specific divergence from optimal performance models
- Calculate precise performance gaps with targeted closure strategies

SECTION 6: STRATEGIC RECOMMENDATIONS
- Provide actionable, high-impact recommendations with implementation timelines
- Quantify expected outcomes for each recommendation
- Identify specific policy adjustments with projected revenue impacts
- Outline multi-phase optimization strategy with measurable milestones

Format this report with professional-grade formatting, precise data visualizations, and executive-focused insights. This should be a decision-ready document that balances analytical depth with strategic clarity.
`;
        
        this.addMessage('user', prompt);
        
        // Call API with enhanced parameters for executive report
        const response = await this.callOpenAI(this.messageHistory, {
            temperature: 0.4,     // Higher precision for formal reports
            max_tokens: 2000,     // Allow for comprehensive detailed report
            presence_penalty: 0.1, // Slight enhancement of diverse content
            frequency_penalty: 0.1 // Slight enhancement of vocabulary diversity
        });
        
        // Store response
        this.addMessage('assistant', response);
        
        return response;
    }
    
    /**
     * Call the OpenAI API
     * @param {Array} messages - The messages to send
     * @param {Object} options - Additional options for the API call
     * @returns {Promise<string>} - The text response
     */
    async callOpenAI(messages, options = {}) {
        if (!this.apiKey) {
            throw new Error("API key not set. Please configure your OpenAI API key in Settings.");
        }
        
        // Default parameters that can be overridden by options
        const params = {
            model: options.model || 'gpt-3.5-turbo',
            messages: messages,
            temperature: options.temperature !== undefined ? options.temperature : 0.7,
            max_tokens: options.max_tokens || 1000,
            top_p: options.top_p || 1,
            presence_penalty: options.presence_penalty || 0,
            frequency_penalty: options.frequency_penalty || 0
        };
        
        try {
            const response = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(params)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${errorData.error?.message || response.statusText}`);
            }
            
            const data = await response.json();
            return data.choices[0].message.content;
        } catch (error) {
            console.error('Error calling OpenAI API:', error);
            throw new Error(`Failed to get AI response: ${error.message}`);
        }
    }
}

// Initialize AI Assistant as a global object
window.aiAssistant = new AIAssistant();

// Try to load API key from localStorage
document.addEventListener('DOMContentLoaded', function() {
    const apiKey = localStorage.getItem('openai_api_key');
    if (apiKey) {
        window.aiAssistant.setApiKey(apiKey);
    }
});